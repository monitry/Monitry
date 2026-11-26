"""Builds the multi-screen monitoring report — a per-screen activity log
accumulated across capture cycles, plus a human-readable summary.
"""
from __future__ import annotations

import datetime
import time


class RoomReport:
    def __init__(self):
        self._entries: dict[str, list[dict]] = {}

    def log(
        self,
        screen_id: str,
        activity: str,
        on_task: bool | None = None,
        timestamp: float | None = None,
    ) -> None:
        ts = timestamp if timestamp is not None else time.time()
        self._entries.setdefault(screen_id, []).append({
            "timestamp": ts,
            "activity": activity,
            "on_task": on_task,
        })

    def screens(self) -> list[str]:
        """Screen ids, ordered by first-seen time (not alphabetically —
        'screen-2' can appear before 'screen-10')."""
        return sorted(self._entries.keys(), key=lambda sid: self._entries[sid][0]["timestamp"])

    def entries_for(self, screen_id: str) -> list[dict]:
        return list(self._entries.get(screen_id, []))

    def summary_for(self, screen_id: str) -> dict:
        entries = self._entries.get(screen_id, [])
        if not entries:
            return {
                "screen_id": screen_id, "entry_count": 0, "first_seen": None,
                "last_seen": None, "duration_seconds": 0.0, "pct_on_task": None,
            }

        first_seen = entries[0]["timestamp"]
        last_seen = entries[-1]["timestamp"]
        judged = [e for e in entries if e["on_task"] is not None]
        pct_on_task = (sum(1 for e in judged if e["on_task"]) / len(judged) * 100) if judged else None

        return {
            "screen_id": screen_id,
            "entry_count": len(entries),
            "first_seen": first_seen,
            "last_seen": last_seen,
            "duration_seconds": max(0.0, last_seen - first_seen),
            "pct_on_task": pct_on_task,
        }

    def to_dict(self) -> dict:
        return {
            "screens": {
                screen_id: {
                    "summary": self.summary_for(screen_id),
                    "entries": self.entries_for(screen_id),
                }
                for screen_id in self.screens()
            }
        }

    def to_markdown(self) -> str:
        if not self._entries:
            return "# Room Monitoring Report\n\nNo screens were observed.\n"

        lines = ["# Room Monitoring Report", ""]
        for screen_id in self.screens():
            summary = self.summary_for(screen_id)
            lines.append(f"## {screen_id}")

            duration_min = summary["duration_seconds"] / 60
            lines.append(f"- Observed {summary['entry_count']} time(s) over {duration_min:.1f} min")
            if summary["pct_on_task"] is not None:
                lines.append(f"- {summary['pct_on_task']:.0f}% on task")
            lines.append("")

            for entry in self.entries_for(screen_id):
                ts_str = datetime.datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M:%S")
                tag = ""
                if entry["on_task"] is True:
                    tag = " [on task]"
                elif entry["on_task"] is False:
                    tag = " [OFF TASK]"
                lines.append(f"- `{ts_str}`{tag} {entry['activity']}")
            lines.append("")

        return "\n".join(lines)
