"""GitHub connector (FR-5, D1): commit quality > quantity, repos, stars, contributions.

Primary outbound signal for technical founders. Emits quality-weighted signals
(not raw counts) so a thoughtful builder outscores a star-farmer. GitHub-sourced
identity is marked `verified` confidence (it's an authoritative public record).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.memory.ingestion.base import BaseConnector, IngestBundle, RawSignal
from app.schemas.common import Confidence

_API = "https://api.github.com"


class GitHubConnector(BaseConnector):
    name = "github"

    def __init__(self) -> None:
        token = get_settings().github_token
        self._headers = {"Accept": "application/vnd.github+json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"

    def _get(self, client: httpx.Client, path: str, **params: Any) -> Any:
        resp = client.get(f"{_API}{path}", params=params, headers=self._headers, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def fetch(self, *, username: str, max_repos: int = 30, **_: Any) -> IngestBundle:
        with httpx.Client() as client:
            user = self._get(client, f"/users/{username}")
            if user is None:
                return IngestBundle(signals=[], identity={"github_handle": username})

            repos = (
                self._get(
                    client,
                    f"/users/{username}/repos",
                    per_page=max_repos,
                    sort="pushed",
                    type="owner",
                )
                or []
            )

        signals: list[RawSignal] = []
        now = self._parse_ts(user.get("updated_at"))

        # Profile-level signal.
        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        original_repos = [r for r in repos if not r.get("fork")]
        signals.append(
            RawSignal(
                source="github",
                record_type="github_profile",
                payload={
                    "followers": user.get("followers"),
                    "public_repos": user.get("public_repos"),
                    "original_repos": len(original_repos),
                    "total_stars": total_stars,
                    "account_created": user.get("created_at"),
                    "bio": user.get("bio"),
                },
                timestamp=now,
                confidence=Confidence.VERIFIED,
                external_url=user.get("html_url"),
                text=(
                    f"GitHub {username}: {user.get('followers', 0)} followers, "
                    f"{len(original_repos)} original repos, {total_stars} stars. "
                    f"Bio: {user.get('bio') or 'n/a'}"
                ),
                identity={"github_handle": username, "name": user.get("name")},
            )
        )

        # Per-repo signals for the top original repos (quality proxy: stars + recency + language).
        top = sorted(original_repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)
        for repo in top[:8]:
            signals.append(
                RawSignal(
                    source="github",
                    record_type="github_repo",
                    payload={
                        "name": repo.get("name"),
                        "stars": repo.get("stargazers_count"),
                        "forks": repo.get("forks_count"),
                        "language": repo.get("language"),
                        "description": repo.get("description"),
                        "pushed_at": repo.get("pushed_at"),
                    },
                    timestamp=self._parse_ts(repo.get("pushed_at")),
                    confidence=Confidence.VERIFIED,
                    external_url=repo.get("html_url"),
                    text=(
                        f"Repo {repo.get('name')} ({repo.get('language') or 'n/a'}), "
                        f"{repo.get('stargazers_count', 0)} stars: {repo.get('description') or ''}"
                    ),
                )
            )

        return IngestBundle(
            signals=signals,
            identity={
                "github_handle": username,
                "name": user.get("name"),
                "email": user.get("email"),
            },
        )

    @staticmethod
    def _parse_ts(value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
