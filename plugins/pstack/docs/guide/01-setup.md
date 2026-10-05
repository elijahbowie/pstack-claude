# Set up pstack

In this page you install the plugin, pick which models pstack uses, and run your first task. Setup is one command plus a short conversation.

## Install the plugin

In a Claude Code session, run:

```text
/plugin marketplace add elijahbowie/pstack-claude
/plugin install pstack@pstack-claude
```

Claude Code confirms the plugin is installed.

## Pick your models

Run:

```text
/pstack:setup-pstack
```

[`/pstack:setup-pstack`](../../skills/setup-pstack/SKILL.md) detects the models you have access to, asks for a model budget, shows you each role (code delegates, judgment, the review panels), and asks what you want. Answer the questions. It writes `~/.claude/pstack-models.md`, a small rule every pstack skill reads.

You only override what you care about. A role with no line in the rule keeps the skill's default. To restore a default, delete that role's line. A rerun of `/pstack:setup-pstack` keeps any role whose model differs from the default. A rule written before 0.15.3 pins the old default models, so delete those role lines, or delete the file, then run `/pstack:setup-pstack` again.

You might be wondering what happens if you use Auto. Set a role to `inherit-parent` or `auto` and pstack omits the subagent `model` field, so the subagent inherits your parent chat model. Both values mean the same thing, and neither is a model slug. For a panel role the value is a list, and one subagent runs per entry, so the list length sets the panel size. Setup also configures `swarm workers`, the default model for every `/pstack:swarm` worker unless a race names a model for each arm.

## Accept the verification offer, or don't

At the end of setup, `/pstack:setup-pstack` looks for a way to prove app behavior in your project, either a `verify-*` skill or an existing harness. If it finds neither, it offers once to generate one with [`/pstack:create-verification-skill`](../../skills/create-verification-skill/SKILL.md).

Say yes and it writes `.claude/skills/verify-<app>/`, a project-local skill that teaches agents to drive your app the way a user does. It proves the skill works once before handing it over. Say no and setup moves on. You can run `/pstack:create-verification-skill` yourself any time. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers when it earns its place.

After setup, skills read `~/.claude/pstack-models.md` explicitly. A new session is not required to load a Claude rule.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
/pstack:poteto-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt. If `/pstack:poteto-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.

From here you can type normal follow-ups. Start each new task with `/pstack:poteto-mode`. Claude Code has no Cursor Custom Mode shortcut; for a persistent project preference, add an instruction in `CLAUDE.md` to read and apply the installed mode skill for rigorous tasks.

Next: [Route work through `/pstack:poteto-mode`](./02-poteto-mode.md).
