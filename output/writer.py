from __future__ import annotations

import json
import re
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from models.article import ConsolidatedArticle, DailyDigest, Sentiment
from models.politician import ImpactRecord, PoliticianProfile

MAX_IMPACT_HISTORY = 365  # cap per-politician history to ~1 year of records

# Titles to strip before slugging politician names, preventing profile fragmentation.
# e.g. "Senator Joel Villanueva" and "Sen. Joel Villanueva" → same slug.
_TITLE_RE = re.compile(
    r"^(?:(?:former|ex)[- ])?"
    r"(?:sen\.?|rep\.?|cong\.?|sec\.?|dr\.?|atty\.?|gen\.?|brig\.?\s*gen\.?|"
    r"col\.?|gov\.?|mayor|president|pres\.?|speaker|dep\.?\s*speaker|"
    r"vice[- ]president|vp|secretary|undersecretary|usec\.?|asec\.?)\s+",
    re.IGNORECASE,
)


class DataWriter:
    """Writes classified news data to the `data` branch of this repository.

    On Jules' VM, existing git credentials are used — no token needed.
    Pass github_repo + github_pat only for local development outside Jules.

    Assumes the `data` branch already exists on the remote (startup.sh creates
    it on first run).
    """

    def __init__(
        self,
        github_repo: str | None = None,
        github_pat: str | None = None,
    ) -> None:
        if github_repo and github_pat:
            self._remote = (
                f"https://x-access-token:{github_pat}@github.com/{github_repo}.git"
            )
        else:
            self._remote = "origin"

    def write_daily(self, digest: DailyDigest) -> None:
        with self._data_worktree() as data_path:
            # Idempotency guard: skip if today's digest already exists
            daily_file = data_path / "daily" / f"{digest.date}.json"
            if daily_file.exists():
                print(f"  Digest for {digest.date} already exists — skipping write.")
                return

            print(f"  Writing daily digest for {digest.date}...")
            self._write_daily_json(data_path, digest)
            self._update_politician_profiles(data_path, digest)
            self._update_sector_files(data_path, digest)
            self._commit_and_push(data_path, digest.date, digest.topic_count)

    # ------------------------------------------------------------------
    # File writers
    # ------------------------------------------------------------------

    def _write_daily_json(self, data_path: Path, digest: DailyDigest) -> None:
        daily_dir = data_path / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        out = daily_dir / f"{digest.date}.json"
        out.write_text(
            json.dumps(digest.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"    Wrote {out.name}")

    def _update_politician_profiles(self, data_path: Path, digest: DailyDigest) -> None:
        pol_dir = data_path / "politicians"
        pol_dir.mkdir(parents=True, exist_ok=True)

        mentions: dict[str, list] = {}
        for topic in digest.topics:
            if not topic.classification:
                continue
            for pm in topic.classification.politicians:
                slug = _to_slug(pm.name)
                mentions.setdefault(slug, []).append((topic, pm))

        for slug, topic_mentions in mentions.items():
            profile_path = pol_dir / f"{slug}.json"
            profile = None
            if profile_path.exists():
                try:
                    profile = PoliticianProfile.model_validate(
                        json.loads(profile_path.read_text("utf-8"))
                    )
                except Exception:
                    profile = None

            if profile is None:
                _, first_pm = topic_mentions[0]
                profile = PoliticianProfile(
                    slug=slug,
                    name=first_pm.name,
                    position=first_pm.position,
                    party=first_pm.party,
                    branch=_infer_branch(first_pm.position),
                    last_updated=datetime.now(timezone.utc),
                )

            for topic, pm in topic_mentions:
                primary = topic.sources[0] if topic.sources else None
                profile.impact_history.append(
                    ImpactRecord(
                        date=digest.date,
                        article_id=str(topic.id),
                        article_title=topic.topic,
                        article_url=primary.url if primary else "",
                        impact=pm.impact,
                        reason=pm.reason,
                        source=primary.source if primary else "unknown",
                    )
                )
                if pm.impact == Sentiment.positive:
                    profile.positive_count += 1
                elif pm.impact == Sentiment.negative:
                    profile.negative_count += 1
                else:
                    profile.neutral_count += 1

            # Cap history to avoid unbounded file growth
            profile.impact_history = profile.impact_history[-MAX_IMPACT_HISTORY:]
            profile.last_updated = datetime.now(timezone.utc)

            profile_path.write_text(
                json.dumps(profile.model_dump(mode="json"), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        print(f"    Updated {len(mentions)} politician profile(s)")

    def _update_sector_files(self, data_path: Path, digest: DailyDigest) -> None:
        sectors_dir = data_path / "sectors"
        sectors_dir.mkdir(parents=True, exist_ok=True)

        sector_topics: dict[str, list[ConsolidatedArticle]] = {}
        for topic in digest.topics:
            if not topic.classification:
                continue
            for sector in topic.classification.affected_sectors:
                s = sector.value if hasattr(sector, "value") else str(sector)
                sector_topics.setdefault(s, []).append(topic)

        for sector, topics in sector_topics.items():
            sector_path = sectors_dir / f"{sector}.json"
            existing: list = []
            if sector_path.exists():
                try:
                    existing = json.loads(sector_path.read_text("utf-8")).get("topics", [])
                except Exception:
                    pass

            new_entries = [
                {"date": digest.date, "topic": t.model_dump(mode="json")}
                for t in topics
            ]
            combined = (new_entries + existing)[:300]

            sector_path.write_text(
                json.dumps({"sector": sector, "topics": combined}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        print(f"    Updated {len(sector_topics)} sector file(s)")

    # ------------------------------------------------------------------
    # Git operations
    # ------------------------------------------------------------------

    @contextmanager
    def _data_worktree(self) -> Generator[Path, None, None]:
        worktree = Path("_data_wt")

        # Remove any stale worktree from a previous crashed run before starting
        _run(["git", "worktree", "remove", str(worktree), "--force"], check=False)
        _run(["git", "worktree", "prune"], check=False)

        try:
            _run(["git", "fetch", "origin", "data"], check=False)
            # Create local tracking branch if it doesn't exist (e.g. fresh clone on Jules VM)
            if not _run(["git", "branch", "--list", "data"], check=False).stdout.strip():
                _run(["git", "branch", "--track", "data", "origin/data"])
            _run(["git", "worktree", "add", str(worktree), "data"])
            yield worktree
        finally:
            _run(["git", "worktree", "remove", str(worktree), "--force"], check=False)

    def _commit_and_push(self, data_path: Path, date_str: str, topic_count: int) -> None:
        _run(["git", "-C", str(data_path), "config", "user.email", "jules-bot@google.com"])
        _run(["git", "-C", str(data_path), "config", "user.name", "Jules (automated)"])
        _run(["git", "-C", str(data_path), "add", "."])

        commit_msg = f"data: {date_str} — {topic_count} topics"
        result = _run(
            ["git", "-C", str(data_path), "commit", "-m", commit_msg],
            check=False,
        )

        stdout = result.stdout + result.stderr
        if result.returncode != 0:
            if "nothing to commit" in stdout or "nothing added to commit" in stdout:
                print("    Nothing new to commit — data branch is already up to date.")
                return
            print(f"  git commit failed:\n  {stdout.strip()}", file=sys.stderr)
            result.check_returncode()

        _run(["git", "-C", str(data_path), "push", self._remote, "data"])
        print("    Pushed to data branch.")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _to_slug(name: str) -> str:
    # Strip honorifics/titles so "Sen. Villanueva" and "Senator Villanueva"
    # map to the same politician profile.
    name = _TITLE_RE.sub("", name.strip())
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _infer_branch(position: str) -> str:
    p = position.lower()
    if any(x in p for x in ["senator", "representative", "congressman", "speaker", "deputy speaker"]):
        return "legislative"
    if any(x in p for x in ["justice", "judge", "chief justice", "associate justice"]):
        return "judicial"
    return "executive"


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        print(f"  git error: {' '.join(cmd)}\n  {result.stderr.strip()}", file=sys.stderr)
        result.check_returncode()
    return result
