# Porting notes: Cursor pstack -> Claude Code

This is a faithful port of [`cursor/plugins/pstack`](https://github.com/cursor/plugins/tree/main/pstack)
at version 0.15.2. Every skill, agent, playbook, reference, and script is carried over byte for byte
except for the platform substitutions listed below. No prose was rewritten, shortened, or "improved".

The port is mechanical and reproducible. A script applies an ordered substitution table and fails if
any rule matches nothing, so a silent partial port is not possible.

## What changed, and why

### Packaging

| Cursor | Claude Code |
|---|---|
| `.cursor-plugin/plugin.json` | `.claude-plugin/plugin.json`, plus a `.claude-plugin/marketplace.json` at the repo root |
| `skills` / `agents` keys in the manifest | implicit, Claude Code discovers `skills/` and `agents/` |

### Frontmatter

Claude Code ignores several Cursor-only keys, so they were dropped rather than left to rot.

| File | Dropped | Effect |
|---|---|---|
| `agents/poteto-agent.md` | `is_background: true` | None. Claude Code `Agent` subagents already run in the background. |
| `skills/poteto-mode/SKILL.md` | `mode: true`, `icon: crown`, `color: yellow` | Cosmetic and Cursor-only. `/poteto-mode` still works. |
| `skills/poteto-mode/SKILL.md` | `reminder: ...` | **Real loss.** Cursor re-surfaced this nudge each new task. See "Known gaps". |
| `skills/typescript-best-practices/SKILL.md` | `paths: ["**/*.ts", "**/*.tsx"]` | **Real loss.** The skill no longer auto-attaches on TS files. Invoke `/typescript-best-practices`, or let `poteto-mode` route to it. |

Three names were kebab-cased, because Claude Code resolves skills and `subagent_type` by slug:
`Poteto Mode` -> `poteto-mode`, `Make Bot UI` -> `make-bot-ui`, `Comment Sicko` -> `comment-sicko`.
`disable-model-invocation: true` is supported by Claude Code and was kept on all 46 skills that had it.

### Tools

| Cursor | Claude Code |
|---|---|
| `Task` tool | `Agent` tool |
| `AskQuestion` | `AskUserQuestion` |
| `subagent_type: generalPurpose` | `subagent_type: general-purpose` |
| `subagent_type: "Comment Sicko"` | `subagent_type: "comment-sicko"` |
| `run_in_background: true` | background execution, the default for `Agent` |
| `environment: "cloud"` | `isolation: "remote"` |
| `environment: "local"` | the default local isolation |
| agent mode vs `readonly: true` | a full-tool agent vs the read-only `Explore` agent |

`subagent_type: "poteto-agent"` is unchanged and works as-is.

### Models

Cursor's slugs do not exist in Claude Code, whose `Agent` tool accepts `opus`, `sonnet`, `haiku`, `fable`.
Each slug was mapped to its nearest role equivalent.

| Cursor slug | role in pstack | Claude Code |
|---|---|---|
| `grok-4.6-fast-xhigh` | fast code delegate | `sonnet` |
| `grok-4.6-medium-fast` | cheapest mechanical edits | `haiku` |
| `claude-fable-5-1-thinking-max` | prose and judgment | `fable` |
| `claude-fable-5-1-thinking-medium` | lighter prose | `fable` |
| `gpt-5.6-sol-max` | diverse adversarial reviewer | `opus` |
| `claude-opus-5-thinking-xhigh` | judgment panel | `opus` |

The aliases `inherit-parent` and `auto` are preserved and still mean "omit `model`".

### Configuration and paths

| Cursor | Claude Code |
|---|---|
| `~/.cursor/rules/pstack-models.mdc` | `~/.claude/pstack-models.md` |
| `~/.cursor/skills/`, `.cursor/skills/` | `~/.claude/skills/`, `.claude/skills/` |
| `~/.cursor/plugins/` | `~/.claude/plugins/` |
| `~/.cursor/projects/` | `~/.claude/projects/` |
| `.cursor/worktrees/` | `.claude/worktrees/` |
| `~/Library/Application Support/Cursor` | `~/Library/Application Support/Claude` |

### External plugin dependencies

pstack referenced skills published by other Cursor plugins. Those do not exist on Claude Code.

| Cursor dependency | replacement |
|---|---|
| `deslop` from `cursor-team-kit` (`/deslop`) | the bundled **unslop** skill (`/unslop`) |
| `control-ui` from `cursor-team-kit` | the repo's own UI driver (Playwright, CDP, Electron harness) |
| `control-cli` from `cursor-team-kit` | the repo's own CLI driver (a pty harness) |
| Cursor's built-in `create-skill` | the `skill-development` skill from Anthropic's `plugin-dev` plugin |
| Cursor's built-in `babysit` skill | no Claude Code equivalent, so the "do not route there" caveat is now generic |
| Cursor's `/loop` | Claude Code's `/loop`, which exists and behaves the same way |

## Known gaps

These are honest losses, not oversights.

1. **Model diversity is narrower.** pstack's adversarial workflows (`interrogate`, `reflect`, `arena`,
   `why`, `how`) get their signal from disagreement *across model families*. On Cursor that meant Grok
   vs GPT vs Claude. Here every reviewer is a Claude model, so `opus` / `fable` / `sonnet` / `haiku`
   disagree less than the original panel did. Agreement is correspondingly lower-signal. The workflows
   still run and still catch real problems, but calibrate expectations.
2. **`typescript-best-practices` no longer auto-attaches** on `.ts` / `.tsx` files. Invoke it explicitly.
3. **The `poteto-mode` reminder is gone.** Cursor re-injected "New task? Playbook match or rigor needed
   -> apply `/poteto-mode`" on each turn. Claude Code skills have no equivalent. Start rigorous tasks
   with `/poteto-mode` yourself, or put that line in your `CLAUDE.md`.
4. **`make-bot-ui` is Cursor-only.** It posts to `https://api2.cursor.sh/automations/webhook/<id>`,
   a Cursor Automations endpoint. Left intact and unported, since faking a Claude equivalent would be
   worse than leaving it truthful.
5. **`automations/benny` is unported.** It targets Cursor Automations (hosted cron plus webhooks).
   The skills under it are included verbatim for reference and will not run as automations here.
6. **`/setup-pstack` writes to a different place.** It now writes `~/.claude/pstack-models.md` instead
   of a Cursor `.mdc` rule. That file is not auto-loaded the way a Cursor rule was, so the skills read
   it by path.

## Reproducing the port

The substitution table and the strict runner live in `tools/port.py`. It is idempotent. Every rule
carries a required-fire assertion, so re-running against a newer upstream pstack will fail loudly on
any rule whose target text moved.
