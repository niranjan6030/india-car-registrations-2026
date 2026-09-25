"""Inject the data bundle into the page template."""
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
tpl = (PROJ / "web/page_template.html").read_text()
data = (PROJ / "web/data.json").read_text()
page = tpl.replace("__DATA__", data)
out = PROJ / "web/dashboard.html"
out.write_text(page)
# docs/ is what GitHub Pages serves
docs = PROJ / "docs/index.html"
docs.parent.mkdir(exist_ok=True)
docs.write_text(page)
print(f"wrote {out} and {docs} ({out.stat().st_size / 1024:.0f} KB)")
