import pytest


@pytest.fixture
def corpus(tmp_path):
    """Three-article toy corpus laid out the way build_corpus writes it."""
    root = tmp_path / "corpus"
    docs = {
        "個人資料保護法/第41條": "意圖為自己或第三人不法之利益，違反第六條第一項規定，足生損害於他人者，處五年以下有期徒刑，得併科新臺幣一百萬元以下罰金。",
        "個人資料保護法/第12條": "公務機關或非公務機關違反本法規定，致個人資料被竊取、洩漏、竄改或其他侵害者，應查明後以適當方式通知當事人。",
        "資通安全管理法/第1條": "為積極推動國家資通安全政策，加速建構國家資通安全環境，以保障國家安全，維護社會公共利益，特制定本法。",
    }
    for doc_id, text in docs.items():
        law, art = doc_id.split("/")
        p = root / law / f"{art}.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# {law} {art}\n\n{text}\n", encoding="utf-8")
    return root
