"""Logs rows in/out for every cleaning step. Owner: Amr (issue #11).

Usage:
    log = CleaningLog("knowledge")
    df = log.step("drop missing topic_id", df, df[df.topic_id.notna()])
    log.save("ml/knowledge/cleaning_log.csv")
"""


class CleaningLog:
    def __init__(self, dataset: str) -> None:
        self.dataset = dataset
        self.rows: list[dict] = []

    def step(self, name: str, before, after, reason: str = ""):
        """Record len(before) -> len(after) for this step and return `after`."""
        raise NotImplementedError("Issue #11")

    def save(self, path: str) -> None:
        raise NotImplementedError("Issue #11")
