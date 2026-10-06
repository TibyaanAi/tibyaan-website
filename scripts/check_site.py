"""Check local HTML navigation, bundled resources and /.well-known files without network access."""

import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import well_known  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
PAGES = (ROOT / "index.html", ROOT / "privacy.html", ROOT / "schools.html", ROOT / "404.html", ROOT / "k" / "index.html")


def check_well_known(errors):
    # GitHub Pages runs Jekyll unless .nojekyll exists, and Jekyll drops dot-directories.
    if not (ROOT / ".nojekyll").is_file():
        errors.append(".nojekyll is missing: GitHub Pages would not publish .well-known/")
    for path, content in well_known.rendered().items():
        target = ROOT / path
        if not target.is_file():
            errors.append(f"missing {path} (run python3 scripts/well_known.py)")
            continue
        text = target.read_text(encoding="utf-8")
        json.loads(text)
        if text != content:
            errors.append(f"{path} is out of date (run python3 scripts/well_known.py)")


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if tag in ("a", "link") and values.get("href"):
            self.links.append(values["href"])
        if tag in ("img", "script") and values.get("src"):
            self.links.append(values["src"])


def main():
    parsed = {}
    for page in PAGES:
        parser = PageLinks()
        parser.feed(page.read_text(encoding="utf-8"))
        parsed[page] = parser

    errors = []
    local_count = 0
    for page, parser in parsed.items():
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            local_count += 1
            if not url.path:
                target = page
            elif url.path.startswith("/"):
                target = (ROOT / unquote(url.path).lstrip("/")).resolve()  # site-root path (404.html)
            else:
                target = (page.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                errors.append(f"{page.name}: missing local target {link}")
                continue
            if url.fragment:
                target_parser = parsed.get(target)
                if target_parser is None:
                    target_parser = PageLinks()
                    target_parser.feed(target.read_text(encoding="utf-8"))
                    parsed[target] = target_parser
                if unquote(url.fragment) not in target_parser.ids:
                    errors.append(f"{page.name}: missing fragment {link}")
    check_well_known(errors)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Checked {len(PAGES)} HTML pages and {local_count} local links/resources")


if __name__ == "__main__":
    main()
