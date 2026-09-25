import pytest

from verified_rag.retrieval import Index, mrr, recall_at_k, tokens


def test_tokens_bigram_and_char_modes_drop_punctuation():
    assert tokens("個資，外洩", "bigram") == ["個資", "外洩"]
    assert tokens("個資外洩", "bigram") == ["個資", "資外", "外洩"]
    assert tokens("個資", "char") == ["個", "資"]


def test_single_cjk_char_run_still_yields_a_token():
    assert tokens("法", "bigram") == ["法"]


@pytest.mark.parametrize("strategy", ["bigram-or", "char-or"])
def test_or_strategies_find_the_article_for_a_paraphrased_question(corpus, strategy):
    idx = Index.build(corpus)
    ranked = idx.search("個資外洩時要怎麼通知當事人", strategy)
    assert ranked[0] == "個人資料保護法/第12條"


def test_bigram_and_returns_nothing_for_a_natural_question(corpus):
    # The failure mode this repo documents: every bigram must match, and
    # natural questions always contain bigrams the statute never uses.
    idx = Index.build(corpus)
    assert idx.search("個資外洩時要怎麼通知當事人", "bigram-and") == []


def test_metrics():
    runs = [(["a", "b"], {"b"}), (["c"], {"x"}), (["d"], {"d"})]
    assert recall_at_k(runs, 1) == pytest.approx(1 / 3)
    assert recall_at_k(runs, 3) == pytest.approx(2 / 3)
    assert mrr(runs) == pytest.approx((0.5 + 0 + 1) / 3)
