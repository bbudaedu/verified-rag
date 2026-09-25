from verified_rag.verify import extract_claims, verify_text


def statuses(report):
    return {(c.text, c.status) for c in report}


def test_verbatim_quote_in_cited_article_passes(corpus):
    md = "違反者「處五年以下有期徒刑」[[個人資料保護法/第41條]]。"
    assert statuses(verify_text(md, corpus)) == {("處五年以下有期徒刑", "ok")}


def test_paraphrased_quote_is_absent(corpus):
    # The LLM upgraded "得併科" to "並科" -- same topic, different law.
    md = "「並科新臺幣一百萬元以下罰金」[[個人資料保護法/第41條]]"
    assert ("並科新臺幣一百萬元以下罰金", "absent") in statuses(verify_text(md, corpus))


def test_real_quote_attached_to_wrong_article_is_misattributed(corpus):
    md = "應「以適當方式通知當事人」[[資通安全管理法/第1條]]"
    assert statuses(verify_text(md, corpus)) == {("以適當方式通知當事人", "misattributed")}


def test_citation_to_nonexistent_article_is_dangling(corpus):
    md = "見 [[個人資料保護法/第99條]]。"
    assert statuses(verify_text(md, corpus)) == {("個人資料保護法/第99條", "dangling")}


def test_uncited_claim_is_flagged_even_when_the_text_exists(corpus):
    # Otherwise a wiki with no citations at all scores 100%.
    md = "法律要求「應查明後以適當方式通知當事人」。"
    assert statuses(verify_text(md, corpus)) == {("應查明後以適當方式通知當事人", "uncited")}


def test_uncited_claim_found_nowhere_is_absent(corpus):
    assert statuses(verify_text("「處十年以下有期徒刑」", corpus)) == {("處十年以下有期徒刑", "absent")}


def test_citation_scope_is_the_list_item_not_the_whole_block(corpus):
    md = "- 「處五年以下有期徒刑」[[個人資料保護法/第41條]]\n- 「以適當方式通知當事人」[[個人資料保護法/第12條]]"
    assert {s for _, s in statuses(verify_text(md, corpus))} == {"ok"}


def test_money_amount_outside_quotes_is_a_claim(corpus):
    md = "最高可罰新臺幣二百萬元以下罰金 [[個人資料保護法/第41條]]"
    assert ("新臺幣二百萬元以下", "absent") in statuses(verify_text(md, corpus))


def test_matching_ignores_whitespace_and_fullwidth_differences(corpus):
    md = "「處 五年以下 有期徒刑」[[個人資料保護法/第41條]]"
    assert {s for _, s in statuses(verify_text(md, corpus))} == {"ok"}


def test_short_fragments_are_not_claims():
    # Three characters match almost anything in a legal corpus; no signal.
    assert extract_claims("「本法」") == []


def test_money_range_is_checked_as_a_whole():
    # Matching only the lower bound would let a wrong upper bound through.
    docs = {"個人資料保護法/第48條": "處新臺幣二萬元以上二百萬元以下罰鍰"}
    md = "處新臺幣二萬元以上二十萬元以下罰鍰 [[個人資料保護法/第48條]]"
    assert statuses(verify_text(md, docs)) == {("新臺幣二萬元以上二十萬元以下", "absent")}


def test_one_sided_amount_keeps_its_direction_word():
    docs = {"a/第1條": "得併科新臺幣一百萬元以下罰金"}
    md = "得併科新臺幣一百萬元以上罰金 [[a/第1條]]"
    assert statuses(verify_text(md, docs)) == {("新臺幣一百萬元以上", "absent")}


def test_colloquial_tai_character_matches_statute_spelling():
    docs = {"a/第1條": "處新臺幣二萬元以上二十萬元以下罰鍰"}
    md = "處新台幣二萬元以上二十萬元以下罰鍰 [[a/第1條]]"
    assert {s for _, s in statuses(verify_text(md, docs))} == {"ok"}


def test_arabic_numeral_amounts_are_not_extracted():
    # Statutes spell amounts in Chinese numerals; matching 2萬 against 二萬
    # would report a correct amount as fabricated.
    assert extract_claims("處新臺幣2萬元以上20萬元以下罰鍰，或新臺幣20,000元") == []
