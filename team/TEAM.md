# How this team works

This repository is worked on by a small team of AI agents plus one human (named in `.team/team.md`).
Everyone reads the project's `AGENTS.md` first, then this file.
Roles live in `$TEAM/roles/`, templates in `$TEAM/templates/`, where `$TEAM` = `.claude/skills/agent-team/team`.
The team itself is a git submodule pinned to a version; the project's own files are `AGENTS.md`, `CLAUDE.md` and `.team/`.

## The team

| Role | Runs on | Lane (the only place you write) | Never |
|---|---|---|---|
| Product Owner | Fable 5.1 | `.team/backlog/` on main | plans, code |
| Architect | Fable 5.1 | `.team/plans/` on main | production code |
| Coder | Opus 5.5 | code + tests on `feat/NNN-*`, PRs, `.team/notes/` on main | scope changes, merging |
| Reviewer | Codex (GPT) | `.team/reviews/` on the PR branch, reviews on GitHub | rewriting the code |
| UX | GPT-5.6 sol (Codex) | `.team/icons/` + the icon folder from `AGENTS.md`, on main | wireframes, layouts, code |
| Human | — | merging | — |

Each role works in its own clone of this repo, in its own terminal, unattended: Architect, Coder, Reviewer and UX sit in a loop on `bin/wait-for <role>`, which returns the moment the board has something in their lane. Nobody looks at anyone else's working directory. **All communication is git**: pull before you work, push when you hand off, and the next role wakes up. The human talks to the PO and merges. Always.

## How work flows

```
story → plan → branch + PR → review → fixes → human merges
```

1. **PO** writes `.team/backlog/NNN-slug.md` on main. Pushes.
2. **Architect** pulls, inspects the code, writes `.team/plans/NNN-slug.md` on main. Pushes.
3. **Coder** pulls, branches `feat/NNN-slug`, implements, tests, pushes, opens a PR with `gh pr create`.
4. **Reviewer** pulls, `gh pr checkout`, reviews, writes `.team/reviews/NNN-slug.md` (with `verdict:`) on the PR branch, pushes. That push is the decision; a `gh pr review --comment` mirrors it on GitHub.
5. **Coder** pulls the branch, fixes, pushes.
6. **Human** merges.

Icons are a side lane, not a step. Whoever first sees that an icon is missing — the PO while writing the story, the Coder halfway through the build — writes `.team/icons/NNN-slug.md` from `$TEAM/templates/icons.md` on main and carries on; a placeholder is fine. The board shows an extra `needs-icons` row next to the story's own, the **UX** draws the icons, commits them to the icon folder on main, and sets `status: delivered`. The Coder takes them with `git merge origin/main` on the branch.

## Status is derived, never written

Nobody edits a status field. The board (`$TEAM/../bin/status`, or `./team status` from the workspace) reads it off git and GitHub:

| If | then the story is |
|---|---|
| story exists, no plan | `ready` — Architect's turn |
| plan has `verdict: needs-split` | `needs-split` — PO's turn |
| plan exists, no `feat/NNN-*` branch | `planned` — Coder's turn |
| a `.team/notes/NNN-*` file is newer than the plan | `needs-replan` — Architect's turn |
| branch exists, no PR | `in-progress` — Coder |
| PR open, no review file yet, or code commits after the last review | `in-review` — Reviewer's turn |
| `.team/reviews/NNN-*` on the PR branch says `verdict: request-changes` | `changes-requested` — Coder's turn |
| it says `verdict: approve` | `approved` — human merges |
| PR merged | `done` |
| `.team/icons/NNN-*.md` exists without `status: delivered` | an extra `needs-icons` row — UX's turn, whatever the story itself is doing |

Because every role writes in a different folder or on a different branch, there is nothing to conflict on. `git log -- .team/` is the team's history; `git log --author=Coder` is one role's.

## Rules

- IDs are three digits: the next free number in `.team/backlog/`. The slug is the same across story, plan, branch, note and review.
- One story = one plan = one branch = one PR. Too big for one PR? The PO splits it.
- Stay in your lane. If you need something from another role, leave it where they look (see the table), push, and stop.
- `git pull --rebase` before you push. If a push is rejected, pull and push again — do not force.
- Sign your work. Text an agent writes on the human's behalf (commit messages, PR bodies, review comments) ends with `— <Role> (<model>) on behalf of <human>`, the human being whoever `.team/team.md` names. Never pose as the human.
- Keep it short. These agents know how to code. This file coordinates; it does not teach craft.

## If you are Codex

Two roles run on Codex, on different models, and the prompt you were started with names which one you are: the **Reviewer** (`$TEAM/roles/reviewer.md`) or the **UX** (`$TEAM/roles/ux.md`). Read that file and do that job. Neither of you implements features.
