# Team config

human: {{HUMAN}}
project: {{PROJECT_NAME}}
profile: lightweight

models:
  coder: claude-opus-5-5
  images: gpt-6-sol
  reviewer: gpt-6-sol

merge: human

team: .claude/skills/agent-team @ {{SKILL_VERSION}}

The human talks directly to the Coder. There is no PO or Architect.
Model overrides: AGENT_TEAM_CODER_MODEL, AGENT_TEAM_IMAGES_MODEL,
AGENT_TEAM_REVIEWER_MODEL. The models above document the profile defaults;
launchers use those defaults unless overridden by the environment or CLI.
Per-project role overrides: `.team/roles/<role>.md`.
