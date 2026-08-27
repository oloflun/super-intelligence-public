---
name: vercel-duplicate-deployments
description: "Fix: GitHub Actions + Vercel Git Integration create duplicate deploys, masking production in dashboard"
user-invocable: false
origin: auto-extracted
---

# Vercel Duplicate Deployments: GitHub Actions + Git Integration Conflict

**Extracted:** 2026-05-15
**Context:** Projects with both Vercel Git Integration and GitHub Actions Vercel deploy workflows

## Problem

When both Vercel Git Integration AND GitHub Actions deploy workflows are active, every push creates **two deployments**:

1. **Git Integration deployment** — has a branch alias URL: `project-git-branch-team.vercel.app`
2. **GitHub Actions deployment** — has only a random hash URL: `project-abc123-team.vercel.app`

The GitHub Actions deployment becomes the "latest" in the Vercel dashboard because it fires slightly after Git Integration (it waits for checkout). It has no branch alias, so it:
- Clutters the dashboard (2 entries per commit instead of 1)
- Masks the real production deployment (the one with `target: "production"`)
- Makes the "latest deployment" ambiguous — the visible one is a preview-targeting GitHub Actions deploy, not the production Git Integration deploy

**Symptom:** Dashboard shows only preview deployments; production appears missing or outdated. Preview URL is accessible but production alias (`project-git-main-team.vercel.app`) points to old code.

**Related:** Vercel preview URLs (e.g. `project-git-branch-team.vercel.app`) on Hobby plan require Vercel account login (SSO/Deployment Protection). An unauthenticated browser gets HTTP 401 with Vercel's auth spinner — this looks like "Internal Server Error" but is not. Test with `vercel inspect` or the MCP `web_fetch_vercel_url` tool to get the real HTTP status.

## Diagnosis

Use Vercel MCP or `vercel ls` and look for two patterns per commit SHA:
- `"branchAlias": "project-git-branch-team.vercel.app"` → Git Integration ✓
- No `branchAlias` field, `target: null` → GitHub Actions duplicate ✗

## Solution

Delete the GitHub Actions workflow files — Git Integration handles all deploys automatically:

```bash
rm .github/workflows/deploy-preview.yml
rm .github/workflows/deploy-production.yml
git add -u
git commit -m "ci: remove duplicate GitHub Actions deploy workflows"
git push origin development
```

Then merge to main to trigger a clean production deployment via Git Integration:

```bash
git checkout main
git merge development --no-ff -m "chore: merge development → main"
git push origin main
```

If branches have diverged (main has commits not on development), merge main into development first using `--strategy-option=ours` to prefer development content on conflicts:

```bash
git checkout development
git merge main --strategy=ort --strategy-option=ours --no-edit
# then proceed with the workflow deletion commit + push
```

## When to Use

- Dashboard shows only preview deployments, no production
- "Latest deployment" in dashboard is always a preview even after merging to main
- Two deployments appear per commit in the Vercel deployment list
- Found `.github/workflows/deploy-*.yml` alongside an active Vercel Git Integration

## Prevention

Choose **one** deployment method — do not use both:
- **Vercel Git Integration** (recommended): auto-deploys on push, creates branch aliases, handles preview/production routing automatically
- **GitHub Actions + `vercel deploy`**: use only when you need controlled build steps between commit and deploy (tests, canary promotion) — and you must disable Git Integration in Vercel project settings to avoid duplication
