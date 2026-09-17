#!/usr/bin/env python3
"""Port cursor/plugins pstack -> Claude Code plugin. Strict: every rule must fire."""
import json, re, shutil, sys
from pathlib import Path

SRC = Path("/private/tmp/claude-501/-Users-elijahbowie/9c9d18d7-f1cb-4194-bccb-08290225303a/scratchpad/plugins/pstack")
DEST_REPO = Path("/Users/elijahbowie/pstack-claude")
DEST = DEST_REPO / "plugins" / "pstack"

# (id, kind, pattern, replacement, required)
RULES = [
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
  ("tool.bg", "lit", "`run_in_background: true`", "background execution (the default for `Agent`)", True),
  ("style.bgcap", "lit", "**Defaults for every `Agent` call.** background execution", "**Defaults for every `Agent` call.** Background execution", True),
  ("tool.env.cloud", "lit", '`environment: "cloud"`', '`isolation: "remote"`', True),
  ("tool.env.local", "lit", '`environment: "local"`', "the default local isolation", True),
  ("tool.readonly.a", "lit", "agent mode (readonly strips MCP)", "full tool access (the read-only `Explore` agent strips MCP)", True),
  ("tool.readonly.b", "lit", "agent mode (`readonly: false`)", "a full-tool agent, not the read-only `Explore` agent", True),
  ("tool.readonly.c", "lit", "Readonly strips MCPs.", "The read-only `Explore` agent strips MCPs.", True),
  # ---- models: Cursor slugs -> Claude Code Agent model values ----
  ("model.grok.fast", "lit", "grok-4.6-fast-xhigh", "sonnet", True),
  ("model.grok.med", "lit", "grok-4.6-medium-fast", "haiku", True),
  ("model.fable.max", "lit", "claude-fable-5-1-thinking-max", "fable", True),
  ("model.fable.med", "lit", "claude-fable-5-1-thinking-medium", "fable", True),
  ("model.sol", "lit", "gpt-5.6-sol-max", "opus", True),
  ("model.opus", "lit", "claude-opus-5-thinking-xhigh", "opus", True),
  # ---- config + paths ----
  ("path.models.rule", "lit", "~/.cursor/rules/pstack-models.mdc", "~/.claude/pstack-models.md", True),
  ("path.skills.home", "lit", "~/.cursor/skills/", "~/.claude/skills/", True),
  ("path.skills.proj", "lit", ".cursor/skills/", ".claude/skills/", True),
  ("path.plugins", "lit", "~/.cursor/plugins/", "~/.claude/plugins/", True),
  ("path.projects.home", "lit", "~/.cursor/projects/", "~/.claude/projects/", True),
  # ---- product naming ----
  ("brand.cloudagent", "lit", "Cursor cloud agent", "Claude Code cloud agent (`isolation: \"remote\"`)", True),
  ("brand.loop", "lit", "Cursor's `/loop` command", "Claude Code's `/loop` command", True),
  ("brand.restart", "lit", "a Cursor restart", "a Claude Code restart", True),
  ("brand.modelsapi", "lit", "If Cursor also exposes a models API", "If Claude Code also exposes a models API", True),
  ("brand.mcpenv", "lit", "the Cursor environment", "the Claude Code environment", True),
  ("brand.babysit.a", "lit", "and not Cursor's built-in babysit skill", "and not any built-in babysit skill", True),
  ("brand.babysit.b", "lit", "This playbook replaces Cursor's built-in babysit skill", "This playbook replaces any built-in babysit skill", True),
  ("brand.appsupport", "lit", "~/Library/Application Support/Cursor", "~/Library/Application Support/Claude", True),
  ("dep.deslop.bare", "lit", "`/deslop`", "`/unslop`", True),
  ("dep.control.orch", "lit", "`control-ui` or `control-cli` runtime verification (the repo's own drivers)", "UI or CLI runtime verification through the repo's own drivers", True),
  ("brand.mcpdir", "lit", "Otherwise inspect the `mcps/` directory Cursor exposes for enabled MCP servers.", "Otherwise inspect the MCP servers Claude Code has configured for this session.", True),
  ("brand.dashboard", "lit", "the Cursor dashboard", "the Claude Code cloud dashboard", True),
  ("path.worktrees", "lit", "`.cursor/worktrees/", "`.claude/worktrees/", True),
]

DROP_FM_KEYS = {"mode", "icon", "color", "reminder", "is_background", "paths"}
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
        fm, body = raw[4:end+1], raw[end+5:]
        out = []
        for line in fm.split("\n"):
            key = line.split(":", 1)[0].strip() if ":" in line else None
            if key in DROP_FM_KEYS:
                fm_dropped.append(f"{rel}: {line.strip()}"); continue
            if key == "name":
                v = line.split(":", 1)[1].strip()
                if v in RENAME:
                    fm_renamed.append(f"{rel}: {v} -> {RENAME[v]}")
                    line = f"name: {RENAME[v]}"
            out.append(line)
        raw = "---\n" + "\n".join(out) + "---\n" + body
    return port_body(raw)

if DEST.exists():
    shutil.rmtree(DEST)
DEST.mkdir(parents=True)

SKIP = {".cursor-plugin", ".gitignore"}
for item in sorted(SRC.iterdir()):
    if item.name in SKIP:
        continue
    tgt = DEST / item.name
    shutil.copytree(item, tgt) if item.is_dir() else shutil.copy2(item, tgt)

for md in sorted(DEST.rglob("*.md")):
    rel = md.relative_to(DEST).as_posix()
    md.write_text(port_md(md, rel), encoding="utf-8")

PLUGIN_DESC = ("if you want to go fast, go deep first. pstack helps you write less, but higher "
               "quality code. rigorous agent workflows you can parallelize with confidence.")
KEYWORDS = ["pstack", "poteto-mode", "workflow", "principles", "agent-style", "subagents", "unslop"]
UPSTREAM = json.loads((SRC / ".cursor-plugin" / "plugin.json").read_text())
VERSION = UPSTREAM["version"]

(DEST / ".claude-plugin").mkdir(parents=True, exist_ok=True)
(DEST / ".claude-plugin" / "plugin.json").write_text(json.dumps({
    "name": "pstack",
    "description": PLUGIN_DESC,
    "version": VERSION,
    "author": UPSTREAM["author"],
    "homepage": UPSTREAM["homepage"],
    "repository": UPSTREAM["repository"],
    "license": UPSTREAM["license"],
    "keywords": KEYWORDS,
}, indent=2) + "\n", encoding="utf-8")

(DEST_REPO / ".claude-plugin").mkdir(parents=True, exist_ok=True)
(DEST_REPO / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
    "name": "pstack-claude",
    "owner": {"name": "Lauren Tan (poteto)", "url": UPSTREAM["homepage"]},
    "metadata": {
        "description": "Claude Code port of pstack, poteto's rigorous agent-workflow plugin for Cursor",
        "version": VERSION,
    },
    "plugins": [{
        "name": "pstack",
        "source": "./plugins/pstack",
        "description": PLUGIN_DESC,
        "version": VERSION,
        "category": "developer-tools",
        "keywords": KEYWORDS,
    }],
}, indent=2) + "\n", encoding="utf-8")

missing = [rid for rid, k, p, r, req in RULES if req and counts[rid] == 0]
print("=== rule fire counts ===")
for rid, k, p, r, req in RULES:
    flag = "  MISS" if counts[rid] == 0 and req else ""
    print(f"  {counts[rid]:>4}  {rid}{flag}")
print(f"\n=== frontmatter keys dropped ({len(fm_dropped)}) ===")
for l in fm_dropped: print("  " + l)
print(f"\n=== names kebab-cased ({len(fm_renamed)}) ===")
for l in fm_renamed: print("  " + l)
if missing:
    print("\nFAILED, rules that never fired: " + ", ".join(missing)); sys.exit(1)
print("\nOK")
