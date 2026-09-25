from verified_rag.coverage import coverage


def test_coverage_counts_distinct_cited_articles(corpus, tmp_path):
    wiki = tmp_path / "wiki"
    wiki.mkdir()
    (wiki / "a.md").write_text("[[個人資料保護法/第41條]] [[個人資料保護法/第41條]]", encoding="utf-8")
    (wiki / "b.md").write_text("[[資通安全管理法/第1條]] [[個人資料保護法/第99條]]", encoding="utf-8")
    r = coverage(wiki, corpus)
    assert r.cited == 2          # dangling 第99條 does not count as coverage
    assert r.total == 3
    assert r.never_cited == ["個人資料保護法/第12條"]


def test_coverage_reports_dangling_citations(corpus, tmp_path):
    w = tmp_path / "a.md"
    w.write_text("[[個人資料保護法/第99條]]", encoding="utf-8")
    assert coverage(w, corpus).dangling == ["個人資料保護法/第99條"]
