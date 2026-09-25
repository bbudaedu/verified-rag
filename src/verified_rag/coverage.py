"""Recall, not just precision: how much of the corpus the wiki ever cites.

A wiki can have zero fabricated claims and still ignore 99% of its sources.
"""

from dataclasses import dataclass
from pathlib import Path

from .corpus import load_corpus
from .verify import CITE


@dataclass
class Coverage:
    cited: int
    total: int
    never_cited: list[str]  # largest first: the likeliest missing knowledge
    dangling: list[str]  # cited but not in the corpus

    @property
    def ratio(self) -> float:
        return self.cited / self.total if self.total else 0.0


def wiki_files(wiki: Path) -> list[Path]:
    return [wiki] if wiki.is_file() else sorted(wiki.rglob("*.md"))


def coverage(wiki: Path, corpus: Path) -> Coverage:
    docs = load_corpus(corpus)
    cited = set()
    for f in wiki_files(wiki):
        cited |= set(CITE.findall(f.read_text(encoding="utf-8")))
    dangling = sorted(cited - docs.keys())
    cited &= docs.keys()
    never = sorted((d for d in docs if d not in cited), key=lambda d: -len(docs[d]))
    return Coverage(len(cited), len(docs), never, dangling)
