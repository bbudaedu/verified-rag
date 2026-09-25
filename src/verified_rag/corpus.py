"""Turn the MOJ bulk law dump into one markdown file per article."""

import json
import zipfile
from pathlib import Path


def doc_id(law_name: str, article_no: str) -> str:
    return f"{law_name}/{article_no.replace(' ', '')}"


def build_corpus(zip_path: Path, law_names: list[str], out_dir: Path) -> int:
    raw = zipfile.ZipFile(zip_path).read("ChLaw.json").decode("utf-8-sig")
    dump = json.loads(raw)
    laws = {law["LawName"]: law for law in dump["Laws"]}
    # A typo in a law name would otherwise silently yield an empty corpus.
    missing = [n for n in law_names if n not in laws]
    if missing:
        raise ValueError(f"不存在的法規：{missing}")

    n = 0
    manifest = {"source": "https://law.moj.gov.tw/api/ch/law/json", "update_date": dump.get("UpdateDate"), "laws": []}
    for name in law_names:
        law = laws[name]
        manifest["laws"].append({"name": name, "url": law.get("LawURL"), "modified": law.get("LawModifiedDate")})
        for art in law["LawArticles"]:
            if art.get("ArticleType") != "A":  # chapter/section headers
                continue
            did = doc_id(name, art["ArticleNo"])
            text = art["ArticleContent"].replace("\r\n", "\n").strip()
            p = out_dir / f"{did}.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"# {name} {did.split('/')[1]}\n\n{text}\n", encoding="utf-8")
            n += 1
    (out_dir / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return n


def load_corpus(root: Path) -> dict[str, str]:
    """doc_id -> article text (heading line dropped)."""
    docs = {}
    for p in sorted(Path(root).glob("*/*.md")):
        body = p.read_text(encoding="utf-8").split("\n\n", 1)[-1]
        docs[f"{p.parent.name}/{p.stem}"] = body.strip()
    return docs
