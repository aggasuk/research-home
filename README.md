# Research Home

Public static research library, India macro monitor and rates paper tracker. Intended GitHub Pages URL: `https://aggasuk.github.io/research-home/`.

The `site/` directory is the complete publishable website. GitHub Actions validates and deploys it on pushes to `main`, or through the manual workflow button. No Bloomberg requests, local Python generators or data refreshes run in GitHub Actions.

## Update the saved website

Refresh the desired local research/data first and run its existing builder. Then package the saved outputs:

```text
python scripts/build_public.py --source "PATH/TO/research-home"
python scripts/validate_site.py
git add site
git commit -m "Update saved research snapshots"
git push
```

Publishing does not itself refresh observations. The site displays source dates and stays available independently of the local computer. It uses relative links and does not need a custom domain.

## Publication scope

Includes rendered research reports, embedded charts, linked presentation images and strategy CSVs, the India page and the saved paper tracker. Notion and bank-site links retain their own login requirements.

The linked reproducible-model ZIP is omitted because it also contains raw market histories and a position file. Local diagnostic JSON links are rendered as text. Raw source directories, working caches, private position files, local credentials and machine-specific configuration are not packaged.

Report downloads are standalone HTML copies of the rendered reports. Original local reports and the SA Dashboard deployment are not modified.

## First deployment

Create public repository `aggasuk/research-home`, push this directory's tracked files to `main`, and set GitHub Pages build type to GitHub Actions. The workflow uploads only `site/`. GitHub CLI authentication is required for repository creation and pushing.

## Rates RV daily publishing

The Rates RV section contains daily discovery and persistent signals, plus the complete original interactive methodology/backtest and trade-ticket pages. The historical research remains dated 21 September 2026; discovery shows its own current source close. Model positions and P&L are simulations.

After the authorized local RV run and Research Home rebuild, use `python scripts/update_rv.py --source "PATH/TO/research-home"`, then `python scripts/validate_site.py`. This scoped updater changes RV pages and navigation while preserving other already-published reports, India and the older tracker. It excludes local diagnostic/cache downloads. Commit these RV changes and push main to trigger the existing Pages workflow. Do not use the full-site packager for routine RV updates or publish unrelated local reports implicitly.

The full `build_public.py` packager also understands the two embedded RV research pages when a full-site update is explicitly requested.

## Verification

The validator checks relative targets, the embedded report resource links, India navigation, duplicate static IDs, common credential/local-path patterns, and per-file manifest hashes. JavaScript syntax and core saved-page rendering are checked locally before the first publish. Browser visual verification is separate.
