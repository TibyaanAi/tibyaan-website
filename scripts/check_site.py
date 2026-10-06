"""Check local HTML navigation and bundled resources without network access."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PAGES = (ROOT / "index.html", ROOT / "privacy.html", ROOT / "schools.html")


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
            target = (page.parent / unquote(url.path)).resolve() if url.path else page
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
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Checked {len(PAGES)} HTML pages and {local_count} local links/resources")


if __name__ == "__main__":
    main()
