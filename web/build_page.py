"""Inject the data bundle into the page template."""
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
tpl = (PROJ / "web/page_template.html").read_text()
data = (PROJ / "web/data.json").read_text()
page = tpl.replace("__DATA__", data)
out = PROJ / "web/dashboard.html"
out.write_text(page)
# docs/ is what GitHub Pages serves - a standalone site needs the document
# skeleton the artifact platform would otherwise wrap around the page
SKELETON = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Every car registered in India, 1 January to 17 June 2026: 146 raw Vahan government files cleaned and visualised.">
%s
</head>
<body>
%s
</body>
</html>
"""
head_end = page.index("</style>") + len("</style>")
docs = PROJ / "docs/index.html"
docs.parent.mkdir(exist_ok=True)
docs.write_text(SKELETON % (page[:head_end], page[head_end:]))
print(f"wrote {out} and {docs} ({out.stat().st_size / 1024:.0f} KB)")
