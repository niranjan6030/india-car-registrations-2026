"""Inject the data bundle into the page template."""
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
tpl = (PROJ / "web/page_template.html").read_text()
data = (PROJ / "web/data.json").read_text()
out = PROJ / "web/dashboard.html"
out.write_text(tpl.replace("__DATA__", data))
print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
