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
/plugin marketplace add <owner>/pstack-claude
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
/poteto-mode this pr has a subtle bug where the scroll drifts every 750ms even when idle. repro
first, then fix and verify.
```

Optionally run `/setup-pstack` once to pin which model runs each role. It writes
`~/.claude/pstack-models.md`. Without it the defaults apply: `sonnet` for code delegates, `fable` for
prose and judgment.

`poteto-agent` is available as a subagent type, so `/poteto-mode` and spawned delegates share one style.

## What's inside

47 skills, 2 agents, 23 playbooks. The entry points are `/poteto-mode` and `/setup-pstack`. The rest
are situational and the mode skill routes to them for you.

See [`plugins/pstack/README.md`](./plugins/pstack/README.md) for poteto's full description of the
workflows, and [`plugins/pstack/docs/guide/`](./plugins/pstack/docs/guide/) for the guide.
