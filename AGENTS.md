# AGENTS.md — liva-toolbench

This repo is a **plugin marketplace and development sandbox** for Claude Code. Each subdirectory under `plugins/` is a self-contained plugin you can install via this marketplace or load directly with `--plugin-dir` for fast iteration.

When working in this repo, you are usually creating, editing, or testing plugin components. Optimize for fast feedback (`--plugin-dir` + `/reload-plugins`) and treat `hello-world/` as the canonical reference for what a healthy plugin looks like.

---

## Repo layout

```
.
├── .claude-plugin/
│   └── marketplace.json          # marketplace catalog (lists all plugins)
└── plugins/
    └── <plugin-name>/
        ├── .claude-plugin/
        │   └── plugin.json        # plugin manifest (only file inside .claude-plugin/)
        ├── skills/<name>/SKILL.md # model- or user-invoked skills
        ├── commands/<name>.md     # legacy slash commands (skills are preferred)
        ├── agents/<name>.md       # subagent definitions
        ├── hooks/hooks.json       # event hooks
        ├── .mcp.json              # MCP server configs
        ├── .lsp.json              # LSP server configs
        ├── monitors/monitors.json # background monitors
        ├── bin/                   # executables added to PATH while plugin is enabled
        ├── settings.json          # default settings (only `agent` and `subagentStatusLine` keys)
        └── scripts/               # arbitrary helper scripts (referenced via ${CLAUDE_PLUGIN_ROOT})
```

> **Common mistake**: only `plugin.json` goes inside `.claude-plugin/`. Skills, commands, agents, and hooks live at the **plugin root**.

---

## Authoring a new plugin

1. `mkdir -p plugins/<name>/.claude-plugin`
2. Write `plugins/<name>/.claude-plugin/plugin.json`:
   ```json
   {
     "name": "<name>",
     "description": "...",
     "version": "0.1.0",
     "author": { "name": "Chris" }
   }
   ```
3. Add components (`skills/`, `agents/`, `hooks/`, …) at the plugin root.
4. Register it in `.claude-plugin/marketplace.json` under `plugins[]`:
   ```json
   { "name": "<name>", "source": "./plugins/<name>", "description": "..." }
   ```
5. Test locally without reinstalling:
   ```bash
   claude --plugin-dir ./plugins/<name>
   ```
   Then `/reload-plugins` inside the session after edits.

---

## Cross-harness plugins (Claude Code + Codex)

Some plugins ship for **both** Claude Code and Codex — they carry a
`.codex-plugin/plugin.json` beside `.claude-plugin/plugin.json`, and both manifests
read the same `skills/` tree. `crank` is the cross-harness flagship; other plugins
are Claude-only unless they grow a `.codex-plugin/`.

**The Codex manifest** mirrors the Claude one (`name`, `version`, `description`,
`keywords`) but swaps `author`/`license` for an `interface` block:

```json
{
  "name": "<name>",
  "version": "<x.y.z>",
  "description": "...",
  "keywords": ["..."],
  "interface": { "displayName": "<Title Case>", "developerName": "Chris Liva" }
}
```

**Two things make a plugin installable under Codex, not one** — a valid
`.codex-plugin/plugin.json` is necessary but not sufficient:

1. The per-plugin `.codex-plugin/plugin.json` above.
2. An entry in the repo's **Codex marketplace index**, `.agents/plugins/marketplace.json`
   — the local-marketplace catalog Codex reads (`codex plugin marketplace list` shows it
   rooted at the repo). A plugin absent from it can't be installed even with a perfect
   `.codex-plugin/plugin.json`: `codex plugin add <name>@liva-toolbench` fails with
   *"not found in marketplace."* Add a `local` source entry beside the others:

   ```json
   { "name": "<name>", "source": { "source": "local", "path": "./plugins/<name>" }, "category": "tools" }
   ```

   Then `codex plugin add <name>@liva-toolbench` to install (re-run after a version bump
   to refresh the snapshot). This index is **separate from** Claude's
   `.claude-plugin/marketplace.json` and must be kept in sync by hand — it's easy to ship
   a `.codex-plugin/` manifest and forget to register the plugin here.

**In a cross-harness plugin, skill/agent bodies must not depend on Claude-only
preprocessing** — none of it runs under Codex:

- `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_SKILL_DIR}`, and every other `${CLAUDE_*}` substitution
- `@file` includes
- `` !`cmd` `` / ` ```! ` bang shell execution

**Sharing a reference file between two skills:** keep the real file in one skill's
directory, **symlink** it into the other, and reference it with a relative link —
`[FILE.md](FILE.md)` (the pattern mattpocock's skills use). Don't add a `_shared/`
dir reached by an absolute or `${CLAUDE_PLUGIN_ROOT}` path. Example:
`crank/skills/crank-plan/HTML-REVIEW.md` symlinks to `../crank-spec/HTML-REVIEW.md`, and both
`SKILL.md`s link to it relatively.

> Symlinks only survive a `core.symlinks=true` checkout (macOS/Linux default). If a
> Windows checkout is in scope, commit a copy in each directory instead.

---

## Bumping a plugin version

A plugin's version is **duplicated across several files that must be kept in sync by hand** — bump them together in one commit, or installers read a stale version. For a plugin named `<name>`:

| File | What to change | Applies to |
| ---- | -------------- | ---------- |
| `plugins/<name>/.claude-plugin/plugin.json` | top-level `"version"` | every plugin |
| `.claude-plugin/marketplace.json` → the plugin's entry in `plugins[]` | that entry's `"version"` | every plugin |
| `plugins/<name>/.codex-plugin/plugin.json` | top-level `"version"` | **cross-harness plugins only** |

So a **Claude-only** plugin has **two** version strings to bump; a **cross-harness** plugin (e.g. `crank`) has **three**. Forgetting the marketplace-catalog copy is the easy miss — the per-plugin manifest and the catalog entry are separate files.

`.agents/plugins/marketplace.json` (the Codex marketplace index) carries **no** `version` field — it only lists `source`/`category`, so there is nothing to bump there. After a cross-harness bump, re-run `codex plugin add <name>@liva-toolbench` to refresh its snapshot instead.

Verify every copy agrees before committing — all should show the **same new** version with no straggler on the old number:

```bash
grep -rn --include='*.json' '"version"' plugins/<name> .claude-plugin/marketplace.json
```

(The `marketplace.json` grep also lists sibling plugins; read the line for `<name>`.)

---

## Magic syntax cheat sheet

> **Claude-only.** Everything in this section is Claude Code preprocessing — it does
> **not** run under Codex. In a cross-harness plugin (see *Cross-harness plugins*),
> avoid all of it; use plain prose + relative file links instead.

These work inside skill `SKILL.md` and command `.md` bodies. They are **preprocessing** — they expand before Claude sees the content.

### Bang prefix `` !`<command>` `` — inline shell

Runs a shell command and replaces the marker with the command's stdout before the prompt is sent to Claude. Use this to inject live state (git diff, file listing, env versions).

```markdown
## Current changes
!`git diff HEAD`

## Recent files
!`ls -lt | head -5`
```

For multi-line commands, open a fenced block with ` ```! `:

````markdown
```!
node --version
npm --version
git status --short
```
````

Bang execution can be globally disabled via `"disableSkillShellExecution": true` in settings.

### `@` file references

Inside skill or command bodies, `@path/to/file.md` inlines the file's contents at preprocess time. Useful for sharing reference material between skills without duplicating it.

### Argument substitution

| Marker          | Expands to                                                                |
| --------------- | ------------------------------------------------------------------------- |
| `$ARGUMENTS`    | Full argument string passed after the slash command                       |
| `$0`, `$1`, …   | Shorthand for `$ARGUMENTS[0]`, `$ARGUMENTS[1]`, … (shell-style quoting)   |
| `$<name>`       | Named argument declared in `arguments:` frontmatter                       |

Multi-word arguments need quotes: `/my-skill "hello world" second` → `$0` = `hello world`, `$1` = `second`.

### Environment variables (string substitution)

| Variable                   | Meaning                                                                              |
| -------------------------- | ------------------------------------------------------------------------------------ |
| `${CLAUDE_PLUGIN_ROOT}`    | Plugin install dir. Use in **hook commands** to reference bundled scripts.            |
| `${CLAUDE_PLUGIN_DATA}`    | Plugin's persistent data dir (survives plugin updates).                              |
| `${CLAUDE_SKILL_DIR}`      | Directory containing the current `SKILL.md`. Use in `` !`...` `` to call bundled scripts. |
| `${CLAUDE_SESSION_ID}`     | Current session id — handy for per-session log filenames.                            |
| `${CLAUDE_EFFORT}`         | Active effort level (`low`/`medium`/`high`/`xhigh`/`max`).                           |

### Tool calls Claude can make from inside a skill/agent body

When you write skill or agent prose, you can instruct Claude to use specific tools. The names that matter:

- **`Skill`** — invokes another skill by name. `Skill(name="...", args="...")`. Use for composition.
- **`AskUserQuestion`** — pops a structured question UI to the user. Prefer over plain prose questions when you need a discrete answer.
- **`Agent`** — spawns a subagent by `subagent_type`. Use to delegate research/work into its own context window.
- **`@<agent-type>`** in user prose (and inside skills) is the shorthand a user types to mention an agent (e.g. `@example-reviewer can you check this?`). It maps to the `Agent` tool with that subagent type.
- **`TaskCreate` / `TaskUpdate`** — for multi-step work, track progress so the user can see it.
- **`Bash`, `Read`, `Edit`, `Write`, `Grep`, `Glob`** — the standard file/shell tools, gated by `allowed-tools`.

Inside a skill, listing a tool in `allowed-tools` pre-approves it (no permission prompt) while the skill is active. Examples:

```yaml
allowed-tools: Read Grep Glob              # allowlist some safe tools
allowed-tools: Bash(git add *) Bash(git status *)   # narrow Bash matchers
```

---

## Skill frontmatter (most-used fields)

```yaml
---
name: my-skill                       # default: directory name
description: When to use this skill  # required-ish; drives auto-invocation
when_to_use: Extra trigger phrases   # appended to description for matching
argument-hint: "[name] [format]"     # autocomplete hint
arguments: name format               # named positional args (space-sep or YAML list)
disable-model-invocation: true       # only the user can invoke (good for /deploy, /commit)
user-invocable: false                # only Claude can invoke (good for background context)
allowed-tools: Read Grep             # pre-approved tools while active
model: sonnet                        # override model for this skill's turn
effort: high                         # low | medium | high | xhigh | max
context: fork                        # run in a forked subagent context
agent: Explore                       # which subagent type to use (with context: fork)
paths: "src/**/*.ts"                 # only auto-load when working with matching files
hooks: { PreToolUse: [...] }         # skill-scoped hooks
---
```

**Rule of thumb for descriptions**: lead with the use case, include trigger phrases the user is likely to say, keep combined `description` + `when_to_use` under ~1,500 chars (it gets truncated).

---

## Agent frontmatter (most-used fields)

```yaml
---
name: example-reviewer               # required
description: When Claude should delegate to me. Mention "use proactively" if appropriate.
tools: Read, Grep, Glob, Bash        # allowlist; omit to inherit all tools
disallowedTools: Write, Edit         # denylist (applied first)
model: sonnet                        # sonnet | opus | haiku | inherit | full id
permissionMode: default              # acceptEdits | auto | dontAsk | bypassPermissions | plan
maxTurns: 20
skills: [code-review-style]          # preload skill bodies into the agent's context
mcpServers: [github, { playwright: { type: stdio, command: npx, args: [...] } }]
memory: project                      # user | project | local — enables cross-session memory
background: false
isolation: worktree                  # run in a temp git worktree
color: blue                          # red | blue | green | yellow | purple | orange | pink | cyan
---

You are <role>. When invoked: ...
```

> **Plugin-agent restriction**: `hooks`, `mcpServers`, and `permissionMode` are **ignored** when an agent is loaded from a plugin. Move the agent into `~/.claude/agents/` or `.claude/agents/` if you need them.

---

## Hooks (`hooks/hooks.json`)

```json
{
  "description": "What this set of hooks does",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

Common events: `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `PreCompact`, `Notification`, `PermissionRequest`. Hook scripts get the tool input as JSON on stdin (use `jq`) and can emit a permission decision on stdout.

---

## Marketplace manifest (`.claude-plugin/marketplace.json`)

Required: `name`, `owner.name`, `plugins[]`. Each plugin entry needs `name` + `source`. Source can be:

| Source kind   | Shape                                                          |
| ------------- | -------------------------------------------------------------- |
| Relative path | `"./plugins/foo"` (must start with `./`)                       |
| GitHub        | `{ "source": "github", "repo": "owner/repo", "ref": "v1" }`    |
| Git URL       | `{ "source": "url", "url": "https://...", "sha": "..." }`      |
| Git subdir    | `{ "source": "git-subdir", "url": "...", "path": "tools/..." }` |
| npm           | `{ "source": "npm", "package": "@scope/pkg", "version": "1" }` |

`source` must always start with `./` (schema enforces `^\./.*`). `metadata.pluginRoot` sets a base for relative sources but does not let you drop the `./` prefix — write `"source": "./foo"`, not `"source": "foo"`.

---

## Iteration loop

```bash
# fast feedback while developing one plugin
claude --plugin-dir ./plugins/<name>
```

Inside the session:
- `/reload-plugins` — picks up edits to plugin files
- `/agents` — inspect/edit subagents
- `/plugin` — manage installed plugins
- `What skills are available?` — confirm yours appears

---

## Record settled decisions where the next agent will look

When you land a load-bearing design choice inside a skill — a tradeoff a future
review could plausibly reverse (offline vs CDN, port vs direct call, which library)
— record it **inline in that skill's reference doc** with a `(per project decision:
…)` marker, not just in chat. Example: `crank/skills/crank-spec/HTML-REVIEW.md` notes
Tailwind + Mermaid load via CDN "(per project decision)". This is what stops coding
agents from re-suggesting the option you already ruled out.

---

## Official documentation

- Plugins: <https://code.claude.com/docs/en/plugins>
- Plugins reference (full schema): <https://code.claude.com/docs/en/plugins-reference>
- Plugin marketplaces: <https://code.claude.com/docs/en/plugin-marketplaces>
- Discover and install plugins: <https://code.claude.com/docs/en/discover-plugins>
- Skills: <https://code.claude.com/docs/en/skills>
- Subagents: <https://code.claude.com/docs/en/sub-agents>
- Slash commands (legacy — merged into skills): <https://code.claude.com/docs/en/slash-commands>
- Commands reference (built-ins + bundled skills): <https://code.claude.com/docs/en/commands>
- Hooks: <https://code.claude.com/docs/en/hooks>
- MCP servers: <https://code.claude.com/docs/en/mcp>
- Permissions: <https://code.claude.com/docs/en/permissions>
- Settings: <https://code.claude.com/docs/en/settings>
- Memory / CLAUDE.md: <https://code.claude.com/docs/en/memory>
- Doc index for further discovery: <https://code.claude.com/docs/llms.txt>
