#!/usr/bin/env python3
"""sandboxed_claude.py <run-root> <plugin-dir> <claude args...>: start one headless session inside the OS sandbox.

A headless session skips permission prompts on the user's machine, so nothing here relies on the agent staying put.
Seatbelt holds every shell command and its children to the run root, with home unreadable and the network limited to
package registries. Seatbelt covers shell commands only, so the tool allowlist closes the tools that act on the user's
account from outside it. The file tools and WebFetch stay outside it too; a harness that needs them bounded adds a hook.
"""
import json
import os
import re
import sys
from pathlib import Path

# a session keeps only these, so an SSH agent, CLI login, or API key in the caller's environment never reaches it
SESSION_ENV = ("HOME", "USER", "LOGNAME", "PATH", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE", "TERM", "SHELL",
               "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_DISABLE_1M_CONTEXT")
# per project decision: an allowlist, because RemoteTrigger, PushNotification, SendMessage, and the like act on the user's account outside the sandbox
SESSION_TOOLS = ["Agent", "Task", "Bash", "Edit", "Glob", "Grep", "Read", "Skill", "ToolSearch", "WebFetch", "WebSearch", "Write"]
TOOL_FLAGS = ["--tools", ",".join(SESSION_TOOLS)]
# per project decision: shell commands reach package registries and nothing else
PUBLIC_HOSTS = ["registry.npmjs.org", "pypi.org", "files.pythonhosted.org"]
OWN_PLUGINS_OFF = {"crank@liva-toolbench": False, "crank-lite@liva-toolbench": False}


def clean_env():
    return {k: os.environ[k] for k in SESSION_ENV if k in os.environ}


def session_env(root):
    """The environment a sandboxed session runs in.

    Seatbelt denies with EPERM, which git treats as fatal on ~/.gitconfig and npm on ~/.npm, and which stops pnpm reaching
    the version a project pins, so all three keep their state under the run root. Losing ~/.gitconfig loses the identity a
    session needs to commit.
    """
    identity = {f"GIT_{who}_{field}": value for who in ("AUTHOR", "COMMITTER")
                for field, value in (("NAME", "Headless session"), ("EMAIL", "session@localhost"))}
    return {**clean_env(), **identity, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "XDG_CONFIG_HOME": f"{root}/xdg",
            "npm_config_cache": f"{root}/npm", "PNPM_HOME": f"{root}/pnpm"}


def settings(root, repo, *readable):
    """The `--settings` a session runs under. `readable` names paths a shell command reads beyond the run root."""
    spill = re.sub(r"[^A-Za-z0-9]", "-", str(Path(repo).resolve()))  # Claude Code spills a large tool result here and hands the agent the path
    allow = [f"~/.claude/projects/{spill}", "~/.claude/shell-snapshots", str(Path(root).resolve()), *map(str, readable)]
    return {"enabledPlugins": OWN_PLUGINS_OFF,
            "sandbox": {"enabled": True, "failIfUnavailable": True, "allowUnsandboxedCommands": False,
                        "filesystem": {"denyRead": ["~/"], "allowRead": allow, "allowWrite": [str(Path(root).resolve())]},
                        "network": {"allowedDomains": PUBLIC_HOSTS, "strictAllowlist": True}}}


if __name__ == "__main__":
    run_root, plugin, *args = sys.argv[1:]
    # --tools takes a list, so another flag has to follow it
    os.execvpe("claude", ["claude", *TOOL_FLAGS, "--settings", json.dumps(settings(run_root, Path.cwd(), plugin)), *args], session_env(run_root))
