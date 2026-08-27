---
name: contributing-to-fork
description: Use when improvements made during a session should be contributed back to an upstream repo via a fork PR. Applies when you've built a reusable pattern, fixed a gap, or added documentation that belongs in the source project, not just the local config.
---

# Contributing to a Fork

Encode session work as an upstream contribution: clone the fork, make targeted changes, push a branch, open a PR via GitHub API — no `gh` CLI required.

## When to Use

- You've built something (hook, doc, pattern) that belongs in the source project
- The local change is generalizable — not project-specific config
- You have a fork URL and git credentials already working

## What to Contribute

Before cloning, decide what's worth sending upstream. Ask: "Would this help anyone using the tool on any project?" If yes, contribute. If it references local paths, naming conventions, or project internals — keep it local.

| Keep local | Contribute upstream |
|---|---|
| Project-specific managed blocks | Reusable hook scripts |
| Local path references | Pattern/workflow documentation |
| Tool configuration | Provider file expansions |
| Session logs | Bug/gap fixes in existing docs |

## Workflow

### 1. Inspect the upstream repo structure first

Before writing anything, understand where things live:

```bash
# Use WebFetch to read the repo tree
# Check: docs/, scripts/, skills/, provider files (CLAUDE.md, AGENTS.md, GEMINI.md)
```

Read the existing files you plan to modify. Don't add to a section that already covers the same ground.

### 2. Clone the fork and create a branch

```bash
git clone https://github.com/<user>/<repo>.git <repo>-fork
cd <repo>-fork
git checkout -b feat/<descriptive-name>
```

Branch naming: `feat/` for additions, `fix/` for corrections, `docs/` for documentation only.

### 3. Make targeted changes

- One PR = one coherent theme. Don't bundle unrelated improvements.
- New files go in the most logical existing directory (`docs/`, `scripts/hooks/`, etc.)
- If a directory doesn't exist, create it only if the name is self-evident
- Read every file you modify before editing it

### 3a. Scrub personal references before committing

**Never include personal file names, project names, repository names, or local paths in upstream contributions.** Replace everything with generic placeholders.

Common leaks from session work:

| Replace | With |
|---|---|
| Real project name (`project-a-next`) | `<project-slug>` or a neutral example (`my-project`) |
| Real file paths (`src/actions/users.ts`) | `src/services/example.ts` |
| Real function/feature names tied to your domain | Generic equivalents (`processOrder()` → `processItem()`) |
| Real branch names (`feature/auth-refactor`) | `feature/my-feature` |
| Local system paths (`{{USER_HOME_FWD}}/...`) | Generic paths or omit entirely |
| Your GitHub username in examples | `<your-user>` |

**Scan before committing:**

```bash
# Replace MY-PROJECT and MY-USERNAME with your actual values
git diff main..HEAD -- <changed-files> | grep "^+" | grep -iE "MY-PROJECT|MY-USERNAME|Users/MY-NAME|my-real-function"
```

If anything matches — fix it, then re-scan before pushing.

### 4. Commit

Follow the repo's existing commit style. When in doubt:

```bash
git commit \
  -m "feat: <imperative summary under 70 chars>" \
  -m "<body: what changed and why, not how>" \
  -m "Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

### 5. Push the branch

```bash
git push origin feat/<name>
# The push output prints the PR creation URL — note it
```

### 6. Open the PR via GitHub API

`gh` CLI is often absent. Use `git credential fill` + `curl` instead.

**Step 1 — get the token:**

```bash
git credential fill << 'EOF'
protocol=https
host=github.com
EOF
# Outputs: username=<user> / password=<token>
```

**Step 2 — write the payload to a file** (heredoc in curl is unreliable on Windows):

```json
// pr-payload.json
{
  "title": "feat: short description",
  "head": "<github-user>:feat/<branch>",
  "base": "main",
  "body": "## Summary\n\n- bullet\n- bullet\n\n## Test Plan\n\n- [ ] step"
}
```

**Step 3 — POST with `--ssl-no-revoke`** (required on Windows — schannel blocks revocation checks):

```bash
curl -s --ssl-no-revoke -X POST \
  -H "Authorization: token <token>" \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Content-Type: application/json" \
  -d @pr-payload.json \
  "https://api.github.com/repos/<owner>/<repo>/pulls" \
  | python -c "import json,sys; r=json.load(sys.stdin); print(r.get('html_url') or r.get('message'))"
```

**Step 4 — clean up:**

```bash
rm pr-payload.json
```

## PR Body Template

```markdown
## Summary

- What was added/changed and why

## New Files

- `path/to/file.ext` — one-line description

## Test Plan

- [ ] command that verifies it works
- [ ] edge case that should no-op
```

## Opening the PR on the Right Repo

A PR on your own fork (`your-user/repo`) is only visible to you — the upstream maintainer won't see it. To get the maintainer's attention:

1. **Create an issue first** on the upstream repo (`upstream-owner/repo/issues`) — describes the problem and links the incoming PR
2. **Create the PR against the upstream** (`upstream-owner/repo/pulls`) with `"head": "<your-user>:<branch>"` and `"base": "main"`

The branch only needs to exist on your fork — GitHub handles the cross-repo diff automatically.

```bash
# Issue on upstream
curl -s --ssl-no-revoke -X POST \
  -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/<upstream-owner>/<repo>/issues" \
  -d @issue-payload.json

# PR on upstream, branch from your fork
curl -s --ssl-no-revoke -X POST \
  -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/<upstream-owner>/<repo>/pulls" \
  -d @pr-payload.json
# pr-payload.json: "head": "<your-user>:<branch>", "base": "main"
```

## Common Mistakes

| Mistake | Fix |
|---|---|
| Curl fails with `CRYPT_E_NO_REVOCATION_CHECK` | Add `--ssl-no-revoke` flag |
| Curl body empty / JSON parse error | Write payload to file, use `-d @file.json` |
| `gh` not found | Use `git credential fill` + `curl` workflow above |
| PR created against wrong base | Set `"base": "main"` explicitly in payload |
| Changes include local paths | Strip before contributing; local paths break for others |
| Committing too much | One PR per theme; split unrelated improvements |

## Cleanup

The cloned fork directory is a temporary workspace. Delete it after the PR is open unless you plan further contributions:

```bash
rm -rf "C:/Users/<user>/<repo>-fork"
```
