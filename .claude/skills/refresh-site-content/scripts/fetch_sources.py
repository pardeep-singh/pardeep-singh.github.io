#!/usr/bin/env python3
"""Fetch GitHub, Kaggle and Coursera activity and report what the site is missing.

Usage:
    python3 -I fetch_sources.py --site <site-root> [--since YYYY-MM-DD] [--out data.json]

Prints a plain-text report to stdout. Every item carries `on_site` (its URL appears in
one of the site's *.html files) and `excluded` (it matches a line in ../exclude.txt).
`--since` defaults to the date of the last commit that touched a page in the site.
Each source fails independently; errors are listed at the top of the report.
"""
import argparse
import datetime as dt
import glob
import http.cookiejar
import json
import os
import re
import subprocess
import sys
import urllib.request

GITHUB_USER = "pardeep-singh"
KAGGLE_USER = "pardeep19singh"
COURSERA_PROFILE = "https://www.coursera.org/learner/pardeep-singh"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
EXCLUDE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "exclude.txt")


# --- GitHub (via the authenticated gh CLI) -------------------------------------------

def gh_api(path, *fields):
    cmd = ["gh", "api", "-X", "GET", path]
    for f in fields:
        cmd += ["-f", f]
    return json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout)


def fetch_github():
    prs = []
    for page in range(1, 11):
        res = gh_api("search/issues", f"q=author:{GITHUB_USER} is:pr -user:{GITHUB_USER}",
                     "per_page=100", f"page={page}")
        for it in res["items"]:
            merged = (it.get("pull_request") or {}).get("merged_at")
            prs.append({
                "repo": it["repository_url"].split("/repos/", 1)[1],
                "title": it["title"],
                "url": it["html_url"],
                "state": "merged" if merged else it["state"],
                "date": (merged or it["created_at"])[:10],
            })
        if len(prs) >= res["total_count"] or not res["items"]:
            break
    repos = [{
        "name": r["name"],
        "url": r["html_url"],
        "description": r["description"] or "",
        "date": r["created_at"][:10],
        "pushed": r["pushed_at"][:10],
    } for r in gh_api(f"users/{GITHUB_USER}/repos", "per_page=100") if not r["fork"]]
    return {"prs": prs, "repos": repos}


# --- Kaggle (public JSON endpoints; the internal API needs the XSRF cookie) -----------

class Kaggle:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.opener.addheaders = [("User-Agent", UA)]
        self.opener.open("https://www.kaggle.com/", timeout=30).read()
        self.xsrf = next((c.value for c in self.jar if c.name == "XSRF-TOKEN"), "")

    def get(self, path):
        with self.opener.open("https://www.kaggle.com/api/v1/" + path, timeout=30) as r:
            return json.load(r)

    def rpc(self, method, body):
        req = urllib.request.Request(
            "https://www.kaggle.com/api/i/" + method, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "x-xsrf-token": self.xsrf}, method="POST")
        with self.opener.open(req, timeout=30) as r:
            return json.load(r)


def fetch_kaggle():
    k = Kaggle()
    prof = k.rpc("users.ProfileService/GetProfile", {"userName": KAGGLE_USER})
    tiers = {}
    for a in prof.get("achievementSummaries", []):
        kind = a["summaryType"].rsplit("_", 1)[-1].lower()
        tiers[kind] = {key: a.get(key) for key in
                       ("tier", "rankCurrent", "rankHighest", "rankOutOf",
                        "totalGoldMedals", "totalSilverMedals", "totalBronzeMedals")}
    stats = {
        "tiers": tiers,
        "notebooks": prof.get("totalKernels"),
        "datasets": prof.get("totalDatasets"),
        "competitions": prof.get("totalCompetitions"),
        "models": prof.get("totalModels"),
    }

    notebooks, token = [], ""
    while True:
        req = {"userId": prof["userId"], "sortBy": "DATE_RUN", "pageSize": 100, "group": "PROFILE"}
        if token:
            req["pageToken"] = token
        res = k.rpc("kernels.KernelsService/ListKernels",
                    {"kernelFilterCriteria": {"search": "", "listRequest": req}})
        for x in res.get("kernels", []):
            notebooks.append({
                "title": x["title"],
                "url": "https://www.kaggle.com" + x["scriptUrl"],
                "votes": x.get("totalVotes", 0),
                "medal": (x.get("medal") or "").lower() or None,
                "date": (x.get("lastRunTime") or "")[:10],
            })
        token = res.get("nextPageToken")
        if not token:
            break

    datasets = [{
        "title": d["title"],
        "subtitle": d.get("subtitle") or "",
        "url": d["url"],
        "downloads": d.get("downloadCount", 0),
        "votes": d.get("voteCount", 0),
        "date": d["lastUpdated"][:10],
    } for d in k.get(f"datasets/list?user={KAGGLE_USER}&page=1")]

    models = [{
        "title": m["title"],
        "url": m["url"],
        "date": (m.get("updateTime") or "")[:10],
    } for m in k.get(f"models/list?owner={KAGGLE_USER}").get("models", [])]

    return {"stats": stats, "notebooks": notebooks, "datasets": datasets, "models": models}


# --- Coursera (accomplishments are embedded as JSON in the server-rendered profile) ---

def fetch_coursera():
    req = urllib.request.Request(COURSERA_PROFILE, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    dec = json.JSONDecoder()
    found = {}
    for m in re.finditer(r'\{"__typename":"LearnerProfile_(Specialization|Course)"', html):
        try:
            obj, _ = dec.raw_decode(html, m.start())
        except ValueError:
            continue
        key = (m.group(1), obj.get("name"))
        prev = found.get(key)
        # The same accomplishment can appear twice; keep the copy with a certificate code.
        if prev is None or (not prev.get("verifyCode") and obj.get("verifyCode")):
            found[key] = obj
    certs = []
    for (kind, name), obj in found.items():
        code = obj.get("verifyCode") or ""
        path = "specialization" if kind == "Specialization" else "verify"
        certs.append({
            "kind": kind.lower(),
            "name": name,
            "issuer": ", ".join(p["name"] for p in obj.get("partners") or []) or None,
            "url": f"https://www.coursera.org/account/accomplishments/{path}/{code}" if code else None,
            "date": (obj.get("completionDate") or "")[:10],
        })
    if not certs:
        raise RuntimeError("no accomplishments found: the profile is missing or private, or the page layout changed")
    return {"certificates": sorted(certs, key=lambda c: c["date"], reverse=True)}


# --- Comparison with the site ---------------------------------------------------------

def site_text(site):
    return "\n".join(open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(site, "*.html")))


def load_excludes():
    if not os.path.exists(EXCLUDE_FILE):
        return []
    lines = (l.split("#", 1)[0].strip() for l in open(EXCLUDE_FILE, encoding="utf-8"))
    return [l for l in lines if l]


def default_since(site):
    out = subprocess.run(["git", "-C", site, "log", "-1", "--format=%cs", "--", "*.html"],
                         capture_output=True, text=True).stdout.strip()
    return out or (dt.date.today() - dt.timedelta(days=90)).isoformat()


def annotate(items, text, excludes):
    for it in items:
        url = it.get("url") or ""
        it["on_site"] = bool(url) and url in text
        it["excluded"] = any(e in url or e == it.get("name") for e in excludes)


def stale_kaggle_stats(stats, text):
    """Return (label, current value) pairs whose current value the site does not quote."""
    checks = []
    for kind, label in (("datasets", "Datasets"), ("notebooks", "Notebooks")):
        t = stats["tiers"].get(kind)
        if t:
            checks.append((f"{label} tier", t["tier"].title(), f"{label} {t['tier'].title()}"))
            if t.get("rankHighest"):
                checks.append((f"{label} highest rank", f"#{t['rankHighest']}", f"#{t['rankHighest']}"))
    for key in ("notebooks", "datasets", "competitions"):
        if stats.get(key) is not None:
            checks.append((f"total {key}", str(stats[key]), f"{stats[key]} {key}"))
    return [(label, value) for label, value, needle in checks if needle not in text]


def lately_block(site):
    """Text of the "Lately" list on index.html, lowercased; empty if the section is missing."""
    html = open(os.path.join(site, "index.html"), encoding="utf-8").read()
    m = re.search(r"<h2>Lately</h2>(.*?)</ul>", html, re.S)
    return m.group(1).lower() if m else ""


def lately_candidates(data, lately):
    """Newest notable item per source, and whether the Lately list already mentions it.

    Lately is separate from the other pages: an item can be linked from experience.html
    or projects.html and still be missing from Lately."""
    rows = []
    cs = data.get("coursera")
    if cs and cs["certificates"]:
        c = cs["certificates"][0]
        rows.append(("Coursera", c["date"], c["name"], (c["url"] or "").lower() in lately or c["name"].lower() in lately))
    gh = data.get("github")
    if gh:
        merged = [p for p in gh["prs"] if p["state"] == "merged"]
        if merged:
            p = max(merged, key=lambda p: p["date"])
            short = p["repo"].split("/", 1)[1]
            rows.append(("Open source", p["date"], p["repo"], short.lower() in lately))
        mine = [r for r in gh["repos"] if not r["excluded"]]
        if mine:
            r = max(mine, key=lambda r: r["date"])
            rows.append(("Own repo", r["date"], r["name"], r["url"].lower() in lately))
    kg = data.get("kaggle")
    if kg:
        medals = [n for n in kg["notebooks"] if n["medal"] and not n["excluded"]]
        if medals:
            n = max(medals, key=lambda n: n["date"])
            rows.append(("Kaggle notebook", n["date"], n["title"], n["url"].lower() in lately))
        if kg["datasets"]:
            d = max(kg["datasets"], key=lambda d: d["date"])
            rows.append(("Kaggle dataset", d["date"], d["title"], d["url"].lower() in lately))
    return sorted(rows, key=lambda r: r[1], reverse=True)


def report(data, since, errors):
    lines = [f"Changes since {since}", ""]
    for src, err in errors.items():
        lines.append(f"ERROR {src}: {err}")
    if errors:
        lines.append("")

    def new(items):
        return [i for i in items if not i["on_site"] and not i["excluded"] and i.get("date", "") >= since]

    gh = data.get("github")
    if gh:
        lines.append("== GitHub pull requests, merged or open (not linked on the site)")
        by_repo = {}
        for pr in new([p for p in gh["prs"] if p["state"] != "closed"]):
            by_repo.setdefault(pr["repo"], []).append(pr)
        for repo, prs in sorted(by_repo.items()):
            all_repo = [p for p in gh["prs"] if p["repo"] == repo]
            merged = sum(p["state"] == "merged" for p in all_repo)
            lines.append(f"{repo}  (all time: {merged} merged, "
                         f"{sum(p['state'] == 'open' for p in all_repo)} open)")
            for p in sorted(prs, key=lambda p: p["date"], reverse=True):
                lines.append(f"  {p['date']}  {p['state']:<6}  {p['title']}  {p['url']}")
        lines.append("== GitHub repos (own, not on the site)")
        for r in new(gh["repos"]):
            lines.append(f"  {r['date']}  {r['name']}  {r['description']}  {r['url']}")
        lines.append("")

    kg = data.get("kaggle")
    if kg:
        lines.append("== Kaggle stats the site does not quote (may be stale)")
        for label, value in stale_kaggle_stats(kg["stats"], data["_site_text"]):
            lines.append(f"  {label}: now {value}")
        for section in ("notebooks", "datasets", "models"):
            lines.append(f"== Kaggle {section} (not on the site)")
            for i in new(kg[section]):
                extra = f"votes {i['votes']}" if "votes" in i else ""
                if i.get("medal"):
                    extra += f", {i['medal']}"
                if "downloads" in i:
                    extra += f", {i['downloads']} downloads"
                lines.append(f"  {i['date']}  {i['title']}  [{extra.strip(', ')}]  {i['url']}")
        lines.append("")

    lines.append("== Lately on index.html: newest item per source (all dates, not just since)")
    for source, date, name, present in data["_lately"]:
        lines.append(f"  {date}  {source:<16} {'in Lately ' if present else 'MISSING   '} {name}")
    lines.append("")

    cs = data.get("coursera")
    if cs:
        lines.append("== Coursera certificates (not on the site)")
        for c in new(cs["certificates"]):
            lines.append(f"  {c['date']}  {c['kind']:<14}  {c['name']}  "
                         f"[{c['issuer'] or 'issuer not given'}]  {c['url'] or 'no certificate'}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help="site root containing the *.html pages")
    ap.add_argument("--since", help="only report items dated on or after YYYY-MM-DD")
    ap.add_argument("--out", help="write the full annotated data as JSON here")
    args = ap.parse_args()

    text = site_text(args.site)
    excludes = load_excludes()
    since = args.since or default_since(args.site)
    data, errors = {}, {}
    for name, fn in (("github", fetch_github), ("kaggle", fetch_kaggle), ("coursera", fetch_coursera)):
        try:
            data[name] = fn()
        except Exception as e:  # report and continue with the other sources
            errors[name] = f"{type(e).__name__}: {e}"

    for src in data.values():
        for key, items in src.items():
            if isinstance(items, list):
                annotate(items, text, excludes)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"since": since, "errors": errors, **data}, f, indent=2)
    data["_site_text"] = text
    data["_lately"] = lately_candidates(data, lately_block(args.site))
    print(report(data, since, errors))
    return 1 if len(errors) == 3 else 0


if __name__ == "__main__":
    sys.exit(main())
