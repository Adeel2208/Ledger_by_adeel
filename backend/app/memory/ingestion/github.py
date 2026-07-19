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

    def _calculate_repo_quality(self, repo: dict) -> float:
        """Calculate quality score for a repository (0-1)."""
        score = 0.0
        
        # Stars (capped at 1000)
        stars = repo.get("stargazers_count", 0)
        score += min(0.3, stars / 1000 * 0.3)
        
        # Forks (shows real usage)
        forks = repo.get("forks_count", 0)
        score += min(0.2, forks / 100 * 0.2)
        
        # Has description (documentation)
        if repo.get("description") and len(repo.get("description", "")) > 20:
            score += 0.15
        
        # Recent activity (pushed in last 90 days)
        pushed_at = repo.get("pushed_at", "")
        if pushed_at:
            try:
                from datetime import datetime, timezone
                pushed_date = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                days_since_push = (datetime.now(timezone.utc) - pushed_date).days
                if days_since_push < 90:
                    score += 0.2
                elif days_since_push < 180:
                    score += 0.1
            except:
                pass
        
        # Has topics/tags
        if repo.get("topics") and len(repo.get("topics", [])) > 0:
            score += 0.1
        
        # Has license
        if repo.get("license"):
            score += 0.05
        
        return min(1.0, score)

    def _analyze_commit_quality(
        self, client: httpx.Client, username: str, repo_name: str
    ) -> dict:
        """Analyze commit quality for a repository."""
        commits = self._get(
            client,
            f"/repos/{username}/{repo_name}/commits",
            per_page=30
        )
        
        if not commits:
            return {"quality": "unknown", "consistency": 0.0}
        
        # Analyze commit messages
        message_lengths = []
        for commit in commits[:30]:
            msg = commit.get("commit", {}).get("message", "")
            message_lengths.append(len(msg))
        
        avg_length = sum(message_lengths) / len(message_lengths) if message_lengths else 0
        
        # Good commit messages are typically >20 chars
        quality = "high" if avg_length > 50 else "medium" if avg_length > 20 else "low"
        
        # Check consistency (commits spread over time)
        dates = []
        for commit in commits:
            date_str = commit.get("commit", {}).get("author", {}).get("date", "")
            if date_str:
                try:
                    from datetime import datetime
                    dates.append(datetime.fromisoformat(date_str.replace("Z", "+00:00")))
                except:
                    pass
        
        # Calculate consistency (std dev of commit intervals)
        consistency = 0.5  # Default
        if len(dates) >= 3:
            dates.sort()
            intervals = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
            if intervals:
                import statistics
                mean = statistics.mean(intervals)
                if mean > 0:
                    stdev = statistics.stdev(intervals) if len(intervals) > 1 else 0
                    consistency = max(0.0, min(1.0, 1.0 - (stdev / (mean + 1))))
        
        return {
            "quality": quality,
            "consistency": consistency,
            "avg_message_length": avg_length,
            "commit_count": len(commits)
        }

    def fetch(self, *, username: str, max_repos: int = 30, deep_analysis: bool = False, **_: Any) -> IngestBundle:
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

        # Per-repo signals for the top original repos (quality-scored and ranked)
        repos_with_quality = [
            (repo, self._calculate_repo_quality(repo))
            for repo in original_repos
        ]
        repos_with_quality.sort(key=lambda x: x[1], reverse=True)
        
        for repo, quality_score in repos_with_quality[:8]:
            payload = {
                "name": repo.get("name"),
                "stars": repo.get("stargazers_count"),
                "forks": repo.get("forks_count"),
                "language": repo.get("language"),
                "description": repo.get("description"),
                "pushed_at": repo.get("pushed_at"),
                "quality_score": quality_score,
                "topics": repo.get("topics", []),
                "has_license": repo.get("license") is not None,
            }
            
            # Deep analysis (commit quality) if requested
            if deep_analysis:
                try:
                    commit_analysis = self._analyze_commit_quality(client, username, repo.get("name"))
                    payload["commit_quality"] = commit_analysis
                except:
                    pass  # Skip if fails
            
            signals.append(
                RawSignal(
                    source="github",
                    record_type="github_repo",
                    payload=payload,
                    timestamp=self._parse_ts(repo.get("pushed_at")),
                    confidence=Confidence.VERIFIED,
                    external_url=repo.get("html_url"),
                    text=(
                        f"Repo {repo.get('name')} ({repo.get('language') or 'n/a'}), "
                        f"{repo.get('stargazers_count', 0)} stars, "
                        f"quality: {quality_score:.2f}: {repo.get('description') or ''}"
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
