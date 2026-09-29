"""Offline integration tests: real git/submodules, stubbed GitHub and model clients.
Run: python3 -m unittest discover -s tests -v
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class Profiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='agent-team-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.startswith(('AGENT_TEAM_', 'GIT_'))}
        self.env.update(GIT_CONFIG_GLOBAL=str(self.root / 'gitconfig'),
                        GIT_CONFIG_NOSYSTEM='1', GIT_ALLOW_PROTOCOL='file',
                        GIT_TERMINAL_PROMPT='0')
        self.run_cmd('git', 'config', '--global', 'user.name', 'Test Human')
        self.run_cmd('git', 'config', '--global', 'user.email', 'test@example.invalid')
        self.run_cmd('git', 'config', '--global', 'init.defaultBranch', 'main')
        self.remote_dir = self.root / 'remotes'
        self.remote_dir.mkdir()
        self.run_cmd('git', 'config', '--global',
                     f'url.file://{self.remote_dir}/.insteadOf', 'https://github.com/local/')
        self.stub = self.root / 'bin'
        self.stub.mkdir()
        self.env['PATH'] = str(self.stub) + os.pathsep + self.env['PATH']
        self.write_executable('gh', '''#!/usr/bin/env bash
case "$1 $2" in
  'auth status'|'repo view') exit 0 ;;
  'pr list') printf '%s' "${TEST_PRS:-}" ;;
  *) echo "unexpected gh call" >&2; exit 2 ;;
esac
''')
        for client in ('claude', 'codex'):
            self.write_executable(client, '#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
        self.write_executable('tmux', '''#!/usr/bin/env python3
import json,os,sys
with open(os.environ['TEST_TMUX_LOG'], 'a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')
if sys.argv[1] == 'has-session': sys.exit(1)
if sys.argv[1] in ('new-session','split-window'): print('%1')
''')
        self.team = self.root / 'team-source'
        shutil.copytree(SOURCE, self.team, ignore=shutil.ignore_patterns('.git', '__pycache__', '.DS_Store'))
        self.run_cmd('git', 'init', '-q', str(self.team))
        self.commit(self.team)

    def write_executable(self, name, contents):
        p = self.stub / name
        p.write_text(contents)
        p.chmod(0o755)

    def run_cmd(self, *args, cwd=None, check=True, env=None):
        result = subprocess.run([str(a) for a in args], cwd=cwd or self.root,
                                env=env or self.env, text=True, capture_output=True)
        if check and result.returncode:
            self.fail(f'{args}\n{result.stdout}\n{result.stderr}')
        return result

    def commit(self, repo, push=False):
        self.run_cmd('git', 'add', '-A', cwd=repo)
        self.run_cmd('git', 'commit', '-qm', 'test fixture', cwd=repo)
        if push:
            self.run_cmd('git', 'push', '-q', cwd=repo)

    def workspace(self, profile=None):
        self.run_cmd('git', 'init', '-q', '--bare', self.remote_dir / 'demo.git')
        ws = self.root / 'demo-team'
        args = ['bash', self.team / 'new-project.sh', 'local/demo', '--dir', ws,
                '--team-url', self.team, '--no-open']
        if profile:
            args.extend(['--profile', profile])
        self.run_cmd(*args)
        return ws

    def board(self, clone, prs=''):
        env = dict(self.env, TEST_PRS=prs)
        result = self.run_cmd(clone / '.claude/skills/agent-team/bin/status', '--tsv', cwd=clone, env=env)
        return [row.split('\t') for row in result.stdout.splitlines()]

    def test_lightweight_bootstrap_launch_and_board(self):
        ws = self.workspace('lightweight')
        self.assertEqual({p.name for p in ws.iterdir() if p.is_dir()}, {'coder', 'images', 'reviewer'})
        coder = ws / 'coder'
        for role, model in [('coder', 'claude-opus-5-5'), ('images', 'gpt-6-sol'), ('reviewer', 'gpt-6-sol')]:
            args = json.loads(self.run_cmd(ws / 'team', role).stdout)
            self.assertEqual(args[args.index('--model') + 1], model)
            if role == 'coder':
                self.assertIn('/profiles/lightweight/coder.md', args[args.index('--append-system-prompt-file') + 1])
        args = json.loads(self.run_cmd(ws / 'team', 'reviewer', '--model', 'explicit-model').stdout)
        self.assertEqual(args.count('--model'), 1)
        self.assertEqual(args[args.index('--model') + 1], 'explicit-model')
        args = json.loads(self.run_cmd(ws / 'team', 'images', env=dict(self.env, AGENT_TEAM_IMAGES_MODEL='image-override')).stdout)
        self.assertEqual(args[args.index('--model') + 1], 'image-override')
        self.assertNotEqual(self.run_cmd(ws / 'team', 'po', check=False).returncode, 0)
        self.assertNotEqual(self.run_cmd(ws / 'team', 'add', 'ux', check=False).returncode, 0)
        self.run_cmd(ws / 'team', 'status')
        self.run_cmd(ws / 'team', 'log')
        self.run_cmd(ws / 'team', 'pull')
        log = self.root / 'tmux.log'
        self.run_cmd(ws / 'team', 'open', '--tmux', env=dict(self.env, TEST_TMUX_LOG=str(log)))
        panes = [json.loads(l) for l in log.read_text().splitlines()]
        self.assertEqual([p[-1].split()[-1] for p in panes if p[0] in ('new-session', 'split-window')],
                         ['coder', 'images', 'reviewer'])
        request = coder / '.team/images/001-hero.md'
        request.write_text('id: 001\ntitle: Hero\nstatus: requested\n')
        self.commit(coder, push=True)
        self.assertEqual(self.board(coder)[0][1:4], ['needs-images', 'Hero', 'images'])
        self.run_cmd(ws / 'images/.claude/skills/agent-team/bin/wait-for', 'images', '0', cwd=ws / 'images')
        request.write_text('id: 001\ntitle: Hero\nstatus: delivered\n')
        story = coder / '.team/backlog/002-feature.md'
        story.write_text('id: 002\ntitle: Feature\n')
        self.commit(coder, push=True)
        self.assertEqual(self.board(coder)[0][1:4], ['ready', 'Feature', 'coder'])
        self.run_cmd('git', 'checkout', '-qb', 'feat/002-feature', cwd=coder)
        self.run_cmd('git', 'push', '-qu', 'origin', 'feat/002-feature', cwd=coder)
        self.assertEqual(self.board(coder)[0][1], 'in-progress')
        self.assertEqual(self.board(coder, 'feat/002-feature\t7\tOPEN\n')[0][1], 'in-review')
        (coder / '.team/reviews/002-feature.md').write_text('verdict: request-changes\n')
        self.commit(coder, push=True)
        self.assertEqual(self.board(coder, 'feat/002-feature\t7\tOPEN\n')[0][1:4], ['changes-requested', 'Feature', 'coder'])
        self.assertEqual(self.board(coder, 'feat/002-feature\t7\tMERGED\n')[0][1], 'done')

    def test_default_full_and_legacy(self):
        ws = self.workspace()
        self.assertEqual({p.name for p in ws.iterdir() if p.is_dir()}, {'po', 'architect', 'coder', 'reviewer', 'ux'})
        args = json.loads(self.run_cmd(ws / 'team', 'coder').stdout)
        self.assertEqual(args[args.index('--model') + 1], 'opus')
        args = json.loads(self.run_cmd(ws / 'team', 'reviewer').stdout)
        self.assertNotIn('--model', args)
        po = ws / 'po'
        config = po / '.team/team.md'
        config.write_text(config.read_text().replace('profile: full\n', ''))
        (po / '.team/backlog/001-feature.md').write_text('id: 001\ntitle: Feature\n')
        self.commit(po, push=True)
        self.assertEqual(self.board(po)[0][1:4], ['ready', 'Feature', 'architect'])
        (po / '.team/plans/001-feature.md').write_text('verdict: plan\n')
        self.commit(po, push=True)
        self.assertEqual(self.board(po)[0][1:4], ['planned', 'Feature', 'coder'])
        self.assertNotEqual(self.run_cmd(ws / 'team', 'images', check=False).returncode, 0)

    def test_overrides_scaffold_idempotence_and_extra_clone(self):
        ws = self.workspace('lightweight')
        coder = ws / 'coder'
        config = coder / '.team/team.md'
        before = config.read_bytes()
        self.run_cmd('bash', self.team / 'scripts/scaffold.sh', cwd=coder)
        self.assertEqual(config.read_bytes(), before)
        self.assertNotEqual(self.run_cmd('bash', self.team / 'scripts/scaffold.sh', '--profile', 'full', cwd=coder, check=False).returncode, 0)
        self.assertEqual(config.read_bytes(), before)
        overrides = coder / '.team/roles'
        overrides.mkdir()
        (overrides / 'coder.md').write_text('Project role override\n')
        self.commit(coder, push=True)
        args = json.loads(self.run_cmd(ws / 'team', 'coder', env=dict(self.env, AGENT_TEAM_CODER_MODEL='test-model')).stdout)
        self.assertEqual(args[args.index('--model') + 1], 'test-model')
        self.assertEqual(args[args.index('--append-system-prompt-file') + 1], '.team/roles/coder.md')
        self.run_cmd(ws / 'team', 'add', 'coder')
        self.assertTrue((ws / 'coder-2/.git').is_dir())
        args = json.loads(self.run_cmd(ws / 'team', 'coder', '2').stdout)
        self.assertEqual(args[args.index('--model') + 1], 'claude-opus-5-5')

    def test_invalid_profile_rejected_before_bootstrap(self):
        result = self.run_cmd('bash', self.team / 'new-project.sh', 'local/demo', '--profile', 'bad', check=False)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / 'demo-team').exists())


if __name__ == '__main__':
    unittest.main()
