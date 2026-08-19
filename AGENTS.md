# AGENTS.md — liva-toolbench

This repo is a **plugin marketplace and development sandbox** for Claude Code and Codex. Each subdirectory under `plugins/` is a self-contained plugin you can install via the marketplace catalogs or load directly for fast iteration.

When working in this repo, you are usually creating, editing, or testing plugin components. Optimize for fast feedback (`--plugin-dir` + `/reload-plugins` for Claude Code; reinstall from the local Codex marketplace after manifest/version changes). There is no `hello-world/` reference plugin anymore; use the existing plugin nearest your task as the reference (`crank` for the full cross-harness workflow, `crank-lite` for a small multi-skill plugin, `effective-html` for a single-skill plugin).

---

## Repo layout

```
.
├── .claude-plugin/
│   └── marketplace.json          # Claude Code marketplace catalog
├── .agents/
│   └── plugins/marketplace.json  # Codex local marketplace index
└── plugins/
    └── <plugin-name>/
        ├── .claude-plugin/
        │   └── plugin.json        # Claude manifest (only file inside .claude-plugin/)
        ├── .codex-plugin/
        │   └── plugin.json        # Codex manifest for cross-harness plugins
        ├── skills/<name>/
        │   ├── SKILL.md             # shared skill instructions + frontmatter
        │   └── agents/openai.yaml   # Codex skill UI/invocation metadata
        ├── commands/<name>.md     # legacy slash commands (skills are preferred)
        ├── agents/<name>.md       # Claude Code subagent definitions
        ├── hooks/hooks.json       # event hooks
        ├── .mcp.json              # MCP server configs
        ├── .lsp.json              # LSP server configs
        ├── monitors/monitors.json # background monitors
        ├── bin/                   # executables added to PATH while plugin is enabled
        ├── settings.json          # default settings (only `agent` and `subagentStatusLine` keys)
        └── scripts/               # arbitrary helper scripts (referenced via ${CLAUDE_PLUGIN_ROOT})
```

The current plugins (`crank`, `crank-lite`, `effective-html`) all ship as cross-harness plugins and currently contain manifests plus `skills/`. Other component directories shown above are supported by the plugin format when a plugin needs them.

> **Common mistake**: only `plugin.json` goes inside `.claude-plugin/` or `.codex-plugin/`. Skills, commands, agents, hooks, scripts, and other runtime files live at the **plugin root**.

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
   { "name": "<name>", "source": "./plugins/<name>", "description": "...", "version": "0.1.0", "category": "tools" }
   ```
5. If the plugin should work in Codex too, add `plugins/<name>/.codex-plugin/plugin.json`:
   ```json
   {
     "name": "<name>",
     "version": "0.1.0",
     "description": "...",
     "keywords": ["..."],
     "interface": { "displayName": "<Title Case>", "developerName": "Chris Liva" }
   }
   ```
6. Register cross-harness plugins in `.agents/plugins/marketplace.json`:
   ```json
   {
     "name": "<name>",
     "source": { "source": "local", "path": "./plugins/<name>" },
     "category": "tools",
     "policy": {
       "installation": "AVAILABLE",
       "authentication": "ON_INSTALL"
     }
   }
   ```
7. Test locally without reinstalling in Claude Code:
   ```bash
   claude --plugin-dir ./plugins/<name>
   ```
   Then `/reload-plugins` inside the session after edits.
8. Test Codex installation after Codex manifest or marketplace changes:
   ```bash
   codex plugin add <name>@liva-toolbench
   ```

---

## Cross-harness plugins (Claude Code + Codex)

Cross-harness plugins ship for **both** Claude Code and Codex — they carry a
`.codex-plugin/plugin.json` beside `.claude-plugin/plugin.json`, and both manifests
read the same `skills/` tree. All current marketplace plugins are cross-harness:
`crank`, `crank-lite`, and `effective-html`.

**The Codex manifest** mirrors the Claude one for `name`, `version`, `description`,
and `keywords`, and adds an `interface` block for Codex display metadata:

```json
{
  "name": "<name>",
  "version": "<x.y.z>",
  "description": "...",
  "keywords": ["..."],
  "interface": {
    "displayName": "<Title Case>",
    "developerName": "Chris Liva"
  }
}
```

`crank-lite` uses a richer Codex `interface` with `shortDescription`,
`longDescription`, `category`, `capabilities`, and `defaultPrompt`; follow that shape
when the plugin needs a better Codex marketplace presentation.

**Two things make a plugin installable under Codex, not one** — a valid
`.codex-plugin/plugin.json` is necessary but not sufficient:

1. The per-plugin `.codex-plugin/plugin.json` above.
2. An entry in the repo's **Codex marketplace index**, `.agents/plugins/marketplace.json`
   — the local-marketplace catalog Codex reads (`codex plugin marketplace list` shows it
   rooted at the repo). A plugin absent from it can't be installed even with a perfect
   `.codex-plugin/plugin.json`: `codex plugin add <name>@liva-toolbench` fails with
   *"not found in marketplace."* Add a `local` source entry beside the others:

   ```json
   {
     "name": "<name>",
     "source": { "source": "local", "path": "./plugins/<name>" },
     "category": "tools",
     "policy": {
       "installation": "AVAILABLE",
       "authentication": "ON_INSTALL"
     }
   }
   ```

   Then `codex plugin add <name>@liva-toolbench` to install (re-run after a version bump
   to refresh the snapshot). This index is **separate from** Claude's
   `.claude-plugin/marketplace.json` and must be kept in sync by hand — it's easy to ship
   a `.codex-plugin/` manifest and forget to register the plugin here.

**Cross-harness skills keep shared instructions but use per-harness metadata.**
Keep the Claude Code fields a skill needs in `SKILL.md`; Codex tolerating an unknown
frontmatter key does not make that key a Codex control. Put Codex-specific UI and
invocation metadata in the skill-local `skills/<skill-name>/agents/openai.yaml` —
not the plugin root's `agents/` directory:

```yaml
interface:
  display_name: "My Skill"
  short_description: "A 25-64 character UI description"
  default_prompt: "Use $my-skill to ..."

policy:
  allow_implicit_invocation: false
```

Quote string values. `default_prompt` must mention the skill as `$<skill-name>`
(including the plugin namespace when installed from a plugin). Codex defaults
`allow_implicit_invocation` to `true`; set it to `false` whenever the shared
`SKILL.md` has Claude Code's `disable-model-invocation: true`. One field does not
configure the other harness.

**In a cross-harness plugin, skill/agent bodies must not depend on Claude-only
preprocessing** — none of it runs under Codex:

- `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_SKILL_DIR}`, and every other `${CLAUDE_*}` substitution
- `@file` includes
- `` !`cmd` `` / ` ```! ` bang shell execution
- `$ARGUMENTS`, `$0`, `$1`, and named argument substitution

**Skill prose must be harness-agnostic, not just preprocessing-free.** Describe
subagent work at the capability level ("dispatch a standard-tier subagent to …"),
never with Claude-specific tool or agent-type names, and never by referencing this
repo's internal agent definitions (`crank-*` agents). Per-harness specifics — the
standard/heavy subagent model tiers and effort mappings for Claude Code, Codex, and
Cursor — live in one small XML block per skill, not scattered through the body.

**Sharing a reference file between two skills:** keep the **canonical** file in one
skill's directory and commit a **real copy** into every other skill that needs it,
each `SKILL.md` referencing its own copy with a relative link — `[FILE.md](FILE.md)`.
**Never symlink** (per project decision: the Codex plugin installer drops symlinks
when it snapshots a plugin, so symlinked reference files silently vanish from Codex
installs — real copies are the only shape that survives every harness). Don't add a
`_shared/` dir reached by an absolute or `${CLAUDE_PLUGIN_ROOT}` path either. Example:
the canonical `SUBAGENT-TIERS.md` lives in `plugins/crank/skills/crank/` (the
coordinator skill's directory, alongside the phase files); the other crank skills
carry identical copies.

Copies are synced by hand, like version strings: edit the canonical file, re-copy it
over the others, and verify before committing (no output = in sync):

```bash
for f in plugins/crank/skills/*/{SUBAGENT-TIERS,VOCABULARY,GRILLING,READBACK,ARTIFACT-HOME}.md \
         plugins/crank-lite/skills/*/ARTIFACT-HOME.md; do
  diff -q "plugins/crank/skills/crank/$(basename "$f")" "$f"
done
diff -q plugins/crank/skills/crank/VOCABULARY.md plugins/crank-lite/skills/lite-deepen/VOCABULARY.md
diff -q plugins/crank/skills/crank/VOCABULARY.md plugins/crank-lite/skills/lite-review/VOCABULARY.md
diff -q plugins/crank-lite/skills/crank-lite/INTERVIEW.md plugins/crank-lite/skills/lite-deepen/INTERVIEW.md
```

---

## Bumping a plugin version

A plugin's version is **duplicated across several files that must be kept in sync by hand** — bump them together in one commit, or installers read a stale version. For a plugin named `<name>`:

| File | What to change | Applies to |
| ---- | -------------- | ---------- |
| `plugins/<name>/.claude-plugin/plugin.json` | top-level `"version"` | every plugin |
| `.claude-plugin/marketplace.json` → the plugin's entry in `plugins[]` | that entry's `"version"` | every plugin |
| `plugins/<name>/.codex-plugin/plugin.json` | top-level `"version"` | **cross-harness plugins only** |

So a future **Claude-only** plugin has **two** version strings to bump; every current
plugin is **cross-harness** and has **three**. Forgetting the marketplace-catalog copy
is the easy miss — the per-plugin manifest and the catalog entry are separate files.

`.agents/plugins/marketplace.json` (the Codex marketplace index) carries **no** `version` field, so there is nothing to bump there; its `source`, `category`, and `policy` metadata are unversioned. After a cross-harness bump, re-run `codex plugin add <name>@liva-toolbench` to refresh its snapshot instead.

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

## Skill frontmatter (portable fields + Claude Code extensions)

`name` and `description` are required portable Agent Skills fields;
`allowed-tools` is portable but experimental. The remaining fields shown below
are Claude Code extensions. Cross-harness skills may retain them for Claude Code,
but must use `agents/openai.yaml` for Codex-specific UI and invocation policy.

```yaml
---
name: my-skill                       # portable; must match the directory name
description: When to use this skill  # portable and required; drives matching
when_to_use: Extra trigger phrases   # Claude Code
argument-hint: "[name] [format]"     # Claude Code autocomplete hint
arguments: name format               # Claude Code positional arguments
disable-model-invocation: true       # Claude Code explicit-only; mirror in openai.yaml
user-invocable: false                # Claude Code model-only invocation
allowed-tools: Read Grep             # portable but experimental
model: sonnet                        # Claude Code model override
effort: high                         # Claude Code effort override
context: fork                        # Claude Code forked context
agent: Explore                       # Claude Code subagent type
paths: "src/**/*.ts"                 # Claude Code path-scoped loading
hooks: { PreToolUse: [...] }         # Claude Code skill-scoped hooks
---
```

**Rule of thumb for descriptions**: lead with the use case, include trigger phrases the user is likely to say, keep combined `description` + `when_to_use` under ~1,500 chars (it gets truncated).

For cross-harness skills, keep `description` itself within the portable Agent
Skills limit of 1,024 characters and put the Codex trigger conditions directly
in it; Codex does not use Claude Code's `when_to_use` extension.

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

Required: `name`, `owner.name`, `plugins[]`. Each plugin entry needs `name` + `source`. The current catalog uses local relative paths, but source can be:

| Source kind   | Shape                                                          |
| ------------- | -------------------------------------------------------------- |
| Relative path | `"./plugins/foo"` (relative string sources must start with `./`) |
| GitHub        | `{ "source": "github", "repo": "owner/repo", "ref": "v1" }`    |
| Git URL       | `{ "source": "url", "url": "https://...", "sha": "..." }`      |
| Git subdir    | `{ "source": "git-subdir", "url": "...", "path": "tools/..." }` |
| npm           | `{ "source": "npm", "package": "@scope/pkg", "version": "1" }` |

For relative string sources, keep the `./` prefix — write `"source": "./plugins/foo"`,
not `"source": "plugins/foo"`. Object sources use the shapes above instead of a
relative string.

---

## Iteration loop

```bash
# fast feedback while developing one plugin
claude --plugin-dir ./plugins/<name>
```

Headless runs (`claude -p …`) bill against the Claude subscription, not metered API
spend — running smoke tests or eval trials is not a cost concern.

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
…)` marker, not just in chat — e.g. a reference doc that pins a library choice notes
it "(per project decision: …)" beside the choice. This is what stops coding
agents from re-suggesting the option you already ruled out.

---

## Official documentation

- OpenAI plugins: <https://developers.openai.com/plugins>
- OpenAI plugin packaging and marketplace metadata: <https://developers.openai.com/plugins/build/plugins>
- OpenAI skill authoring and metadata: <https://learn.chatgpt.com/docs/build-skills>
- Portable Agent Skills specification: <https://agentskills.io/specification>
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
