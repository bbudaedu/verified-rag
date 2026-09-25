"""Exit codes: 0 pass, 1 problems found, 2 the check itself could not run.

Keeping 1 and 2 apart matters when this runs as a CI gate: a broken tool
must not look like either a clean wiki or a dirty one.
"""

import argparse
import json
import sys
from pathlib import Path

from .corpus import build_corpus, load_corpus
from .coverage import coverage, wiki_files
from .retrieval import STRATEGIES, Index, mrr, recall_at_k
from .verify import verify_text


def cmd_corpus(a) -> int:
    n = build_corpus(Path(a.zip), a.law, Path(a.out))
    print(f"wrote {n} articles to {a.out}")
    return 0


def _wiki_or_none(path: str) -> list[Path] | None:
    files = wiki_files(Path(path)) if Path(path).exists() else []
    if not files:
        print(f"error: wiki not found or has no .md files: {path}", file=sys.stderr)
        return None
    return files


def cmd_verify(a) -> int:
    files = _wiki_or_none(a.wiki)
    if files is None:
        return 2
    docs = load_corpus(Path(a.corpus))
    if not docs:
        print(f"error: no articles under {a.corpus}", file=sys.stderr)
        return 2
    report = []
    for f in files:
        report += [(f, c) for c in verify_text(f.read_text(encoding="utf-8"), docs)]
    if not report:
        print("error: no checkable claims found -- nothing was verified", file=sys.stderr)
        return 2
    bad = [(f, c) for f, c in report if c.status != "ok"]
    for f, c in bad:
        cited = ", ".join(c.cited) or "(uncited)"
        print(f"{c.status.upper():14} {f.name}: 「{c.text}」 cited: {cited}")
    ok = len(report) - len(bad)
    print(f"\n{ok}/{len(report)} claims sourced verbatim; {len(bad)} flagged")
    return 1 if bad else 0


def cmd_coverage(a) -> int:
    if _wiki_or_none(a.wiki) is None:
        return 2
    r = coverage(Path(a.wiki), Path(a.corpus))
    if not r.total:
        print(f"error: no articles under {a.corpus}", file=sys.stderr)
        return 2
    print(f"cited {r.cited}/{r.total} articles ({r.ratio:.1%})")
    if r.dangling:
        print(f"{len(r.dangling)} citations to articles not in the corpus: {', '.join(r.dangling)}")
    if r.ratio < a.min:
        print(f"below minimum {a.min:.0%}; largest never-cited articles:")
        for d in r.never_cited[:10]:
            print(f"  {d}")
        return 1
    return 0


def cmd_eval(a) -> int:
    queries = json.loads(Path(a.queries).read_text(encoding="utf-8"))
    idx = Index.build(Path(a.corpus))
    print(f"{len(queries)} queries\n\n| strategy | Hit@1 | Hit@3 | MRR |\n|---|---|---|---|")
    for s in STRATEGIES:
        runs = [(idx.search(q["q"], s), set(q["expected"])) for q in queries]
        print(f"| {s} | {recall_at_k(runs, 1):.1%} | {recall_at_k(runs, 3):.1%} | {mrr(runs):.3f} |")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="verified-rag")
    sub = p.add_subparsers(required=True)

    c = sub.add_parser("corpus", help="build per-article corpus from the MOJ bulk ZIP")
    c.add_argument("--zip", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--law", action="append", required=True)
    c.set_defaults(fn=cmd_corpus)

    v = sub.add_parser("verify", help="precision: is every quoted claim in its cited article?")
    v.add_argument("wiki")
    v.add_argument("--corpus", required=True)
    v.set_defaults(fn=cmd_verify)

    g = sub.add_parser("coverage", help="recall: how much of the corpus is ever cited?")
    g.add_argument("wiki")
    g.add_argument("--corpus", required=True)
    g.add_argument("--min", type=float, default=0.3)
    g.set_defaults(fn=cmd_coverage)

    e = sub.add_parser("eval", help="compare Chinese BM25 query strategies")
    e.add_argument("--corpus", required=True)
    e.add_argument("--queries", required=True)
    e.set_defaults(fn=cmd_eval)

    a = p.parse_args(argv)
    try:
        return a.fn(a)
    except (OSError, ValueError) as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
