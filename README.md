# claude-toolbench

A personal marketplace for developing and testing Claude Code plugins.

## Layout

```
.
├── .claude-plugin/
│   └── marketplace.json          # marketplace catalog
├── plugins/
│   └── hello-world/              # reference plugin
│       ├── .claude-plugin/plugin.json
│       ├── skills/
│       ├── agents/
│       ├── hooks/
│       └── scripts/
├── CLAUDE.md                     # plugin development cheat sheet
└── README.md
```

## Usage

### Install the marketplace locally

```bash
# from inside Claude Code
/plugin marketplace add /Users/chris/GitHub/claude-toolbench
/plugin install hello-world@claude-toolbench
```

### Iterate on a plugin without installing

```bash
claude --plugin-dir ./plugins/hello-world
```

After edits, run `/reload-plugins` inside the session.

### Add a new plugin

```bash
mkdir -p plugins/<name>/.claude-plugin
# write plugins/<name>/.claude-plugin/plugin.json
# add skills/, agents/, hooks/, etc.
# add an entry to .claude-plugin/marketplace.json
```

See [CLAUDE.md](./CLAUDE.md) for plugin authoring conventions and the magic-syntax cheat sheet.
