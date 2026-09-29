# Lightweight team

Read project conventions in `AGENTS.md` and project identity in `.team/team.md`.
`$TEAM` is `.claude/skills/agent-team/team`. This profile replaces the full team's
role table and workflow. There is no Product Owner, Architect, or UX role.

| Role | Default model | Owns |
|---|---|---|
| Coder | Claude Opus 5.5 (`claude-opus-5-5`) | Human conversation, `.team/backlog/` and image requests on main, code and tests on feature branches |
| Images | Codex GPT-6 Sol (`gpt-6-sol`) | `.team/images/` and requested image assets on main |
| Reviewer | Codex GPT-6 Sol (`gpt-6-sol`) | `.team/reviews/` on the PR branch and GitHub review comments |
| Human | — | Priorities and merging |

Each agent uses its own clone and terminal. Communicate durable requests and
results through git/GitHub. Pull before working and push at handoffs. Do not
force-push. Sign commits, PR descriptions and comments with
`— <Role> (<actual model>) on behalf of <human>`.

The human talks directly to the Coder. The flow is:

`request → short story → implementation + PR → review → fixes → human merges`

No plan file is required. The board sends stories without a branch directly to
the Coder. One story has one three-digit ID, slug, branch (`feat/NNN-slug`) and PR.
Resume your existing work after interruption; check remote branches and PRs first.

Images are a parallel lane: the Coder writes `.team/images/NNN-slug.md` using
`$TEAM/templates/images.md`, pushes, and can build against placeholders. The Images
agent delivers assets on main and marks the request `status: delivered`. The Coder
merges origin/main into the feature branch, integrates the assets, and reruns
relevant checks before review. Required images must be integrated before calling
an implementation complete. Standalone image requests do not need a backlog story.

Review decisions live in `.team/reviews/NNN-slug.md` on the PR branch, mirrored as
GitHub comments because these agents may share the PR author's account. A reviewer
checks the story and actual diff; no architect plan is expected. Only the human
merges. A missing image tool or unavailable model is a blocker to report, not a
reason to silently substitute a model or invent a delivered artifact.

Project role overrides in `.team/roles/` take precedence over bundled roles;
ensure any overrides also follow this profile.
