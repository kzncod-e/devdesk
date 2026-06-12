from html.parser import HTMLParser
from urllib.parse import urljoin


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.og_title = ""
        self.description = ""
        self.og_description = ""
        self.favicon_href = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {k: (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            content = attr.get("content", "")
            if attr.get("name") == "description" and not self.description:
                self.description = content
            elif attr.get("property") == "og:description" and not self.og_description:
                self.og_description = content
            elif attr.get("property") == "og:title" and not self.og_title:
                self.og_title = content
        elif tag == "link":
            rels = attr.get("rel", "").lower().split()
            if "icon" in rels and not self.favicon_href:
                self.favicon_href = attr.get("href", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def parse_metadata(html: str, base_url: str) -> dict[str, str]:
    """Best-effort title/description/favicon extraction for bookmark metadata."""
    parser = _MetaParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass  # keep whatever was parsed before the markup broke
    favicon = urljoin(base_url, parser.favicon_href or "/favicon.ico")
    return {
        "title": (parser.title or parser.og_title).strip(),
        "description": (parser.description or parser.og_description).strip(),
        "favicon": favicon,
    }
