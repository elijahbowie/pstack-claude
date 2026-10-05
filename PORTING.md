# Porting notes: Cursor pstack -> Claude Code

This ports [`cursor/plugins/pstack`](https://github.com/cursor/plugins/tree/main/pstack)
**0.15.10**, from commit [`4e5b1cf2ccb0ea3716f08c8ee0a5856b5ab93536`](https://github.com/cursor/plugins/commit/4e5b1cf2ccb0ea3716f08c8ee0a5856b5ab93536).
It contains 51 skills, 2 agents, and 23 playbooks. Workflow prose, references, and scripts are
preserved except for the platform substitutions below. The Cursor Automations pack is copied
verbatim as reference material.

## Platform substitutions

| Cursor | Claude Code |
|---|---|
| `.cursor-plugin/plugin.json` | `.claude-plugin/plugin.json` plus the root marketplace manifest |
| Explicit `skills` / `agents` manifest paths | Automatic discovery of `skills/` and `agents/` |
| Unscoped slash skills | `/pstack:<skill>` for plugin installs; unscoped for standalone vendoring |
| `poteto-agent` / `Comment Sicko` subagent types | `pstack:poteto-agent` / `pstack:comment-sicko` for plugin installs |
| `Task` | `Agent` |
| `AskQuestion` | `AskUserQuestion` |
| `generalPurpose` | `general-purpose` |
| `is_background: true` agent frontmatter | `background: true`; explicit `run_in_background: true` calls are retained |
| `environment: "cloud"` | `isolation: "worktree"`; this isolates files on the local machine |
| `cloud_base_branch` | Create a worktree from the desired branch and provide its path in the brief |
| `~/.cursor/rules/pstack-models.mdc` | `~/.claude/pstack-models.md`, read explicitly by the skills |
| Cursor skill/plugin/project paths | Corresponding `.claude` paths |
| Cursor transcript audit directory | `~/.claude/projects`, including nested session and subagent logs |

The names `Poteto Mode`, `Make Bot UI`, and `Comment Sicko` are kebab-cased in frontmatter.
Cursor-only `mode`, `icon`, `color`, `reminder`, and TypeScript `paths` frontmatter is removed.
`disable-model-invocation: true` is retained on 49 skills; `setup-pstack` and `poteto-help` can
also be selected by the model. Help, installation, and guide instructions use Claude commands.
Public help links point to this port so users see the same platform instructions as their agent.

## Models and budget

| Upstream default | Role | Claude Code alias |
|---|---|---|
| `grok-4.7-xhigh-fast` | Code delegate | `sonnet` |
| `claude-opus-5-5-max` | Hardest tasks, prose, judgment | `opus` |
| `gpt-5.6-sol-max` | Adversarial reviewer | `opus` |

`inherit-parent` and `auto` mean omit the Agent `model` field. Panel lists keep their seat count,
including repeated aliases. The default panel is `opus`, `opus`, `sonnet`.

Claude aliases do not encode reasoning effort. `/pstack:setup-pstack` therefore offers model-cost
budgets and validates model aliases; it never appends Cursor effort suffixes. Configure reasoning
effort separately in Claude Code. Its configuration file has no `alwaysApply` metadata and is
read explicitly rather than injected as a rule. Old configured choices remain pinned until removed.

## External dependencies

- Cursor's `deslop` references use the bundled `/pstack:unslop` skill.
- `control-ui` and `control-cli` use the repository's own harness, such as Playwright, CDP, or a pty.
- Skill authoring uses `skill-development` from Anthropic's `plugin-dev` plugin.
- `/loop` is Claude Code's built-in command. The pstack Babysit playbook owns PR-status workflows.

## Known gaps

1. **Narrower model diversity.** All delegates use Claude aliases. Repeated Opus reviewers retain
   review separation, but cannot reproduce upstream's cross-family disagreement.
2. **No Cursor Custom Mode.** Invoke `/pstack:poteto-mode` for each new task. A persistent project
   preference can go in `CLAUDE.md`. Cursor's per-turn reminder and TypeScript auto-attachment are
   unavailable in this port.
3. **Local worktrees are not hosted cloud workers.** They share this machine. Cursor cloud
   concurrency, dashboard, durable restacks, and restart recovery are unavailable. The Orchestrate
   playbook carries an explicit limitation and routes to Autonomous run with local workers unless
   an external harness supplies those capabilities. Nested spawning depends on the session's depth
   limit; a leaf agent executes directly when spawning is unavailable.
4. **`make-bot-ui` and `automations/benny` remain Cursor-only.** They require Cursor Automations
   and its webhook endpoint. Included files do not supply equivalent Claude automations.
5. **Transcript-driven history needs care.** The cleanup audit scans Claude's local transcript store,
   but cannot infer pinned or active chats. Missing transcripts never establish that a worktree is
   unused. Other history workflows retain upstream's transcript assumptions and may need a local
   transcript adapter. Cursor application-cache examples are reference only.

Claude tool and skill behavior was checked against the installed CLI and the official
[subagent documentation](https://code.claude.com/docs/en/sub-agents) and
[skill documentation](https://code.claude.com/docs/en/skills). Static validation does not establish
that every agent workflow runs end to end on every Claude deployment.

## Reproduce and verify

Clone `cursor/plugins`, check out the commit above, then run from this repository:

```sh
python3 tools/port.py /path/to/cursor-plugins/pstack
python3 -m unittest discover -s tools -p 'test_*.py'
claude plugin validate . --strict
claude plugin validate plugins/pstack --strict
```

`--dest-repo /path/to/repo` writes into another repository. Every substitution must match; generation
and rule validation happen in a temporary directory before the existing port is replaced. Failed
rules leave the destination unchanged. Repeated runs against the same upstream produce identical
file contents. Automation files and binary assets are copied without transformation.

`tools/vendor-into-repo.sh /path/to/target/repo` copies the bundled skills and agents into `.claude/`
and removes plugin namespaces for standalone discovery, preserving unrelated skills and agents.
