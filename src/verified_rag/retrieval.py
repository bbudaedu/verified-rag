"""BM25 over Chinese text via SQLite FTS5, with three query strategies.

FTS5's default tokenizer does not segment Chinese, so text is pre-split into
character bigrams (or single characters) and stored space-separated.
"""

import re
import sqlite3
import unicodedata
from pathlib import Path

from .corpus import load_corpus

RUN = re.compile(r"[㐀-鿿豈-﫿]+|[A-Za-z0-9]+")
STRATEGIES = ("bigram-and", "bigram-or", "char-or")


def tokens(text: str, mode: str) -> list[str]:
    out = []
    for run in RUN.findall(unicodedata.normalize("NFKC", text)):
        if run.isascii():
            out.append(run.lower())
        elif mode == "char" or len(run) == 1:
            out += list(run)
        else:
            out += [run[i:i + 2] for i in range(len(run) - 1)]
    return out


class Index:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    @classmethod
    def build(cls, corpus: Path) -> "Index":
        db = sqlite3.connect(":memory:")
        for mode in ("bigram", "char"):
            db.execute(f"CREATE VIRTUAL TABLE {mode} USING fts5(id UNINDEXED, body)")
            db.executemany(
                f"INSERT INTO {mode} VALUES (?, ?)",
                [(k, " ".join(tokens(v, mode))) for k, v in load_corpus(corpus).items()],
            )
        return cls(db)

    def search(self, query: str, strategy: str, k: int = 10) -> list[str]:
        mode, join = strategy.split("-")
        terms = list(dict.fromkeys(tokens(query, mode)))
        if not terms:
            return []
        expr = f" {join.upper()} ".join(f'"{t}"' for t in terms)
        rows = self.db.execute(
            f"SELECT id FROM {mode} WHERE {mode} MATCH ? ORDER BY rank LIMIT ?", (expr, k)
        )
        return [r[0] for r in rows]


def _first_hit(ranked: list[str], expected: set[str]) -> int | None:
    return next((i for i, d in enumerate(ranked) if d in expected), None)


# Hit@k: any expected article in the top k. With several expected articles
# this is looser than "all of them in the top k"; the README says which.
def recall_at_k(runs: list[tuple[list[str], set[str]]], k: int) -> float:
    hits = [_first_hit(r, e) for r, e in runs]
    return sum(h is not None and h < k for h in hits) / len(runs)


def mrr(runs: list[tuple[list[str], set[str]]]) -> float:
    hits = [_first_hit(r, e) for r, e in runs]
    return sum(1 / (h + 1) for h in hits if h is not None) / len(runs)
