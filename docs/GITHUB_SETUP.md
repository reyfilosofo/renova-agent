# GitHub setup

## Option A — GitHub website

1. Open GitHub.
2. Create a new repository named `renova-agent`.
3. Choose private at first.
4. Do not add README, license or gitignore if you plan to push this folder as-is.
5. Upload or push the project.

## Option B — GitHub CLI

From the project folder:

```bash
git init
git add .
git commit -m "Bootstrap RENOVA Agent"
gh repo create reyfilosofo/renova-agent --private --source=. --remote=origin --push
```

## Recommended branches

```bash
git checkout -b codex/bootstrap-renova-agent
```

## Recommended PR title

```text
Bootstrap RENOVA Agent technical scaffold
```

## Recommended PR body

```text
## Summary
- Adds Next.js + TypeScript scaffold.
- Adds RENOVA Agent landing page.
- Adds SVG identity assets.
- Adds local agent planning API route.
- Adds documentation for Codex, GitHub and deployment.
- Adds CI structure check and build workflow.

## Validation
- npm run check:structure
- npm run build

## Notes
No secrets or external APIs are included in this initial scaffold.
```
