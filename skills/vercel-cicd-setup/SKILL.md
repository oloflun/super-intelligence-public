---
name: vercel-cicd-setup
description: "Wire GitHub Actions deploy pipelines for a Next.js project on Vercel (production + preview, no Vercel Git integration)"
version: 1.0.0
metadata:
  tags: [vercel, github-actions, ci-cd, nextjs, devops]
  category: devops
---

# Vercel CI/CD Setup

## When to Use

New project needs Vercel deployments controlled by GitHub Actions (not Vercel's built-in Git integration). Typically:
- `main` branch → production deployment
- `development` branch → preview/staging deployment

## Procedure

### 1. Verify prerequisites
```powershell
vercel --version     # must be installed
vercel whoami        # must be authenticated
```

### 2. Create and link Vercel project
```bash
cd <project-root>
vercel link --yes --project <project-name> --scope <team-slug>
```
This creates `.vercel/project.json` with `projectId` and `orgId`. Read both values — needed for GitHub secrets.

If the project already exists in Vercel, `vercel link` finds and links it. If not, it creates it and connects the GitHub repo automatically.

### 3. Create `vercel.json`
```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "git": {
    "deploymentEnabled": false
  }
}
```
The `"git": {"deploymentEnabled": false}` key is critical — it disables Vercel's own Git integration so only GitHub Actions deploys. Without this, every push triggers two deployments.

### 4. Create production workflow
`.github/workflows/deploy-production.yml`:
```yaml
name: Deploy — Production

on:
  push:
    branches:
      - main

jobs:
  deploy:
    name: Deploy to Vercel (production)
    runs-on: ubuntu-latest
    environment:
      name: production
      url: ${{ steps.deploy.outputs.url }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm

      - name: Install Vercel CLI
        run: npm install -g vercel@latest

      - name: Pull Vercel environment
        run: vercel pull --yes --environment=production --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

      - name: Build
        run: vercel build --prod --token=${{ secrets.VERCEL_TOKEN }}
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

      - name: Deploy
        id: deploy
        run: |
          URL=$(vercel deploy --prebuilt --prod --token=${{ secrets.VERCEL_TOKEN }})
          echo "url=$URL" >> $GITHUB_OUTPUT
        env:
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

### 5. Create development/preview workflow
`.github/workflows/deploy-development.yml` — same structure, change:
- `branches: [development]`
- `environment.name: development`
- `vercel pull --yes --environment=preview` (not `production`)
- `vercel build` (no `--prod` flag)
- `vercel deploy --prebuilt` (no `--prod` flag)

### 6. Ensure `package-lock.json` is committed
`actions/setup-node@v4` with `cache: npm` **requires** a lock file. If missing:
```bash
npm install --package-lock-only   # generates lock file without local install
git add package-lock.json
git commit -m "ci: add package-lock.json for npm cache in GitHub Actions"
```

### 7. Add GitHub secrets
In GitHub → repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|---|---|
| `VERCEL_TOKEN` | Create at vercel.com/account/tokens |
| `VERCEL_ORG_ID` | `orgId` from `.vercel/project.json` |
| `VERCEL_PROJECT_ID` | `projectId` from `.vercel/project.json` |

Note: `.vercel/` is typically gitignored — that's fine. The workflows read IDs from env vars, not from the file.

### 8. Commit and push workflows to both branches
```bash
git add .github/workflows vercel.json package-lock.json
git commit -m "ci: add Vercel deploy workflows for main and development"

git checkout main && git merge <source-branch> && git push origin main
git checkout development && git merge <source-branch> && git push origin development
```

## Pitfalls

- **Duplicate deployments:** Forgetting `"git": {"deploymentEnabled": false}` in `vercel.json` causes both Vercel's Git integration AND GitHub Actions to deploy on every push.
- **Missing lock file:** `actions/setup-node@v4 cache: npm` fails with `Error: Dependencies lock file is not found` if `package-lock.json` (or `yarn.lock`) is not committed. Fix: `npm install --package-lock-only`.
- **`.vercel/` gitignored:** The `.vercel/project.json` IDs are typically not committed. Always capture `projectId`/`orgId` immediately after `vercel link` and add to GitHub secrets before closing the terminal.
- **Workflow only fires on target branches:** Workflows pushed to a feature branch do not run until merged into `main` or `development`. Always merge/push to both target branches as the final step.
- **Branch doesn't exist yet:** If `development` branch doesn't exist on remote, create it before pushing the workflow, or the trigger never fires.

## Verification

1. Go to GitHub → Actions tab — both workflows should appear after the push.
2. Check the run triggered by the push: all steps should be green.
3. In Vercel dashboard, confirm a deployment appears for the correct environment (Production vs Preview).
4. Visit the deployment URL from the workflow's `url` output.

## Changelog
- 2026-05-24 v1.0.0 — Initial creation from project-b/snipra setup session
