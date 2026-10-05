# pstack-claude

A Claude Code port of [pstack](https://github.com/cursor/plugins/tree/main/pstack), poteto's agent
workflow plugin for Cursor. Same skills, same playbooks, same principles, same `poteto-agent`.

Everything is carried over verbatim except the platform substitutions documented in
[`PORTING.md`](./PORTING.md). Read that before trusting the port.

Upstream is by [Lauren Tan (poteto)](https://x.com/poteto), MIT licensed. This repo is a port, not a fork
with opinions.

## Install

From a Claude Code session, anywhere the repo is reachable:

```
/plugin marketplace add elijahbowie/pstack-claude
/plugin install pstack@pstack-claude
```

For a local checkout instead of a GitHub remote:

```
/plugin marketplace add /Users/elijahbowie/pstack-claude
/plugin install pstack@pstack-claude
```

Installing from a GitHub remote is what makes this work in Claude Code on the web and in cloud
sessions. A local path only works on the machine that holds it.

## Use

```
/pstack:poteto-mode this pr has a subtle bug where the scroll drifts every 750ms even when idle. repro
first, then fix and verify.
```

Optionally run `/pstack:setup-pstack` once to pin which model runs each role. It writes
`~/.claude/pstack-models.md`. Without it the defaults apply: `sonnet` for code delegates, `opus` for
prose and judgment.

`pstack:poteto-agent` is available as a plugin subagent type, so `/pstack:poteto-mode` and spawned delegates share one style.

49 of the 51 skills carry `disable-model-invocation: true`, which is upstream's setting. Claude Code
honours it the same way Cursor did, so those skills only run when you type `/pstack:name`. They will not
auto-trigger, and they will not appear in the model's own skill list. `setup-pstack` and `poteto-help` are the exceptions.

## What's inside

51 skills, 2 agents, 23 playbooks, synced to upstream **0.15.10**. The entry points are `/pstack:poteto-mode` and `/pstack:setup-pstack`. The rest
are situational and the mode skill routes to them for you.

See [`plugins/pstack/README.md`](./plugins/pstack/README.md) for poteto's full description of the
workflows, and [`plugins/pstack/docs/guide/`](./plugins/pstack/docs/guide/) for the guide.

## Update an installed copy

```text
/plugin marketplace update pstack-claude
/plugin update pstack@pstack-claude
```

Restart Claude Code after updating. Model choices written by older versions stay pinned; delete
role lines you want to reset, then rerun `/pstack:setup-pstack`.

For standalone cloud-session configuration, run `tools/vendor-into-repo.sh /path/to/target/repo`
and commit the generated `.claude/` files in that repository. Vendored commands use `/poteto-mode`
and `/setup-pstack` without the plugin namespace.
