# Research Home

Public static research library, India macro monitor and rates paper tracker. Intended GitHub Pages URL: `https://aggasuk.github.io/research-home/`.

The `site/` directory is the complete publishable website. GitHub Actions validates and deploys it on pushes to `main`, or through the manual workflow button. No Bloomberg requests, local Python generators or data refreshes run in GitHub Actions.

## Update the saved website

### Navigation and RV workspace — 26 September 2026

The canonical shell lives in `scripts/navigation.html` and is applied by both publishers through `navigation.py`. It has five sections: Rates RV, Rates Trend, Research, Frameworks and India. Overview is removed; `#home` remains a compatibility route to Research. Research combines daily and topic briefs with optional filters. Frameworks combines methods, protocols, studies and frameworks. Rates Trend embeds the saved tracker inside the same shell at `#rates-trend`; its historical metadata and ledger are unchanged.

`python scripts/update_navigation.py` applies presentation changes to the existing package without importing new research or reading market caches. The v3 RV workspace has New today, Tracking and a persistent search across 246 structures. Signal rows and search open the same full model review; old review/model routes redirect to this workspace or the current methodology. The authorized 26 September v3 research run used completed 25 September closes. It evaluated 559 of 614 models, holding 55 for stale ESTR histories; no exact same-day model spot snapshots were available.

The existing package contains four complete daily briefs (10–13 September), three topic briefs, and six framework/study reports, plus Rates RV. Notion is an additional destination where linked, not a prerequisite for reading the hosted reports. Later RV-only updates do not synchronize the daily archive or Rates Trend snapshot. The visible latest-daily date reflects that limitation.

Validation: static-site validator, JavaScript syntax and browser checks pass. Non-RV report payloads and saved tracker metadata are preserved. The RV review supports model comparison, evidence period/direction filters, package expressions, targets, charts and episode history. Derived per-structure files load on demand.

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

The Rates RV section contains daily discovery and persistent signals, with one shared candidate review. The current methodology is under Frameworks. Original v2 studies remain explicitly historical archives. Model positions and P&L are simulations. A 5bp gross opportunity floor applies to new historical/current signals; no execution costs or investigate/paper tiers are applied.

After the authorized local v3 run, use `python scripts/update_rv_v3.py --rv-root "PATH/TO/rates_rv_v3"`, then `python scripts/validate_site.py`. This scoped updater reads the committed result, verifies cache hashes for diagnostic chart construction, and preserves other already-published reports, India and the older tracker. It excludes raw source caches, local file paths and private holdings. Commit these RV changes and push main to trigger the existing Pages workflow. Verify the hosted observation date and deployment before saving the local publication receipt. Do not use the legacy RV updater or full-site packager for routine RV updates.

The legacy `update_rv.py` rejects v3 sites to prevent an accidental downgrade. A separately authorized full research archive refresh must preserve the v3 workspace assets and metadata.

## Verification

The validator checks relative targets, the embedded report resource links, India navigation, duplicate static IDs, common credential/local-path patterns, and per-file manifest hashes. JavaScript syntax and core saved-page rendering are checked locally before the first publish. Browser visual verification is separate.

## Single historical qualification screen (26 September correction)

The v3 publisher now uses the model package's qualification.py: at least 8 full-history trades and 3 since 2022, positive gross means in both periods, and positive full-history gross mean in the proposed direction. No extra directional count requirement. Current statistical/5bp rules remain. Preserve the local selection_state.json: it records admission under the policy without backdating qualification or changing model fills. Only admitted signals populate New today/Tracking; every structure and raw history remains searchable. The same policy governs future daily observed entries. Original saved reference backtests were reused, not rerun or rewritten. Initial corrected screen: 46 model readings, 39 structures, 40 structure/direction groups.
