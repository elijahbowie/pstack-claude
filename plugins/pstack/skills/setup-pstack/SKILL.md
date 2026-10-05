---
name: setup-pstack
description: Configure which models pstack uses per role and at what model budget. Detects your available models and writes a configuration file read explicitly by the skills. Reasoning effort is controlled separately in Claude Code. Use for /pstack:setup-pstack, "configure pstack models", "pstack budget", or changing pstack's model choices.
---

# Setup pstack

Write `~/.claude/pstack-models.md`, a configuration file read explicitly by pstack skills to set each role’s model.

## Steps

### 1. Detect available models

Enumerate the model slugs you can pass to an `Agent` subagent in this session. That is the dependable source. If Claude Code also exposes a models API or CLI that lists the user's entitled models, prefer it for completeness. If you cannot detect any, ask the user to paste the slugs they have access to. Never write a real slug you have not confirmed is available. The aliases `inherit-parent` and `auto` are always valid even though they are not detected slugs.

### 2. Load current state

The default role-to-model mapping is the rule shape shown in step 5 below. If `~/.claude/pstack-models.md` already exists, read it and treat its `# budget` line and its role values as the current choices. Otherwise start from those defaults. A line whose role is not in step 5, such as `how critics`, is from a retired role. Drop it.

### 3. Budget, map, and confirm

**(a) Ask for a model budget.** Prefer AskUserQuestion over free text. Offer `unlimited — strongest available models`, `large — opus and sonnet`, `medium — mostly sonnet`, or `small — sonnet and haiku`. Name the current budget when the file records one. These labels select model cost, not reasoning effort; configure effort separately in Claude Code and never invent effort-suffixed model aliases.

Use only the detected model aliases when applying that budget.

**(b) Apply it.** Start from the skill defaults and preserve explicit role choices on a rerun, including panel lists and `inherit-parent` / `auto`. For unconfigured roles, `unlimited` and `large` keep the defaults; `medium` uses `sonnet` for code and review roles; `small` uses `haiku` for mechanical code work and `sonnet` for harder work and judgment. Only use aliases confirmed available. Do not append reasoning suffixes to aliases or claim that the budget controls effort. Keep the panel’s seat count unless the user changes it.

**(c) Show the roles and confirm.** Show every role with its model, marking any real slug not in the detected set as needing a choice. Also list each line step 2 dropped. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` (both mean: this role runs on the parent chat model, which is how Auto users stay on Auto) as the options. Prefer AskUserQuestion over free text. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one value from it whose model family differs from the parent's when possible. `swarm workers` is the default model for every worker unless a race or comparison assigns another model per arm.

### 4. Validate

Every real slug written must be in the detected set. `inherit-parent` and `auto` always pass. If a chosen real slug is not available, stop and ask again.

### 5. Write the rule

Write `~/.claude/pstack-models.md` with a `# budget` line containing the chosen model-cost label, and one line per role, using the same labels poteto-mode uses. Overwrite the whole file so re-runs stay idempotent. Shape:

```
# pstack per-role model choices (overrides skill defaults). One line per role. Delete a line to fall back to the skill default.
# `inherit-parent` or `auto` as a value: the role runs on the parent chat model (omit Agent `model`). Alias entries in a panel list still count toward its fan-out.
# budget: unlimited
feature, refactoring: sonnet
bug-fix: sonnet
perf-issue: sonnet
hillclimb: sonnet
judgment and prose: opus
hardest tasks: opus
how explorer: sonnet
how explainer: opus
why investigators: sonnet
why synthesizer: opus
reflect tooling: opus
reflect judgment, divergent, synthesizer: opus
arena runners: opus, opus, sonnet
arena cross-judge pool: opus, opus, sonnet
swarm workers: sonnet
architect runners: opus, opus, sonnet
interrogate reviewers: opus, opus, sonnet
```

### 6. Confirm

Tell the user the configuration was written and is read explicitly by the skills. It is not an auto-loaded Claude rule. Re-running this skill updates it.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /pstack:create-verification-skill." On yes, invoke `/pstack:create-verification-skill` (resolves wherever pstack is installed: workspace, user, or plugin). On no, move on without pushing.
