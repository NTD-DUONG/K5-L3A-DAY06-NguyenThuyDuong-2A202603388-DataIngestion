"""Package saved Wikipedia HTML as text-only MHTML sources for submission."""
from collections import Counter
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
import hashlib
import json

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest_path = ROOT / "data/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = ROOT / "data/text_sources"
    output_dir.mkdir(exist_ok=True)
    log = []
    for document in manifest["documents"]:
        original = ROOT / "data/raw" / Path(document["raw_path"]).name
        raw = original.read_bytes()
        message = BytesParser(policy=policy.default).parsebytes(raw)
        part = next(p for p in message.walk() if p.get_content_type() == "text/html")
        soup = BeautifulSoup(part.get_payload(decode=True).decode("utf-8"), "html.parser")
        # Full textual DOM retains source headings, references, attribution and history links.
        for element in soup.select("script, style, link, img, picture, source, svg, canvas, iframe, object, embed, video, audio, input"):
            element.decompose()
        for element in soup.find_all(True):
            for attribute in list(element.attrs):
                if attribute in {"style", "src", "srcset", "poster", "background"} or attribute.lower().startswith("on"):
                    del element.attrs[attribute]
        safe = EmailMessage(policy=policy.SMTP)
        safe["Subject"] = document["title"]
        safe["Snapshot-Content-Location"] = document["snapshot_url"]
        safe.set_content(str(soup), subtype="html", charset="utf-8")
        safe["Content-Location"] = document["snapshot_url"]
        safe.make_related()
        destination = output_dir / original.name
        destination.write_bytes(safe.as_bytes())
        check = BytesParser(policy=policy.default).parsebytes(destination.read_bytes())
        payload_types = [p.get_content_type() for p in check.walk() if not p.is_multipart()]
        assert payload_types == ["text/html"]
        document["raw_path"] = destination.relative_to(ROOT).as_posix()
        document["source_packaging"] = "Text-only MHTML with media, CSS and executable elements removed from saved source"
        log.append({
            "source_id": document["source_id"], "snapshot_url": document["snapshot_url"],
            "original_local_path": original.relative_to(ROOT).as_posix(),
            "original_sha256": hashlib.sha256(raw).hexdigest(),
            "submitted_path": document["raw_path"],
            "submitted_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "original_mime_parts": dict(Counter(p.get_content_type() for p in message.walk() if not p.is_multipart())),
            "submitted_mime_parts": payload_types,
        })
        print(document["source_id"], "text-only MHTML saved")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "data/processing_logs/text_source_packaging.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
