from app.core.htmlmeta import parse_metadata

BASE = "https://example.com/docs/page"


def test_extracts_title_description_and_favicon():
    html = """
    <html><head>
      <title>  Example Docs </title>
      <meta name="description" content="A useful page.">
      <link rel="icon" href="/static/icon.png">
    </head><body>hi</body></html>
    """
    meta = parse_metadata(html, BASE)
    assert meta["title"] == "Example Docs"
    assert meta["description"] == "A useful page."
    assert meta["favicon"] == "https://example.com/static/icon.png"


def test_og_fallbacks_and_absolute_favicon():
    html = """
    <html><head>
      <meta property="og:title" content="OG Title">
      <meta property="og:description" content="OG desc">
      <link rel="shortcut icon" href="https://cdn.example.com/i.ico">
    </head></html>
    """
    meta = parse_metadata(html, BASE)
    assert meta["title"] == "OG Title"
    assert meta["description"] == "OG desc"
    assert meta["favicon"] == "https://cdn.example.com/i.ico"


def test_title_tag_wins_over_og_title():
    html = "<head><title>Real</title><meta property='og:title' content='OG'></head>"
    assert parse_metadata(html, BASE)["title"] == "Real"


def test_defaults_when_nothing_found():
    meta = parse_metadata("<html><body>plain</body></html>", BASE)
    assert meta["title"] == ""
    assert meta["description"] == ""
    assert meta["favicon"] == "https://example.com/favicon.ico"


def test_survives_malformed_html():
    # <title> is RCDATA: an unclosed tag legitimately swallows the rest.
    # The contract here is "no crash, always returns the three string keys".
    meta = parse_metadata("<title>Broken<meta name=description content", BASE)
    assert meta["title"].startswith("Broken")
    assert set(meta) == {"title", "description", "favicon"}
