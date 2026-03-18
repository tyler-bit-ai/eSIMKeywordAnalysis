# GitHub Pages Deployment

## Recommended Deployment Mode

- Keep `main` as the source-of-truth branch.
- Use GitHub Pages with `GitHub Actions` as the publish source.
- Do not treat `gh-pages` as the primary working branch.

## Branch Strategy

### Preferred Flow

1. Create a feature branch such as `feature/public-dashboard`.
2. Make changes to Python export code, static site files, and docs on the feature branch.
3. Validate locally.
4. Open a pull request into `main`.
5. Merge into `main`.
6. Let the Pages workflow publish the artifact built from `main`.

### Why This Flow

- Source code and deployment output stay separated.
- Review happens on normal source files instead of generated deployment commits.
- Rollback is simpler because the deployment is derived from a known `main` commit.

## Workflow Responsibilities

The GitHub Actions workflow should do the following:

1. Check out repository contents from `main`.
2. Install Python dependencies from `pyproject.toml`.
3. Generate the public dashboard JSON bundle into `site/data/dashboard_data.json`.
4. Upload `site/` as the Pages artifact.
5. Deploy the artifact to GitHub Pages.

## Required Repository Setting

In repository settings:

- Open `Settings -> Pages`
- Set `Build and deployment -> Source` to `GitHub Actions`

## Workflow File

- Workflow path:
  - `.github/workflows/deploy-pages.yml`

## Notes On `gh-pages`

- A manual `gh-pages` branch is only a fallback option.
- Use it only if the repository policy cannot use Actions-based Pages deployment.
- If that fallback is ever used, keep `gh-pages` deployment-only and never treat it as the main development branch.

## Local Validation Before Merge

1. Run or refresh the local reports.
2. Generate public dashboard data:
   - `python -c "from pathlib import Path; from keyword_analysis.pipeline import export_korea_public_dashboard; export_korea_public_dashboard(output_dir=Path('site/data'))"`
3. Serve the repository with a local static HTTP server.
4. Open `site/` through the server and confirm the dashboard loads `site/data/dashboard_data.json`.

## Deployment Trigger

- Default trigger:
  - push to `main`
- Optional trigger:
  - manual `workflow_dispatch`

## Expected Published Artifact

The Pages artifact should include:

- `site/index.html`
- `site/styles.css`
- `site/app.js`
- `site/data/dashboard_data.json`

The Pages artifact should not include:

- local SQLite databases
- collector failure logs
- arbitrary files from `outputs/`
