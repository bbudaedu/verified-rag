from verified_rag.cli import main


def _wiki(tmp_path, text):
    p = tmp_path / "page.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_verify_exit_0_when_every_claim_is_sourced(corpus, tmp_path, capsys):
    w = _wiki(tmp_path, "「處五年以下有期徒刑」[[個人資料保護法/第41條]]")
    assert main(["verify", str(w), "--corpus", str(corpus)]) == 0


def test_verify_exit_1_and_names_the_bad_claim(corpus, tmp_path, capsys):
    w = _wiki(tmp_path, "「處七年以下有期徒刑」[[個人資料保護法/第41條]]")
    assert main(["verify", str(w), "--corpus", str(corpus)]) == 1
    assert "處七年以下有期徒刑" in capsys.readouterr().out


def test_verify_exit_2_when_corpus_is_empty(tmp_path, capsys):
    # An empty corpus must not read as "nothing fabricated".
    w = _wiki(tmp_path, "「處五年以下有期徒刑」")
    (tmp_path / "empty").mkdir()
    assert main(["verify", str(w), "--corpus", str(tmp_path / "empty")]) == 2


def test_verify_exit_2_when_wiki_has_no_checkable_claims(corpus, tmp_path, capsys):
    # Zero claims checked is not a pass either.
    w = _wiki(tmp_path, "這是一段沒有引號也沒有引用的敘述。")
    assert main(["verify", str(w), "--corpus", str(corpus)]) == 2


def test_coverage_exit_1_below_threshold(corpus, tmp_path, capsys):
    w = _wiki(tmp_path, "[[個人資料保護法/第41條]]")
    assert main(["coverage", str(w), "--corpus", str(corpus), "--min", "0.5"]) == 1
    assert main(["coverage", str(w), "--corpus", str(corpus), "--min", "0.3"]) == 0


def test_missing_wiki_is_exit_2_for_both_commands(corpus, tmp_path, capsys):
    missing = str(tmp_path / "nope.md")
    assert main(["verify", missing, "--corpus", str(corpus)]) == 2
    assert main(["coverage", missing, "--corpus", str(corpus), "--min", "0"]) == 2
    assert "not found" in capsys.readouterr().err


def test_empty_wiki_dir_is_exit_2_for_coverage(corpus, tmp_path, capsys):
    (tmp_path / "wiki").mkdir()
    assert main(["coverage", str(tmp_path / "wiki"), "--corpus", str(corpus), "--min", "0"]) == 2
