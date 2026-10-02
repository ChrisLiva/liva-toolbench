#!/usr/bin/env python3
"""Show and edit the effort settings in your Claude Code user settings file.

Run it from the project you want to inspect, so the precedence view includes
that project's .claude/settings.json and .claude/settings.local.json:

    python3 tools/claude-effort/claude_effort.py

It writes only model, effortLevel, maxEffortLevel, ultracode,
env.CLAUDE_CODE_EFFORT_LEVEL, and modelSettings in $CLAUDE_CONFIG_DIR/settings.json,
or ~/.claude/settings.json when that variable is unset. Every other key keeps its
value, and each save copies the previous file to settings.json.bak.

Keys: up/down select a row, left/right change it, 1-5 pick low..max, 0 unsets,
c cycles a model's cap, d makes the selected model the default, Tab switches
between the scenarios and precedence views, w saves, r reloads from disk, q quits.
"""

from __future__ import annotations

import argparse
import copy
import curses
import glob
import json
import locale
import os
import re
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass

ENV_KEY = "CLAUDE_CODE_EFFORT_LEVEL"
LEVELS = ("low", "medium", "high", "xhigh")
FIVE = ("low", "medium", "high", "xhigh", "max")
FOUR = ("low", "medium", "high", "max")
RANK = {level: i for i, level in enumerate(FIVE)}

# Label, supported levels, and built-in default per model, from
# code.claude.com/docs/en/model-config#adjust-effort-level for Claude Code 2.1.287.
MODELS = {
    "claude-opus-5-5": ("Opus 5.5", FIVE, "medium"),
    "claude-sonnet-5-5": ("Sonnet 5.5", FIVE, "medium"),
    "claude-fable-5-1": ("Fable 5.1", FIVE, "high"),
    "claude-opus-5": ("Opus 5", FIVE, "high"),
    "claude-sonnet-5": ("Sonnet 5", FIVE, "high"),
    "claude-fable-5": ("Fable 5", FIVE, "high"),
    "claude-opus-4-8": ("Opus 4.8", FIVE, "high"),
    "claude-opus-4-7": ("Opus 4.7", FIVE, "xhigh"),
    "claude-opus-4-6": ("Opus 4.6", FOUR, "high"),
    "claude-sonnet-4-6": ("Sonnet 4.6", FOUR, "high"),
}
# The docs say Opus 5.5 ignores a top-level effortLevel in the user file; a
# headless 2.1.287 run showed Sonnet 5.5 ignores it too.
SKIPS_USER_EFFORT_LEVEL = {"claude-opus-5-5", "claude-sonnet-5-5"}
# How the Anthropic API resolves each alias.
ALIASES = {
    "opus": "claude-opus-5-5",
    "sonnet": "claude-sonnet-5-5",
    "fable": "claude-fable-5-1",
    "best": "claude-fable-5-1",
    "haiku": "claude-haiku-4-5",
}
MANAGED_DIR = (
    "/Library/Application Support/ClaudeCode"
    if sys.platform == "darwin"
    else "/etc/claude-code"
)
EDITABLE_PATHS = (
    ("model",),
    ("effortLevel",),
    ("maxEffortLevel",),
    ("ultracode",),
    ("env", ENV_KEY),
)
MODEL_FIELDS = ("effortLevel", "maxEffortLevel")


def canonical(model):
    """Map an alias, [1m] variant, or date-suffixed ID to its modelSettings name."""
    if not isinstance(model, str) or not model.strip():
        return None
    name = model.strip().lower().removesuffix("[1m]")
    return re.sub(r"-\d{8}$", "", ALIASES.get(name, name))


def read_json(path):
    """Return (data, error). A missing file returns (None, None)."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None, None
    except (OSError, ValueError) as exc:
        return None, str(exc)
    if not isinstance(data, dict):
        return None, "the top level is not a JSON object"
    return data, None


def write_json(path, data):
    """Replace path atomically, keeping its mode and a .bak copy of the old file."""
    path = os.path.realpath(path)
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    exists = os.path.exists(path)
    if exists:
        shutil.copy2(path, path + ".bak")
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".settings.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        if exists:
            os.chmod(tmp, stat.S_IMODE(os.stat(path).st_mode))
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise


def get_path(data, path):
    for key in path[:-1]:
        data = data.get(key) if isinstance(data, dict) else None
    return data.get(path[-1]) if isinstance(data, dict) else None


def set_path(data, path, value):
    """Set a nested key; None deletes it and prunes the objects it leaves empty."""
    if value is not None:
        for key in path[:-1]:
            if not isinstance(data.get(key), dict):
                data[key] = {}
            data = data[key]
        data[path[-1]] = value
        return
    chain = [data]
    for key in path[:-1]:
        child = chain[-1].get(key)
        if not isinstance(child, dict):
            return
        chain.append(child)
    chain[-1].pop(path[-1], None)
    for parent, key, child in reversed(list(zip(chain, path, chain[1:]))):
        if child:
            break
        del parent[key]


@dataclass
class Layer:
    name: str
    path: str
    data: dict | None
    error: str | None = None

    @property
    def settings(self):
        return self.data or {}


def load_managed(directory):
    path = os.path.join(directory, "managed-settings.json")
    data, error = read_json(path)
    for extra in sorted(
        glob.glob(os.path.join(directory, "managed-settings.d", "*.json"))
    ):
        more, more_error = read_json(extra)
        data = {**(data or {}), **more} if more else data
        error = error or more_error
    return Layer("managed", path, data, error)


def model_entry(settings, model):
    entries = settings.get("modelSettings")
    for key, value in (entries if isinstance(entries, dict) else {}).items():
        if canonical(key) == model and isinstance(value, dict):
            return value
    return {}


def top_level_applies(layer, model):
    return not (layer.name == "user" and model in SKIPS_USER_EFFORT_LEVEL)


def env_override(layers, environ):
    """A settings env block beats the shell, as a headless 2.1.287 run showed."""
    for layer in layers:
        env = layer.settings.get("env")
        if isinstance(env, dict) and env.get(ENV_KEY):
            return env[ENV_KEY], f"{layer.name} settings env"
    if environ.get(ENV_KEY):
        return environ[ENV_KEY], "shell"
    return None, None


def effort_cap(model, layers):
    """The lowest cap any layer sets; a model's own entry replaces its layer's top-level cap."""
    cap, source = None, None
    for layer in layers:
        value = model_entry(layer.settings, model).get(
            "maxEffortLevel"
        ) or layer.settings.get("maxEffortLevel")
        if (
            value in RANK
            and value != "max"
            and (cap is None or RANK[value] < RANK[cap])
        ):
            cap, source = value, layer.name
    return cap, source


@dataclass
class Resolution:
    level: str | None
    requested: str | None
    source: str
    winner: tuple
    cap: str | None
    cap_source: str | None
    capped: bool


def resolve(model, layers, environ, explicit=None):
    """Resolve the level a session or subagent on `model` runs at.

    `explicit` is a level from --effort, /effort in the current session, a parent
    session that used either, or an agent's or skill's effort field. Without one,
    the level comes from settings, as for a new session or for a subagent whose
    parent's level was saved. `layers` runs from highest precedence to lowest:
    managed, local, project, user.
    """
    _, supported, default = MODELS.get(model, (model, FIVE, None))
    value, where = env_override(layers, environ)
    requested, source, winner = default, "model default", ("default",)
    if value and value != "auto":
        requested, source, winner = value, f"{ENV_KEY} in {where}", ("env",)
    elif value == "auto":
        source = f"{ENV_KEY}=auto, model default"
    elif explicit:
        requested, source, winner = explicit, "explicit level", ("explicit",)
    else:
        for layer in layers:
            per_model = model_entry(layer.settings, model).get("effortLevel")
            top = (
                layer.settings.get("effortLevel")
                if top_level_applies(layer, model)
                else None
            )
            per_model, top = (v if v in LEVELS else None for v in (per_model, top))
            if per_model or top:
                key = "modelSettings" if per_model else "effortLevel"
                requested, source, winner = (
                    per_model or top,
                    f"{layer.name} {key}",
                    ("layer", layer.name, key),
                )
                break
    cap, cap_source = effort_cap(model, layers)
    level, capped = None, False
    if requested in RANK:
        capped = cap is not None and RANK[requested] > RANK[cap]
        ceiling = RANK[cap] if cap and capped else RANK[requested]
        level = max(
            (v for v in supported if RANK[v] <= ceiling),
            key=lambda v: RANK[v],
            default=None,
        )
    return Resolution(level, requested, source, winner, cap, cap_source, capped)


def read_agent(path):
    """Return the frontmatter fields of an agent definition, or None."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    match = re.match(r"---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not line[:1].isspace():
            fields[key.strip()] = value.strip().strip("\"'")
    fields.setdefault("name", os.path.splitext(os.path.basename(path))[0])
    return fields


def read_agents(scopes):
    """Map agent name to (scope, path, fields); earlier scopes win, as in Claude Code."""
    agents = {}
    for scope, directory in scopes:
        for path in sorted(
            glob.glob(os.path.join(directory, "**", "*.md"), recursive=True)
        ):
            fields = read_agent(path)
            if fields and fields["name"] not in agents:
                agents[fields["name"]] = (scope, path, fields)
    return agents


class Editor:
    def __init__(self, config_dir, project_dir, managed_dir, environ):
        self.config_dir = config_dir
        self.project_dir = project_dir
        self.managed_dir = managed_dir
        self.environ = environ
        self.user_path = os.path.join(config_dir, "settings.json")
        self.reload()

    def reload(self):
        data, self.error = read_json(self.user_path)
        self.user_exists = os.path.exists(self.user_path)
        self.loaded = data or {}
        self.work = copy.deepcopy(self.loaded)
        claude_dir = os.path.join(self.project_dir, ".claude")
        self.others = [load_managed(self.managed_dir)]
        for name, filename in (
            ("local", "settings.local.json"),
            ("project", "settings.json"),
        ):
            path = os.path.join(claude_dir, filename)
            self.others.append(Layer(name, path, *read_json(path)))
        self.agents = read_agents(
            [
                ("project", os.path.join(claude_dir, "agents")),
                ("user", os.path.join(self.config_dir, "agents")),
            ]
        )

    def layers(self):
        return [
            *self.others,
            Layer(
                "user",
                self.user_path,
                self.work if self.user_exists or self.work else None,
                self.error,
            ),
        ]

    @property
    def dirty(self):
        return self.work != self.loaded

    def get(self, path):
        return get_path(self.work, path)

    def set(self, path, value):
        set_path(self.work, path, value)

    def models(self):
        names = list(MODELS)
        entries = self.work.get("modelSettings")
        for key in entries if isinstance(entries, dict) else {}:
            name = canonical(key)
            if name and name not in names:
                names.append(name)
        return names

    def model_path(self, model, field):
        entries = self.work.get("modelSettings")
        key = next(
            (
                k
                for k in (entries if isinstance(entries, dict) else {})
                if canonical(k) == model
            ),
            model,
        )
        return ("modelSettings", key, field)

    def default_model(self):
        if self.environ.get("ANTHROPIC_MODEL"):
            return canonical(self.environ["ANTHROPIC_MODEL"]), "ANTHROPIC_MODEL"
        for layer in self.layers():
            if layer.settings.get("model"):
                return canonical(layer.settings["model"]), f"{layer.name} settings"
        return None, "account default"

    def changed_paths(self):
        paths = list(EDITABLE_PATHS)
        for data in (self.loaded, self.work):
            entries = data.get("modelSettings")
            for key in entries if isinstance(entries, dict) else {}:
                paths += [
                    ("modelSettings", key, f)
                    for f in MODEL_FIELDS
                    if ("modelSettings", key, f) not in paths
                ]
        return [p for p in paths if get_path(self.work, p) != get_path(self.loaded, p)]

    def save(self):
        """Apply this session's edits onto the file as it is on disk now."""
        if self.error:
            return f"Not saved: settings.json is not valid JSON ({self.error}). Fix it by hand first."
        changed = self.changed_paths()
        if not changed:
            return "Nothing to save."
        fresh, error = read_json(self.user_path)
        if error:
            return f"Not saved: settings.json became unreadable ({error})."
        fresh = fresh or {}
        stale = [p for p in changed if get_path(fresh, p) != get_path(self.loaded, p)]
        if stale:
            return f"Not saved: {'.'.join(stale[0])} changed on disk since loading. Press r to reload."
        for p in changed:
            set_path(fresh, p, get_path(self.work, p))
        write_json(self.user_path, fresh)
        self.loaded, self.work, self.user_exists = fresh, copy.deepcopy(fresh), True
        return (
            f"Saved {len(changed)} change(s). The previous file is settings.json.bak."
        )


@dataclass
class Row:
    label: str
    path: tuple
    choices: tuple
    note: str = ""
    model: str | None = None


def build_rows(ed):
    model_choices = (None, "opus", "sonnet", "fable", "haiku")
    if ed.get(("model",)) not in model_choices:
        model_choices += (ed.get(("model",)),)
    rows = [
        Row("model", ("model",), model_choices, "the model new sessions start on"),
        Row(
            "effortLevel",
            ("effortLevel",),
            (None, *LEVELS),
            "fallback for models older than Opus 5.5 without a saved level",
        ),
        Row(
            "maxEffortLevel",
            ("maxEffortLevel",),
            (None, *FIVE),
            "caps every model; max sets no cap",
        ),
        Row(
            "ultracode",
            ("ultracode",),
            (None, True, False),
            "starts sessions with ultracode; level unchanged",
        ),
        Row(
            f"env {ENV_KEY}",
            ("env", ENV_KEY),
            (None, *FIVE, "auto"),
            "beats every source, agent files too",
        ),
    ]
    for model in ed.models():
        label, supported, _ = MODELS.get(model, (model, FIVE, None))
        choices = (None, *(v for v in supported if v in LEVELS))
        rows.append(
            Row(label, ed.model_path(model, "effortLevel"), choices, model=model)
        )
    return rows


def show(value):
    return "unset" if value is None else str(value).lower()


def short_path(path, project_dir=None):
    home = os.path.expanduser("~")
    if project_dir and path.startswith(project_dir + os.sep):
        return os.path.relpath(path, project_dir)
    return "~" + path[len(home) :] if path.startswith(home + os.sep) else path


VIEWS = ("scenarios", "precedence")


def build_lines(ed, rows, cursor, view=VIEWS[0]):
    """Return (lines, cursor_line); a line is a list of (text, style) segments."""
    lines, cursor_line = [], 0
    layers = ed.layers()
    default, default_source = ed.default_model()
    title = [("Claude effort settings", "title")]
    if ed.dirty:
        title.append(("  unsaved changes", "warn"))
    lines.append(title + [("  " + short_path(ed.user_path), "dim")])
    lines.append([("Project ", "dim"), (short_path(ed.project_dir), "")])
    if ed.error:
        lines.append(
            [
                (
                    f"settings.json is not valid JSON, so editing is off: {ed.error}",
                    "warn",
                )
            ]
        )
    lines.append([])
    lines.append([(f"{'User settings':<34}{'value':<10}what it does", "head")])
    for i, row in enumerate(rows):
        if row.model and not rows[i - 1].model:
            lines.append([])
            lines.append(
                [
                    (
                        f"{'modelSettings':<34}{'saved':<10}{'cap':<9}{'runs at':<10}decided by",
                        "head",
                    )
                ]
            )
        if i == cursor:
            cursor_line = len(lines)
        marker = "> " if i == cursor else "  "
        value = ed.get(row.path)
        if not row.model:
            lines.append(
                [
                    (marker + f"{row.label:<32}", ""),
                    (f"{show(value):<10}", "dim" if value is None else "key"),
                    (row.note, "dim"),
                ]
            )
            continue
        res = resolve(row.model, layers, ed.environ)
        cap = ed.get(ed.model_path(row.model, "maxEffortLevel"))
        star = " *" if row.model == default else ""
        decided = res.source
        if res.level and res.level != res.requested:
            decided += (
                f", capped by {res.cap_source}"
                if res.capped
                else f", {res.requested} unsupported"
            )
        lines.append(
            [
                (marker + f"{row.label + star:<32}", ""),
                (f"{show(value):<10}", "dim" if value is None else "key"),
                (f"{show(cap):<9}", "dim" if cap is None else "key"),
                (f"{res.level or 'n/a':<10}", "win"),
                (decided, "dim"),
            ]
        )
    lines.append([("  * the default model, from " + default_source, "dim")])
    lines.append([])
    subject = rows[cursor].model or (
        default if default in MODELS else "claude-opus-5-5"
    )
    tabs = [("    Tab: ", "dim")] + [
        (f"[{v}] " if v == view else f"{v} ", "head" if v == view else "dim")
        for v in VIEWS
    ]
    detail = scenario_lines if view == "scenarios" else precedence_lines
    lines += detail(ed, layers, subject, tabs)
    return lines, cursor_line


def scenario_lines(ed, layers, model, tabs):
    label = MODELS.get(model, (model,))[0]
    saved = resolve(model, layers, ed.environ)
    out = [[(f"How a session or subagent on {label} gets its level", "head")] + tabs]

    def row(text, level, why):
        out.append(
            [(f"  {text:<52}", ""), (f"{level or 'n/a':<8}", "win"), (why, "dim")]
        )

    row("New session, no --effort flag", saved.level, saved.source)
    row(
        "Subagent, no effort field, parent's level was saved",
        saved.level,
        "the parent's level isn't passed on",
    )
    out.append([])
    out.append(
        [
            (
                "  An explicit level beats saved levels. It comes from --effort or /effort in the current session,",
                "",
            )
        ]
    )
    out.append(
        [
            (
                "  which subagents on any model inherit, or from an agent's or skill's effort field.",
                "",
            )
        ]
    )
    out.append([(f"  {'    asked for':<52}", "dim")] + [(f"{v:<8}", "") for v in FIVE])
    out.append(
        [(f"  {'    runs at':<52}", "dim")]
        + [
            (f"{resolve(model, layers, ed.environ, v).level or 'n/a':<8}", "win")
            for v in FIVE
        ]
    )
    out.append([])
    env_value, env_where = env_override(layers, ed.environ)
    if env_value:
        out.append(
            [
                (
                    f"  {ENV_KEY}={env_value} from {env_where} replaces every level above, agent files too.",
                    "warn",
                )
            ]
        )
    else:
        out.append(
            [
                (
                    f"  {ENV_KEY} is unset. Once set, it replaces every level above, agent files too.",
                    "dim",
                )
            ]
        )
    out.append([])
    out.append([(f"Agent files that can run on {label}", "head")])
    agents = [
        (name, scope, path, fields)
        for name, (scope, path, fields) in sorted(ed.agents.items())
        if canonical(fields.get("model")) in (model, None, "inherit")
    ]
    for name, scope, path, fields in agents:
        effort = fields.get("effort")
        why = f"effort {effort}" if effort else "no effort field, see above"
        if canonical(fields.get("model")) in (None, "inherit"):
            why += ", model inherit"
        level = resolve(model, layers, ed.environ, effort).level
        source = f"{scope} {os.path.basename(path)}"
        out.append(
            [
                (f"  {name:<24}{source:<28}", ""),
                (f"{level or 'n/a':<8}", "win"),
                (why, "dim"),
            ]
        )
    if not agents:
        out.append([("  none in ~/.claude/agents or .claude/agents", "dim")])
    return out


def precedence_lines(ed, layers, model, tabs):
    label, _, default = MODELS.get(model, (model, FIVE, None))
    res = resolve(model, layers, ed.environ)
    decides = ("  < decides", "win")
    out = [
        [
            (
                f"Why a new session on {label} runs at {res.level or 'n/a'}, highest precedence first",
                "head",
            )
        ]
        + tabs
    ]

    def row(number, name, parts):
        out.append([(f"  {number:<3}{name:<34}", "")] + parts)

    def mark(winner):
        return [decides] if res.winner == winner else []

    env_value, env_where = env_override(layers, ed.environ)
    if env_value:
        row("1", ENV_KEY, [(f"{env_value} from {env_where}", "key")] + mark(("env",)))
    else:
        row("1", ENV_KEY, [("unset in your shell and every settings env", "dim")])
    row(
        "2",
        "--effort flag, /effort",
        [("explicit levels; the scenarios view shows what they map to", "dim")],
    )
    for i, layer in enumerate(layers):
        name = f"{layer.name} {short_path(layer.path, ed.project_dir)}"
        name = name if len(name) < 34 else layer.name
        settings, parts = layer.settings, []
        if layer.error:
            parts.append([(f"unreadable: {layer.error}", "warn")])
        elif layer.data is None:
            parts.append([("no file", "dim")])
        per_model = model_entry(settings, model).get("effortLevel")
        top = settings.get("effortLevel")
        cap = model_entry(settings, model).get("maxEffortLevel") or settings.get(
            "maxEffortLevel"
        )
        if per_model:
            parts.append(
                [(f"modelSettings {per_model}", "key")]
                + mark(("layer", layer.name, "modelSettings"))
            )
        if top and top_level_applies(layer, model):
            parts.append(
                [(f"effortLevel {top}", "key")]
                + mark(("layer", layer.name, "effortLevel"))
            )
        elif top:
            parts.append(
                [
                    (
                        f"effortLevel {top}, ignored: Opus 5.5 and Sonnet 5.5 skip it in user settings",
                        "dim",
                    )
                ]
            )
        if cap:
            parts.append([(f"maxEffortLevel {cap}", "key")])
        for j, part in enumerate(parts or [[("no effort keys", "dim")]]):
            row("3" if i == 0 and j == 0 else "", name if j == 0 else "", part)
    row("4", "model default", [(show(default), "key")] + mark(("default",)))
    row(
        "",
        "cap",
        [(f"{res.cap} from {res.cap_source}", "key") if res.cap else ("none", "dim")],
    )
    return out


FOOTER = "up/down move  left/right change  1-5 low..max  0 unset  c cap  d default  tab view  w save  r reload  q quit"


def init_styles():
    styles = {
        "": 0,
        "title": curses.A_BOLD,
        "head": curses.A_BOLD,
        "dim": curses.A_DIM,
        "win": curses.A_BOLD,
        "warn": curses.A_BOLD,
        "key": 0,
    }
    if curses.has_colors():
        curses.start_color()
        try:
            curses.use_default_colors()
            background = -1
        except curses.error:
            background = curses.COLOR_BLACK
        for pair, (name, color) in enumerate(
            (
                ("head", curses.COLOR_CYAN),
                ("win", curses.COLOR_GREEN),
                ("warn", curses.COLOR_YELLOW),
                ("key", curses.COLOR_MAGENTA),
            ),
            start=1,
        ):
            curses.init_pair(pair, color, background)
            styles[name] |= curses.color_pair(pair)
    return styles


def paint(stdscr, styles, lines, cursor_line, top, status):
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    body = max(1, height - 2)
    top = min(top, cursor_line) if cursor_line < top + body else cursor_line - body + 1
    top = max(0, min(top, len(lines) - body))
    for y, line in enumerate(lines[top : top + body]):
        x, selected = 0, top + y == cursor_line
        extra = curses.A_REVERSE if selected else 0
        for text, style in line + ([(" " * width, "")] if selected else []):
            if x >= width - 1:
                break
            stdscr.addnstr(y, x, text, width - 1 - x, styles[style] | extra)
            x += len(text)
    if height > 2:
        stdscr.addnstr(height - 2, 0, status, width - 1, styles["warn"])
    stdscr.addnstr(height - 1, 0, FOOTER, width - 1, styles["dim"])
    stdscr.refresh()
    return top


def run(stdscr, ed):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    styles = init_styles()
    cursor, top, status, quit_armed, view = 0, 0, "", False, VIEWS[0]
    while True:
        rows = build_rows(ed)
        cursor = min(cursor, len(rows) - 1)
        row = rows[cursor]
        lines, cursor_line = build_lines(ed, rows, cursor, view)
        top = paint(stdscr, styles, lines, cursor_line, top, status)
        key = stdscr.getch()
        status, armed = "", False
        char = chr(key) if 0 <= key < 256 else "\0"
        editing = (
            key
            in (
                curses.KEY_LEFT,
                curses.KEY_RIGHT,
                curses.KEY_BACKSPACE,
                curses.KEY_DC,
                127,
            )
            or char in "hl012345xcd"
        )
        if editing and ed.error:
            status = "Editing is off until settings.json is valid JSON."
        elif key in (curses.KEY_UP,) or char == "k":
            cursor = max(0, cursor - 1)
        elif key in (curses.KEY_DOWN,) or char == "j":
            cursor = min(len(rows) - 1, cursor + 1)
        elif key in (curses.KEY_LEFT, curses.KEY_RIGHT) or char in "hl":
            step = 1 if key == curses.KEY_RIGHT or char == "l" else -1
            value = ed.get(row.path)
            index = row.choices.index(value) if value in row.choices else 0
            ed.set(row.path, row.choices[(index + step) % len(row.choices)])
        elif key in (curses.KEY_BACKSPACE, curses.KEY_DC, 127) or char in "0x":
            ed.set(row.path, None)
        elif char in "12345":
            level = FIVE[int(char) - 1]
            if level in row.choices:
                ed.set(row.path, level)
            else:
                status = f"{row.label} doesn't take {level}."
        elif char == "c":
            if row.model:
                path = ed.model_path(row.model, "maxEffortLevel")
                choices = (None, *FIVE)
                current = ed.get(path)
                ed.set(
                    path,
                    choices[
                        (choices.index(current) + 1) % len(choices)
                        if current in choices
                        else 1
                    ],
                )
            else:
                status = "c sets a cap on a model row."
        elif char == "d":
            if row.model:
                ed.set(
                    ("model",),
                    next((a for a, m in ALIASES.items() if m == row.model), row.model),
                )
            else:
                status = "d works on a model row."
        elif char == "\t":
            view = VIEWS[(VIEWS.index(view) + 1) % len(VIEWS)]
        elif char == "w":
            status = ed.save()
        elif char == "r":
            ed.reload()
            status = "Reloaded from disk."
        elif char == "q":
            if not ed.dirty or quit_armed:
                return
            status, armed = (
                "Unsaved changes: w saves, q again quits without saving.",
                True,
            )
        quit_armed = armed


def main(argv=None):
    argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    ).parse_args(argv)
    locale.setlocale(locale.LC_ALL, "")
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    ed = Editor(config_dir, os.getcwd(), MANAGED_DIR, dict(os.environ))
    try:
        curses.wrapper(run, ed)
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
