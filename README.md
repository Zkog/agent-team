# agent-team

A Claude Code skill that runs a multi-model agent team on a GitHub repo:
Product Owner and Architect on Fable 5.1, Coder on Opus 5, Reviewer on Codex (GPT), UX on GPT-5.6 sol drawing the icons.
The team lives **in the project** as a pinned git submodule. One clone per role, one terminal per clone, all communication through git. Status is derived, never written. The human merges.

See [SKILL.md](SKILL.md) for the design and [team/TEAM.md](team/TEAM.md) for the rulebook the agents get.

## New project

One command, from nothing to a running workspace:

```bash
curl -sL https://raw.githubusercontent.com/Zkog/agent-team/main/new-project.sh | bash -s -- myproj
```

It creates the GitHub repo if needed (private by default, `--public` to change), makes `./myproj-team/`, clones `po/`, pins the newest tagged team version as a submodule, scaffolds, pushes, clones `architect/`, `coder/`, `reviewer/`, `ux/`, writes `./team` — and opens every role in its own window: tiled Terminal windows on macOS, a tiled tmux session elsewhere (`--no-open` to skip). From a clone of this repo, `./new-project.sh myproj` does the same.

```
cd myproj-team
./team open        # (again) PO top-left, then Architect, Coder, Reviewer, UX; --tmux for tmux anywhere
                   # every role starts working on launch; the four workers wait on the board and wake up when it's their turn
./team board       # the board, refreshed every 30 s — park it in a corner
./team po          # or start any single role by hand — PO is the one you talk to; ask it to fill in Project conventions first
./team status      # the board, once
./team log         # who did what
./team add coder   # more throughput: coder-2/, started with ./team coder 2
./team ux          # the icon agent alone — it draws what .team/icons/ asks for
```

`./team` is a three-line shim; the launcher itself lives in the submodule, so it upgrades with the team.

By hand, the same thing is: `gh repo create`, `git clone … po`, `git submodule add … .claude/skills/agent-team`, then `/agent-team init` inside `po/`.

## On a host that runs 24/7

The roles are already written to work unattended — they loop on the board and wake when it is
their turn — but two things assume someone is in the room, and both are settings, not code:

```bash
export AGENT_TEAM_CLAUDE_FLAGS="--permission-mode acceptEdits"   # PO, Architect, Coder
export AGENT_TEAM_CODEX_FLAGS="--sandbox danger-full-access --ask-for-approval never"  # Reviewer, UX
./team open --tmux      # never the macOS Terminal path: AppleScript needs a logged-in desktop
```

Without the first line a role stops at its first permission prompt and waits forever. Leave the
PO out of it if you want to be asked before a story is written — it is the role you talk to.

Detach with `Ctrl-b d`; the tmux session keeps running after you log out. On a Mac, `caffeinate -s`
keeps the machine awake. One thing to watch: `wait-for` deliberately fails closed — if the network
or `gh` goes down it prints why and stops rather than looping on a board it cannot trust, so a
transient outage leaves roles idle until something restarts them.

## Upgrading a project's team

Inside any clone: `/agent-team upgrade` — or by hand, `git submodule update --remote .claude/skills/agent-team`, commit, push. Every project records its pinned version in `.team/team.md` and in the scaffold commit.

## Layout

```
SKILL.md          what Claude reads when you run /agent-team
bin/              po architect coder reviewer ux — launchers (pull, pick role file, start)
                  status                         — the board, derived from git + GitHub
team/TEAM.md      the rulebook every agent reads
team/roles/       product-owner architect coder reviewer ux
team/templates/   story plan note review icons
assets/           per-project files init writes: AGENTS.md, CLAUDE.md, .team/
scripts/          init.sh, scaffold.sh
workspace/team    the ./team launcher
```

## Changing the team

For every future project: edit `team/roles/*.md` here, commit, tag. For one project: drop a file in that project's `.team/roles/<role>.md`; the launcher prefers it over the submodule's. Keep roles short — if an agent misbehaves, the fix is usually fewer instructions, not more.
