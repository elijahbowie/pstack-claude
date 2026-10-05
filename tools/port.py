#!/usr/bin/env python3
"""Port cursor/plugins pstack -> Claude Code plugin. Strict: every rule must fire."""
import argparse, json, re, shutil, sys, tempfile
from pathlib import Path

# (id, kind, pattern, replacement, required)
RULES = [
  ('help.links', 'lit', 'https://github.com/cursor/plugins/blob/main/pstack/', 'https://github.com/elijahbowie/pstack-claude/blob/main/plugins/pstack/', True),
  ('install.chat', 'lit', 'In a Cursor chat, run:', 'In a Claude Code session, run:', True),
  ('install.confirm', 'lit', 'Cursor confirms the plugin is installed.', 'Claude Code confirms the plugin is installed.', True),
  ('help.install', 'lit', '1. Install with `/add-plugin pstack` in chat, or from Customize in the sidebar.\n2. Run [`/setup-pstack`](../setup-pstack/SKILL.md). It asks for a reasoning budget, maps a model to each role, and writes a rule. The rule applies to new chats.\n3. Start a real task with `/poteto-mode`, a goal, and a check that can pass or fail.', '1. Add the marketplace with `/plugin marketplace add elijahbowie/pstack-claude`, then install with `/plugin install pstack@pstack-claude`.\n2. Run [`/setup-pstack`](../setup-pstack/SKILL.md). It maps a model to each role and writes a configuration file read by the skills. Reasoning effort is controlled separately by Claude Code.\n3. Start a real task with `/poteto-mode`, a goal, and a check that can pass or fail.', True),
  ('install.command', 'lit', '/add-plugin pstack', '/plugin marketplace add elijahbowie/pstack-claude\n/plugin install pstack@pstack-claude', True),
  ('help.platform', 'lit', 'pstack is built for Cursor. Its skills use the Agent Skills format, so other tools can read them. But most workflow skills, including `/poteto-mode`, `/how`, `/why`, and `/teach`, spawn Cursor subagents with per-role models, and Custom Modes and `/loop` are Cursor features, so those parts may not work there.', 'This is the Claude Code port of pstack. Workflow skills spawn Claude Code subagents with per-role models. Cursor Custom Modes have no direct equivalent here; invoke `/poteto-mode` for each new task. Cursor Automations remain unported reference material. See [PORTING.md](https://github.com/elijahbowie/pstack-claude/blob/main/PORTING.md) for the limitations.', True),
  ('help.mode', 'lit', "- Enter on `/poteto-mode` attaches the skill to one message. It fades as the chat moves on.\n- Option+Enter on Mac or Alt+Enter on Windows, or Use as Mode from the skill entry, makes it a Custom Mode. It stays in context every turn until the user exits the mode, and it stays out of casual turns.\n- Cursor's docs list Custom Modes in the Agents Window and the CLI. Elsewhere, start each new task with `/poteto-mode`.", '- Start each new task with `/poteto-mode`. Claude Code has no Cursor Custom Mode or Option+Enter shortcut.\n- For a persistent project preference, add an instruction to the project’s `CLAUDE.md` to read and apply the installed pstack mode skill when a task needs rigor.', True),
  ('help.docs', 'lit', 'Link [Cursor\'s skills docs](https://cursor.com/docs/skills) when this comes up. Mid-chat, "new task" makes the mode match a fresh playbook. `/poteto-mode` already uses `poteto-agent` for the subagents its playbook steps spawn. To get the same style from a subagent of your own, spawn it with `subagent_type: "poteto-agent"`.', 'Link [Claude Code’s skills docs](https://code.claude.com/docs/en/skills) when this comes up. Plugin slash commands use the namespace `/pstack:<skill>`, for example `/pstack:poteto-mode`; standalone vendored skills use `/poteto-mode`. Mid-chat, "new task" makes the mode match a fresh playbook. For plugin subagents use `subagent_type: "pstack:poteto-agent"`; standalone agents use `"poteto-agent"`.', True),
  ('help.notshipped', 'lit', '- `/deslop`, `control-cli`, and `control-ui` ship in the `cursor-team-kit` plugin.\n- `/loop` and `/create-skill` are Cursor built-ins.\n- pstack has no `/orchestrate` skill. Orchestrate is a `/poteto-mode` playbook. If the slash menu shows `/orchestrate`, another plugin provides it.', '- `/unslop` is bundled in this port. Use the repo’s own UI or CLI harness instead of Cursor’s `control-cli` and `control-ui`.\n- `/loop` is a Claude Code built-in; skill authoring uses the `skill-development` skill from Anthropic’s `plugin-dev` plugin.\n- pstack has no `/orchestrate` skill. Orchestrate is a `/poteto-mode` playbook. If the slash menu shows `/orchestrate`, another plugin provides it.', True),
  ('help.babysit', 'lit', 'Without `/poteto-mode`, a phrase such as "babysit this pr" can start Cursor\'s own skill for the same job instead.', 'Invoke `/poteto-mode` explicitly to select its Babysit playbook.', True),
  ('help.plan', 'lit', "Cursor's Plan Mode works alongside it.", 'Claude Code’s plan mode works alongside it.', True),
  ('help.modefix', 'lit', 'It was started with Enter. Start it as a Custom Mode, or start each task with `/poteto-mode`.', 'Start each task with `/poteto-mode`, or add a project preference to `CLAUDE.md`.', True),
  ('help.configfix', 'lit', 'The rule from `/setup-pstack` applies to new chats. Start one.', 'Have the skill reread `~/.claude/pstack-models.md`; it is read explicitly, not auto-loaded.', True),
  ('help.parallel', 'lit', 'Give each agent its own worktree, or run them as cloud agents, which each get their own machine.', 'Give each writing agent its own worktree with `isolation: "worktree"`. These agents share the local machine.', True),
  ('help.custommention', 'lit', 'and mention once that a Custom Mode keeps it on.', 'and mention once that `/poteto-mode` should be invoked for each new task.', True),
  ('guide.mode', 'lit', 'From here you can type normal follow-ups. To keep `/poteto-mode` on for the whole chat, pick it from the `/` menu with Option+Enter (Mac) or Alt+Enter (Windows) instead of Enter. That makes it a [Custom Mode](https://cursor.com/docs/skills), which stays in context on every turn until you exit it. Custom Modes are available in the Agents Window and the CLI. Plain Enter attaches the skill to one message, and it fades as the chat moves on.', 'From here you can type normal follow-ups. Start each new task with `/poteto-mode`. Claude Code has no Cursor Custom Mode shortcut; for a persistent project preference, add an instruction in `CLAUDE.md` to read and apply the installed mode skill for rigorous tasks.', True),
  ('readme.mode', 'lit', 'to keep [`/poteto-mode`](./skills/poteto-mode/SKILL.md) on across turns, pick it from the `/` menu and press option+enter (mac) or alt+enter (windows) instead of enter. that makes it a [custom mode](https://cursor.com/docs/skills), which cursor offers in the agents window and the cli. it stays in context every turn, applies itself when a playbook matches or the task needs rigor, and stays out of the way otherwise. plain enter attaches it to one message only. say so to opt out, or exit the mode to turn it off.', 'start each new task with [`/poteto-mode`](./skills/poteto-mode/SKILL.md). Claude Code has no Cursor Custom Mode shortcut. For a persistent project preference, add an instruction in `CLAUDE.md` to read and apply this skill when the task needs rigor.', True),
  ('guide.modebrief', 'lit', 'a Custom Mode keeps `/poteto-mode` in context on every turn.', 'you invoke `/poteto-mode` for each new task.', True),
  ('readme.loop', 'lit', "cursor's `/loop` command. you can make cursor work", "Claude Code's `/loop` command. you can make Claude Code work", True),
  ('readme.models', 'lit', "that's it. the other skills are situational; the mode skill uses them for you as needed. out of the box the mode splits work by model strength: code delegates (feature, refactoring, bug fix, perf, hillclimb) go to grok, while the hardest changes, prose, and judgment go to opus 5.5. the default panel is opus 5.5 / sol / grok. [`/setup-pstack`](./skills/setup-pstack/SKILL.md) changes any of it.", "that's it. the other skills are situational; the mode skill uses them for you as needed. In this port, code delegates use `sonnet`; the hardest changes, prose, and judgment use `opus`. Default review panels retain three seats (`opus`, `opus`, `sonnet`) but have less model-family diversity than upstream. [`/setup-pstack`](./skills/setup-pstack/SKILL.md) changes the choices.", True),
  ('readme.deps', 'lit', '- `/deslop` and the `deslop` skill ship in the `cursor-team-kit` plugin.\n- `control-cli` (for CLIs and TUIs) and `control-ui` (for browser, Electron, web) ship in `cursor-team-kit` too.\n- `/create-skill` is a cursor built-in. cursor also ships a built-in `/babysit`; inside `poteto-mode`, the [babysit playbook](./skills/poteto-mode/playbooks/babysit.md) supersedes it for pr-status requests.', '- `/unslop` is bundled in this port.\n- Use the repo’s own UI or CLI harness in place of Cursor’s `control-cli` and `control-ui`.\n- Skill authoring uses `skill-development` from Anthropic’s `plugin-dev` plugin. Inside `poteto-mode`, the [babysit playbook](./skills/poteto-mode/playbooks/babysit.md) handles PR-status requests.', True),
  ('readme.depsinstall', 'lit', 'install `cursor-team-kit` alongside pstack if you want the full set.', 'Install Anthropic’s `plugin-dev` plugin if you need its skill-authoring workflow.', True),
  ('readme.plan', 'lit', 'cursor already has a great plan mode which works great with pstack.', 'Claude Code’s plan mode works alongside pstack.', True),
  ('config.description', 'lit', 'writes an always-applied rule that overrides the skill defaults.', 'writes a configuration file read explicitly by the skills. Reasoning effort is controlled separately in Claude Code.', True),
  ('config.intro', 'lit', "an always-applied rule that sets pstack's model per role.", 'a configuration file read explicitly by pstack skills to set each role’s model.', True),
  ('config.budget', 'lit', '**(a) Ask for a budget.** Prefer AskQuestion over free text. Offer these four options with these exact labels, and name the current budget when the rule records one.', '**(a) Ask for a model budget.** Prefer AskQuestion over free text. Offer `unlimited — strongest available models`, `large — opus and sonnet`, `medium — mostly sonnet`, or `small — sonnet and haiku`. Name the current budget when the file records one. These labels select model cost, not reasoning effort; configure effort separately in Claude Code and never invent effort-suffixed model aliases.', True),
  ('config.budgetlabels', 'lit', '- `unlimited — keep max`\n- `large — xhigh reasoning`\n- `medium — high reasoning`\n- `small — medium reasoning`', 'Use only the detected model aliases when applying that budget.', True),
  ('config.apply', 'lit', "**(b) Apply it.** Build the working table from the skill defaults, and on a re-run keep any role you changed by family, list, or alias (`inherit-parent`, `auto`). `unlimited` leaves every effort as in that table. `large`, `medium`, and `small` set the effort token of every real slug, panel entries included, to `xhigh`, `high`, or `medium`. The effort token is the last token, or the one before a trailing `fast`, on the ladder `max` > `xhigh` > `high` > `medium` > `low`. If the result is not a detected slug, use the same family's detected slug with the highest effort at or below the target, else mark the role as needing a choice. `inherit-parent` and `auto` do not change. So `small` turns `claude-opus-5-5-max` into `claude-opus-5-5-medium`, and `grok-4.7-xhigh-fast` into `grok-4.7-medium-fast`.", '**(b) Apply it.** Start from the skill defaults and preserve explicit role choices on a rerun, including panel lists and `inherit-parent` / `auto`. For unconfigured roles, `unlimited` and `large` keep the defaults; `medium` uses `sonnet` for code and review roles; `small` uses `haiku` for mechanical code work and `sonnet` for harder work and judgment. Only use aliases confirmed available. Do not append reasoning suffixes to aliases or claim that the budget controls effort. Keep the panel’s seat count unless the user changes it.', True),
  ('config.write', 'lit', 'with `alwaysApply: true`, a `# budget` line with the chosen label and its target effort,', 'with a `# budget` line containing the chosen model-cost label,', True),
  ('config.yaml', 'lit', '---\ndescription: pstack per-role model choices (overrides skill defaults)\nalwaysApply: true\n---\n# pstack model configuration.', '# pstack per-role model choices (overrides skill defaults).', True),
  ('config.budgetline', 'lit', '# budget: unlimited (max)', '# budget: unlimited', True),
  ('config.confirm', 'lit', 'Tell the user the rule was written and that it applies to new sessions.', 'Tell the user the configuration was written and is read explicitly by the skills. It is not an auto-loaded Claude rule.', True),
  ('guide.config', 'lit', 'After setup, start a new chat. The model rule applies to new sessions.', 'After setup, skills read `~/.claude/pstack-models.md` explicitly. A new session is not required to load a Claude rule.', True),
  ('config.readme', 'lit', 'writes a small always-applied rule mapping each role', 'writes a configuration file read explicitly by the skills, mapping each role', True),
  ('guide.deslop', 'lit', "The [Opening a PR playbook](../../skills/poteto-mode/playbooks/opening-a-pr.md) runs `/deslop` on the diff before each commit and applies [`/unslop`](../../skills/unslop/SKILL.md) to the PR description and commit bodies. `/deslop` ships in the `cursor-team-kit` plugin, not in pstack. If you don't have it, ask for the same outcome in plain words: remove narrating comments, unsupported guards, dead compatibility paths, and unrelated edits.", 'The [Opening a PR playbook](../../skills/poteto-mode/playbooks/opening-a-pr.md) runs the bundled [`/unslop`](../../skills/unslop/SKILL.md) before each commit and on the PR description and commit bodies. Use the repo’s own checks to remove unsupported guards, dead compatibility paths, and unrelated edits.', True),
  ('guide.loop', 'lit', "`/loop` is Cursor's built-in wake mechanism", "`/loop` is Claude Code's built-in wake mechanism", True),
  ('swarm.cloud', 'lit', 'Fan out N parallel cloud workers.', 'Fan out N parallel workers in isolated local worktrees.', True),
  ('swarm.concurrency', 'lit', 'not the cloud concurrency limit.', 'not the local concurrency limit.', True),
  ('swarm.local', 'lit', 'Use `environment: "local"` only when the worker needs access to something on the user\'s computer.', 'Omit worktree isolation only for read-only work or when the worker must use the current checkout. All workers share the local machine.', True),
  ('swarm.branch', 'lit', 'When a worker must start from a non-default pushed branch, pass `cloud_base_branch`.', 'When a worker must start from a non-default branch, create a worktree from that branch before spawning, omit automatic `isolation`, and pass its path in the brief. Require the worker to run every command in that directory and verify its HEAD matches the requested SHA before working. Do not pass `cloud_base_branch`; it is not a Claude Code parameter.', True),
  ('orchestrate.nesting', 'lit', 'nesting works to depth 3, and a nested spawn has the full Task schema including `environment`', 'nesting is subject to the session’s configured depth limit, and a nested spawn uses the Agent schema including `isolation`; if spawning is unavailable, the leaf agent executes its scope directly', True),

  ("autopilot.installed", "lit", '`git show origin/main:pstack/skills/poteto-mode/playbooks/autopilot-full.md`', 'the installed `autopilot-full.md` playbook by its resolved file path (the host app repository may not contain pstack)', True),
  # ---- external plugin deps (must run before generic token rules) ----
  ("dep.deslop.skill", "lit", "the `deslop` skill from the `cursor-team-kit` plugin (`/deslop`)", "the **unslop** skill (`/unslop`)", True),
  ("dep.deslop.run", "lit", "Run `/deslop` from `cursor-team-kit` over the diff before commit.", "Run `/unslop` over the diff before commit.", True),
  ("dep.control.publishes", "lit", "`cursor-team-kit` publishes `control-cli` (CLIs and TUIs) and `control-ui` (browser / Electron / web UIs).",
   "This port ships no control skills, so drive the surface with the repo's own harness: a pty harness for CLIs and TUIs, Playwright or CDP for browser / Electron / web UIs.", True),
  ("dep.control.ui_or_cli", "lit", "`control-ui` or `control-cli` from `cursor-team-kit`", "the repo's own UI or CLI driver", True),
  ("dep.control.cli_or_ui", "lit", "`control-cli` or `control-ui` from `cursor-team-kit`", "the repo's own CLI or UI driver", True),
  ("dep.control.ui", "lit", "`control-ui` from `cursor-team-kit`", "the repo's own UI driver", True),
  ("dep.control.cli", "lit", "`control-cli` from `cursor-team-kit`", "the repo's own CLI driver", True),
  ("dep.control.paren", "lit", "(from `cursor-team-kit`)", "(the repo's own drivers)", True),
  # ---- create-skill -> Claude Code skill authoring ----
  ("dep.createskill.a", "lit", "Cursor's built-in `create-skill` skill", "the `skill-development` skill from Anthropic's `plugin-dev` plugin", True),
  ("dep.createskill.b", "lit", "Cursor's built-in `create-skill`", "the `skill-development` skill from Anthropic's `plugin-dev` plugin", True),
  ("dep.createskill.c", "lit", "(Cursor's built-in for authoring SKILL.md files)", "(Anthropic's `plugin-dev` plugin, for authoring SKILL.md files)", True),
  ("dep.createskill.tok", "re", r"create-skill", "skill-development", True),
  # ---- tools ----
  ("tool.askq", "re", r"\bAskQuestion\b", "AskUserQuestion", True),
  ("tool.task.tool", "lit", "Task tool", "Agent tool", True),
  ("tool.task.calls", "lit", "`Task` calls", "`Agent` calls", True),
  ("tool.task.call", "lit", "`Task` call", "`Agent` call", True),
  ("tool.task.prompts", "lit", "`Task` prompts", "`Agent` prompts", True),
  ("tool.task.response", "lit", "`Task` response", "`Agent` response", True),
  ("tool.task.model", "lit", "omit Task `model`", "omit Agent `model`", True),
  ("tool.task.spawn", "lit", "Spawn `Task` with", "Spawn an `Agent` with", True),
  ("tool.subagent.gp1", "lit", "`subagent_type: generalPurpose`", "`subagent_type: general-purpose`", True),
  ("tool.subagent.gp2", "lit", "`generalPurpose`", "`general-purpose`", True),
  ("tool.subagent.sicko", "lit", '`subagent_type: "Comment Sicko"`', '`subagent_type: "comment-sicko"`', True),
  ("tool.env.cloud", "lit", '`environment: "cloud"`', '`isolation: "worktree"`', True),
  ("tool.readonly.a", "lit", "agent mode (readonly strips MCP)", "full tool access (the read-only `Explore` agent strips MCP)", True),
  ("tool.readonly.b", "lit", "agent mode (`readonly: false`)", "a full-tool agent, not the read-only `Explore` agent", True),
  ("tool.readonly.c", "lit", "Readonly strips MCPs.", "The read-only `Explore` agent strips MCPs.", True),
  # ---- models: Cursor slugs -> Claude Code Agent model values ----
  ("model.grok.fast", "lit", "grok-4.7-xhigh-fast", "sonnet", True),
  ("model.opus", "lit", "claude-opus-5-5-max", "opus", True),
  ("model.sol", "lit", "gpt-5.6-sol-max", "opus", True),
  # ---- config + paths ----
  ("path.models.rule", "lit", "~/.cursor/rules/pstack-models.mdc", "~/.claude/pstack-models.md", True),
  ("path.skills.home", "lit", "~/.cursor/skills/", "~/.claude/skills/", True),
  ("path.skills.proj", "lit", ".cursor/skills/", ".claude/skills/", True),
  ("path.plugins", "lit", "~/.cursor/plugins/", "~/.claude/plugins/", True),
  ("path.projects.home", "lit", "~/.cursor/projects/", "~/.claude/projects/", True),
  # ---- product naming ----
  ("brand.cloudagent", "lit", "Cursor cloud agent", "Claude Code agent in its own worktree", True),
  ("brand.loop", "lit", "Cursor's `/loop` command", "Claude Code's `/loop` command", True),
  ("brand.restart", "lit", "a Cursor restart", "a Claude Code restart", True),
  ("brand.modelsapi", "lit", "If Cursor also exposes a models API", "If Claude Code also exposes a models API", True),
  ("brand.mcpenv", "lit", "the Cursor environment", "the Claude Code environment", True),
  ("brand.babysit.a", "lit", "and not Cursor's built-in babysit skill", "and not any built-in babysit skill", True),
  ("brand.babysit.b", "lit", "This playbook replaces Cursor's built-in babysit skill", "This playbook replaces any built-in babysit skill", True),
  ("dep.deslop.bare", "lit", "`/deslop`", "`/unslop`", True),
  ("dep.control.orch", "lit", "`control-ui` or `control-cli` runtime verification (the repo's own drivers)", "UI or CLI runtime verification through the repo's own drivers", True),
  ("brand.mcpdir", "lit", "Otherwise inspect the `mcps/` directory Cursor exposes for enabled MCP servers.", "Otherwise inspect the MCP servers Claude Code has configured for this session.", True),
  ("brand.dashboard", "lit", "the Cursor dashboard", "the available local Agent status tools", True),
  ("path.worktrees", "lit", "`.cursor/worktrees/", "`.claude/worktrees/", True),
  ('tool.task.remaining', 'lit', '`Task`', '`Agent`', True),
  ('tool.task.subagent', 'lit', 'Task subagent', 'Agent subagent', True),
  ('path.models.basename', 'lit', 'pstack-models.mdc', 'pstack-models.md', True),
]

DROP_FM_KEYS = {"mode", "icon", "color", "reminder", "paths"}
RENAME = {"Poteto Mode": "poteto-mode", "Make Bot UI": "make-bot-ui", "Comment Sicko": "comment-sicko"}

counts = {r[0]: 0 for r in RULES}
fm_dropped, fm_renamed = [], []

def port_body(text):
    for rid, kind, pat, rep, _req in RULES:
        if kind == "lit":
            n = text.count(pat)
            if n:
                text = text.replace(pat, rep); counts[rid] += n
        else:
            text, n = re.subn(pat, rep, text)
            counts[rid] += n
    return text

def port_md(path, rel):
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end < 0:
            raise ValueError(f"{rel}: unterminated frontmatter")
        fm, body = raw[4:end+1], raw[end+5:]
        out = []
        for line in fm.split("\n"):
            key = line.split(":", 1)[0].strip() if ":" in line else None
            if key == "is_background":
                line = line.replace("is_background:", "background:", 1)
            if key in DROP_FM_KEYS:
                fm_dropped.append(f"{rel}: {line.strip()}"); continue
            if key == "name":
                v = line.split(":", 1)[1].strip()
                if v in RENAME:
                    fm_renamed.append(f"{rel}: {v} -> {RENAME[v]}")
                    line = f"name: {RENAME[v]}"
            out.append(line)
        raw = "---\n" + "\n".join(out) + "---\n" + body
    raw = port_body(raw)
    raw = raw.replace("a `Agent` subagent", "an `Agent` subagent")
    if rel == "skills/poteto-mode/playbooks/orchestrate.md":
        raw = """**Claude Code port limitation.** This playbook describes Cursor’s durable cloud orchestration. Claude Code Agent worktrees share this machine, have no Cursor cloud dashboard, and do not survive a restart as hosted workers. Treat references to cloud restacks, cloud concurrency, and durable cloud recovery below as upstream reference only. Use the Autonomous run playbook with flat local workers unless an external orchestration harness supplies those capabilities. Never claim local worktrees are hosted cloud agents.

""" + raw
    if rel == "skills/poteto-mode/playbooks/worktree-cleanup.md":
        raw = """**Claude Code port limitation.** The audit scans local Claude transcripts, but cannot infer whether a chat is pinned or still active. Missing transcripts are not proof that a worktree is unused. Cross-check every candidate against the user’s active and pinned chats before removing it. Cursor-specific application caches below are upstream reference only; do not reinterpret them as Claude caches.

""" + raw
    return raw

def generate(src, dest_repo):
    dest = dest_repo / "plugins" / "pstack"
    dest.mkdir(parents=True)
    for item in sorted(src.iterdir()):
        if item.name in {".cursor-plugin", ".gitignore"}:
            continue
        target = dest / item.name
        shutil.copytree(item, target) if item.is_dir() else shutil.copy2(item, target)

    for md in sorted(dest.rglob("*.md")):
        rel = md.relative_to(dest).as_posix()
        # Cursor Automations are included as reference, without platform substitutions.
        if rel.startswith("automations/"):
            continue
        md.write_text(port_md(md, rel), encoding="utf-8")

    # The audit searches the whole Claude store because session/subagent logs
    # live below per-project directories, rather than Cursor's agent-transcripts.
    audit = dest / "skills" / "poteto-mode" / "scripts" / "worktree-audit.sh"
    if audit.exists():
        text = audit.read_text()
        old = '# Transcripts dir: ~/.cursor/projects/<slugified-repo-path>/agent-transcripts.\nslug=$(printf \'%s\' "$main_wt" | sed \'s#^/##; s#/#-#g\')\ntranscripts="$HOME/.cursor/projects/$slug/agent-transcripts"'
        if old not in text:
            raise ValueError("worktree-audit.sh: transcript layout changed upstream")
        audit.write_text(text.replace(old, '# Claude session and subagent transcripts live below per-project directories.\ntranscripts="$HOME/.claude/projects"'))

    # Plugin commands/agents are scoped; vendor-into-repo.sh removes this scope.
    skills = [p.name for p in (dest / "skills").iterdir() if p.is_dir()]
    command_pattern = r"(?<![\w./:-])/(" + "|".join(map(re.escape, skills)) + r")(?=[$\s`\[<(.,:;!?\"’')]|$)"
    for md in dest.rglob("*.md"):
        if md.relative_to(dest).parts[0] == "automations":
            continue
        text = md.read_text()
        text = re.sub(command_pattern, r"/pstack:\1", text)
        text = text.replace("reasoning budget", "model budget")
        text = text.replace("as cloud agents", "in isolated local worktrees")
        text = text.replace("but it's not a default. \n", "but it's not a default.\n")
        text = text.replace('subagent_type: "poteto-agent"', 'subagent_type: "pstack:poteto-agent"')
        text = text.replace('subagent_type: "comment-sicko"', 'subagent_type: "pstack:comment-sicko"')
        text = text.replace('standalone vendored skills use `/pstack:poteto-mode`', 'standalone vendored skills use the unprefixed skill name')
        md.write_text(text)

    upstream = json.loads((src / ".cursor-plugin" / "plugin.json").read_text())
    plugin = {key: upstream[key] for key in (
        "name", "description", "version", "author", "homepage", "repository", "license", "keywords"
    )}
    manifest_dir = dest / ".claude-plugin"
    manifest_dir.mkdir()
    (manifest_dir / "plugin.json").write_text(json.dumps(plugin, indent=2) + "\n")
    marketplace = {
        "name": "pstack-claude",
        "owner": {"name": "Lauren Tan (poteto)", "url": upstream["homepage"]},
        "metadata": {
            "description": "Claude Code port of pstack, poteto's rigorous agent-workflow plugin for Cursor",
            "version": upstream["version"],
        },
        "plugins": [{
            "name": "pstack", "source": "./plugins/pstack",
            "description": plugin["description"], "version": plugin["version"],
            "category": "developer-tools", "keywords": plugin["keywords"],
        }],
    }
    (dest_repo / ".claude-plugin").mkdir()
    (dest_repo / ".claude-plugin" / "marketplace.json").write_text(json.dumps(marketplace, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="upstream pstack directory")
    parser.add_argument("--dest-repo", type=Path, default=Path(__file__).resolve().parents[1],
                        help="destination repository (defaults to this repository)")
    args = parser.parse_args()
    src, dest_repo = args.source.resolve(), args.dest_repo.resolve()
    if not (src / ".cursor-plugin" / "plugin.json").is_file():
        parser.error(f"not an upstream pstack directory: {src}")
    dest = dest_repo / "plugins" / "pstack"
    if src == dest or src in dest.parents or dest in src.parents:
        parser.error("source and destination plugin directories must not overlap")

    counts.clear()
    counts.update({rule[0]: 0 for rule in RULES})
    fm_dropped.clear()
    fm_renamed.clear()

    # Validate the whole generated tree before touching the existing port.
    with tempfile.TemporaryDirectory(prefix="pstack-port-") as directory:
        staged_repo = Path(directory)
        generate(src, staged_repo)
        missing = [rid for rid, _, _, _, required in RULES if required and counts[rid] == 0]
        print("Rule matches:")
        for rid, _, _, _, _ in RULES:
            print(f"  {counts[rid]:>4}  {rid}")
        if missing:
            print("FAILED, rules that never fired: " + ", ".join(missing), file=sys.stderr)
            return 1
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(staged_repo / "plugins" / "pstack", dest)
        (dest_repo / ".claude-plugin").mkdir(parents=True, exist_ok=True)
        shutil.copy2(staged_repo / ".claude-plugin" / "marketplace.json",
                     dest_repo / ".claude-plugin" / "marketplace.json")
    print(f"OK: {len(fm_dropped)} frontmatter keys dropped, {len(fm_renamed)} names renamed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
