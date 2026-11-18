"""Server-side proxy for GitHub's public REST API.

Responses are cached so visitors never hit GitHub's anonymous rate limit,
the optional token stays on the server, and a stale copy is served if
GitHub is unavailable.
"""
import json
import logging
import urllib.error
import urllib.request
from collections import Counter

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)
API = "https://api.github.com"


def _get(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "portfolio-site",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    if settings.GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {settings.GITHUB_TOKEN}")
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))


def summarize(user, repos):
    own = [r for r in repos if not r.get("fork")]
    langs = Counter(r["language"] for r in own if r.get("language"))
    recent = sorted(own, key=lambda r: r.get("pushed_at") or "", reverse=True)[:6]
    return {
        "ok": True,
        "profile": {
            "login": user.get("login"),
            "name": user.get("name"),
            "avatar_url": user.get("avatar_url"),
            "html_url": user.get("html_url"),
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "created_at": user.get("created_at"),
        },
        "languages": [{"name": k, "count": v} for k, v in langs.most_common(8)],
        "repos": [{
            "name": r["name"],
            "description": r.get("description") or "",
            "language": r.get("language"),
            "html_url": r["html_url"],
            "stars": r.get("stargazers_count", 0),
            "pushed_at": r.get("pushed_at"),
        } for r in recent],
        "total_stars": sum(r.get("stargazers_count", 0) for r in own),
    }


def get_github_summary(username):
    if not username:
        return {"ok": False, "error": "No GitHub username configured."}
    key, stale_key = f"gh:summary:{username}", f"gh:summary:stale:{username}"
    data = cache.get(key)
    if data:
        return data
    try:
        user = _get(f"/users/{username}")
        repos = _get(f"/users/{username}/repos?per_page=100&sort=pushed")
        data = summarize(user, repos)
        cache.set(key, data, settings.GITHUB_CACHE_SECONDS)
        cache.set(stale_key, data, 60 * 60 * 24 * 7)
        return data
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        logger.warning("GitHub API unavailable: %s", exc)
        stale = cache.get(stale_key)
        if stale:
            return {**stale, "stale": True}
        # Short negative cache so a GitHub outage doesn't slow every request.
        fail = {"ok": False, "error": "GitHub is temporarily unavailable."}
        cache.set(key, fail, 120)
        return fail
