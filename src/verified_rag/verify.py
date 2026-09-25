"""Check each concrete claim in a wiki against the article it cites.

Only verbatim-checkable claims are extracted: quoted statute text 「…」 and
monetary amounts. Narrative sentences are not checked -- string matching
cannot judge them, and flooding the report with false positives teaches
people to ignore it.
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .corpus import load_corpus

CITE = re.compile(r"\[\[([^\]]+)\]\]")
QUOTE = re.compile(r"「(.+?)」")
# Chinese numerals only: statutes never use Arabic digits for amounts.
_AMT = r"[零〇一二兩三四五六七八九十百千萬億]{1,20}元"
MONEY = re.compile(rf"新[臺台]幣{_AMT}(?:以上{_AMT}以下|以上|以下)?")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")
# Shorter fragments match somewhere in any legal corpus; no signal.
MIN_CLAIM_CHARS = 4


@dataclass(frozen=True)
class Claim:
    text: str
    status: str  # ok | absent | misattributed | uncited | dangling
    cited: tuple[str, ...]


def norm(s: str) -> str:
    # 台/臺 are interchangeable in everyday writing; statutes use 臺.
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", s)).replace("台", "臺")


def extract_claims(text: str) -> list[str]:
    found = QUOTE.findall(text) + MONEY.findall(text)
    out = []
    for c in (c.strip() for c in found):
        if len(norm(c)) >= MIN_CLAIM_CHARS and c not in out:
            out.append(c)
    return out


def scopes(md: str) -> list[str]:
    """A citation covers its paragraph, or its own list item inside a list."""
    out = []
    for block in re.split(r"\n\s*\n", md):
        items: list[str] = []
        for line in block.splitlines():
            if LIST_ITEM.match(line) or not items:
                items.append(line)
            else:
                items[-1] += "\n" + line
        out += items
    return out


def verify_text(md: str, corpus: Path | dict[str, str]) -> list[Claim]:
    docs = load_corpus(corpus) if isinstance(corpus, Path) else corpus
    normed = {k: norm(v) for k, v in docs.items()}
    report = []
    for scope in scopes(md):
        cites = CITE.findall(scope)
        valid = tuple(c for c in cites if c in normed)
        report += [Claim(c, "dangling", (c,)) for c in cites if c not in normed]
        for text in extract_claims(CITE.sub("", scope)):
            n = norm(text)
            if valid and any(n in normed[c] for c in valid):
                status = "ok"
            elif any(n in v for v in normed.values()):
                status = "misattributed" if valid else "uncited"
            else:
                status = "absent"
            report.append(Claim(text, status, valid))
    return report
