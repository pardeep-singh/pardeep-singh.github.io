---
name: github-pages-merge-and-verify
description: Use when merging and deploying this GitHub Pages site.
category: deployment
---

Ship site changes as a feature-branch PR, merge with `gh`, and verify the Pages build for the merged commit before reporting the deploy as live. Once the user approves a diff (for example "lgtm, merge and deploy"), run commit, push, PR, merge, and verify in one pass without asking again.

- Stage explicit paths only (`git add <file>...`), never `git add -A`. Keep untracked personal files out of commits: the CV PDF (it carries a phone number) and `.claude/`. Check `git status --short` first.
- Before the PR, check that the header nav and footer match on every page (they are duplicated), that CLAUDE.md's File Structure section matches the pages as they now are, and that JSON-LD and canonical URLs point at the host that serves the site. Flag a mismatch to the user instead of silently editing it.
- Visual check: serve with `python3 -m http.server 8765 --bind 127.0.0.1 &`, take a headless Chrome screenshot (`--headless=new --window-size=1400,4200 --screenshot=<path>`), and crop with `sips -c <h> <w> --cropOffset <y> <x>` because PIL is not installed. Kill the server afterward.
- Merge: `gh pr create --base main --head <branch>`, then `gh pr merge <branch> --merge`. Keep the branch unless asked to delete it. Then `git switch main && git pull`.
- Verify with `scripts/verify_pages_build.sh <owner/repo> <base-url> [page ...]`. It waits for the Pages build of `HEAD` to reach built or errored, then prints HTTP status per page. A 404 on a removed page is expected.
- Report the merged PR URL and the verified build. Do not call the deploy live from the merge alone.
