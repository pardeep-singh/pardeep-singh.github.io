---
name: refresh-site-content
description: Use when refreshing the site with new GitHub, Kaggle or Coursera work, or when asked what the site is missing.
category: web-content
---

Pull the latest open source, Kaggle and Coursera activity, draft the site updates on a branch, and ship them only after the user approves the preview.

## 1. Fetch

```bash
python3 -I .claude/skills/refresh-site-content/scripts/fetch_sources.py --site . [--since YYYY-MM-DD] [--out <scratchpad>/refresh.json]
```

- Sources: GitHub PRs on other people's repos and your own non-fork repos (through the logged-in `gh` CLI), Kaggle profile stats, notebooks, datasets and models (public endpoints, no login needed), and Coursera certificates (JSON embedded in the public profile page).
- `--since` defaults to the date of the last commit that changed a page. Pass an earlier date for a fuller sweep.
- An item counts as already on the site when its URL appears in any `*.html` file. Items matching `exclude.txt` are never suggested.
- Each source fails on its own. Report any `ERROR` line to the user rather than guessing. The most common one is a Coursera layout change; in that case, read `--out` and the page itself.

## 2. Decide what belongs on the site

The site lists highlights, not every item. Propose changes; don't paste everything the script finds.

- **Open source** (`projects.html`): one dated entry per upstream project. When a project gets new merged PRs, update its count and date span, and fold notable PRs into the theme bullets. Mention open PRs as "In review" and move them to merged once they land. Skip PRs that were closed without merging. If a repo has a new burst of work, it may also belong in "Lately" on `index.html`.
- **Own repos**: add a new non-fork repo only if it is real work. Ask about anything that looks like a test, an assignment or a fork of a course.
- **Kaggle**: update the stats sentence on `projects.html` whenever the "may be stale" section lists something. Add a notebook to a themed row when it has a medal or represents new work (for example a new LLM fine-tune). Course exercises and one-off experiments can stay off the site. Update dataset download counts when they have changed noticeably.
- **Coursera** (`experience.html`): follow `dated-items-list-content`. A specialization is one row; fold its courses into it. Name any issuer you inferred.
- **"Lately"** (`index.html`): keep about five of the newest notable items, newest first, drawn from every source: roles, open source, own repos, Kaggle and Coursera. Lately is checked separately from the other pages, because an item linked from `experience.html` or `projects.html` can still be missing from Lately. The report's "Lately" section lists the newest item per source with MISSING or "in Lately". A new Coursera certificate or specialization always goes in. For the other sources, decide whether a MISSING item is notable enough to replace the oldest entry.
- Whenever the user turns an item down, add it to `exclude.txt` with a short reason.

## 3. Draft and preview

- Branch from an up-to-date `main`: `git switch main && git pull && git switch -c content/refresh-<YYYY-MM-DD>`.
- Edit in the existing style: `<ul class="items">` entries, first-person voice, no phone number, nav and footer unchanged.
- Check that every new link loads (`curl -s -o /dev/null -L -w '%{http_code}'`, expecting 200), and take screenshots as described in `github-pages-merge-and-verify`.
- Show the user a short list of what changed, with the preview URL and anything you inferred, then wait for approval.

## 4. Ship

After the user approves, follow `github-pages-merge-and-verify` in one pass: commit, PR, merge, verify the Pages build. Commit and PR text must carry no AI attribution.
