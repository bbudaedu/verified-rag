import io
import json
import zipfile

from verified_rag.corpus import build_corpus, doc_id, load_corpus


def _zip(tmp_path, laws):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        # The real file starts with a UTF-8 BOM.
        z.writestr("ChLaw.json", "﻿" + json.dumps({"UpdateDate": "2026/9/18", "Laws": laws}, ensure_ascii=False))
    p = tmp_path / "ChLaw.zip"
    p.write_bytes(buf.getvalue())
    return p


def test_doc_id_strips_spaces_and_keeps_sub_numbers():
    assert doc_id("個人資料保護法", "第 1-1 條") == "個人資料保護法/第1-1條"


def test_build_corpus_writes_only_requested_articles_and_skips_chapter_rows(tmp_path):
    z = _zip(tmp_path, [
        {"LawName": "個人資料保護法", "LawArticles": [
            {"ArticleType": "C", "ArticleNo": "", "ArticleContent": "第 一 章 總則"},
            {"ArticleType": "A", "ArticleNo": "第 1 條", "ArticleContent": "第一項。\r\n第二項。"},
        ]},
        {"LawName": "民法", "LawArticles": [{"ArticleType": "A", "ArticleNo": "第 1 條", "ArticleContent": "x"}]},
    ])
    out = tmp_path / "corpus"
    n = build_corpus(z, ["個人資料保護法"], out)
    assert n == 1
    docs = load_corpus(out)
    assert list(docs) == ["個人資料保護法/第1條"]
    assert "第一項。\n第二項。" in docs["個人資料保護法/第1條"]


def test_build_corpus_fails_loudly_on_unknown_law_name(tmp_path):
    z = _zip(tmp_path, [{"LawName": "民法", "LawArticles": []}])
    import pytest
    with pytest.raises(ValueError, match="不存在的法規"):
        build_corpus(z, ["民法", "個資法"], tmp_path / "c")
