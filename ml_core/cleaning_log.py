"""Logs rows in/out for every cleaning step. Owner: Amr (issue #11).

Usage:
    log = CleaningLog("knowledge")
    df = log.step("drop missing topic_id", df, df[df.topic_id.notna()], reason="topic_id is required")
    log.save("ml/knowledge/cleaning_log.csv")
"""

import csv
import logging
from collections.abc import Sized
from pathlib import Path

LOGGER = logging.getLogger(__name__)
CSV_FIELDS = ("dataset", "step", "rows_before", "rows_after", "reason")


class CleaningLog:
    def __init__(self, dataset: str) -> None:
        self.dataset = dataset
        self.rows: list[dict[str, str | int]] = []

    def step[After: Sized](self, name: str, before: Sized, after: After, reason: str = "") -> After:
        """Record len(before) -> len(after) for this step and return `after`."""
        rows_before = len(before)
        rows_after = len(after)
        self.rows.append(
            {
                "dataset": self.dataset,
                "step": name,
                "rows_before": rows_before,
                "rows_after": rows_after,
                "reason": reason,
            }
        )
        LOGGER.info(
            "%s: %s | rows_before=%d rows_after=%d | reason=%s",
            self.dataset,
            name,
            rows_before,
            rows_after,
            reason,
        )
        return after

    def save(self, path: str) -> None:
        """Write the complete audit trail as UTF-8 CSV, creating parent directories."""
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)
