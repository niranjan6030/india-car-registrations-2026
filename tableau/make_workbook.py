"""Generate a Tableau workbook (.twb) for the India car registrations data.

A .twb is plain XML. The element patterns here mirror Tableau's own shipped
workbooks (Superstore.twbx, PerformanceRecording_new.twb) so the file passes
Tableau's schema validation on open.
"""
from pathlib import Path
import csv

PROJ = Path(__file__).resolve().parent.parent
CSV_PATH = PROJ / "data/clean/tableau_cars_flat.csv"
OUT = PROJ / "tableau/India_Car_Registrations_2026.twb"

DS = "CarData"
LEAF = "CarDataleaf"
TABLE = "tableau_cars_flat#csv"

TYPES = {  # csv column -> (datatype, role, type, remote-type)
    "Month": ("date", "dimension", "ordinal", "7"),
    "State": ("string", "dimension", "nominal", "129"),
    "Maker (legal entity)": ("string", "dimension", "nominal", "129"),
    "Powertrain": ("string", "dimension", "nominal", "129"),
    "Registrations": ("integer", "measure", "quantitative", "20"),
    "Brand": ("string", "dimension", "nominal", "129"),
    "Parent Group": ("string", "dimension", "nominal", "129"),
    "Origin Country": ("string", "dimension", "nominal", "129"),
    "Region": ("string", "dimension", "nominal", "129"),
    "State Code": ("string", "dimension", "nominal", "129"),
    "State or UT": ("string", "dimension", "nominal", "129"),
    "Map Location": ("string", "dimension", "nominal", "129"),
    "Month Name": ("string", "dimension", "nominal", "129"),
    "Month Number": ("integer", "dimension", "ordinal", "20"),
    "Quarter": ("string", "dimension", "nominal", "129"),
    "Days Covered": ("integer", "measure", "quantitative", "20"),
    "Is Partial Month": ("boolean", "dimension", "nominal", "11"),
    "Is EV": ("boolean", "dimension", "nominal", "11"),
}
SEMANTIC = {"State": "[State].[Name]", "Map Location": "[State].[Name]"}

# calculated fields: id -> (caption, datatype, role, type, formula, format)
CALCS = {
    "Calculation_ev_reg": ("EV Registrations", "integer", "measure", "quantitative",
                           "IF [Is EV] THEN [Registrations] ELSE 0 END", None),
    "Calculation_ev_share": ("EV Share", "real", "measure", "quantitative",
                             "SUM([Calculation_ev_reg]) / SUM([Registrations])", "p0.0%"),
    "Calculation_per_day": ("Cars Per Day", "real", "measure", "quantitative",
                            "SUM([Registrations]) / SUM({ FIXED [Month Name] : MAX([Days Covered]) })",
                            "n#,##0"),
}


UPDATED = __import__("datetime").datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&apos;"))


with open(CSV_PATH) as fh:
    HEADERS = next(csv.reader(fh))

# ---------------------------------------------------------------- data source
rel_cols, meta, ds_cols = [], [], []
for i, h in enumerate(HEADERS):
    dt, role, ty, remote = TYPES[h]
    rel_cols.append(f"            <column datatype='{dt}' name='{esc(h)}' ordinal='{i}' />")
    meta.append(f"""          <metadata-record class='column'>
            <remote-name>{esc(h)}</remote-name>
            <remote-type>{remote}</remote-type>
            <local-name>[{esc(h)}]</local-name>
            <parent-name>[{TABLE}]</parent-name>
            <remote-alias>{esc(h)}</remote-alias>
            <ordinal>{i}</ordinal>
            <local-type>{dt}</local-type>
            <aggregation>{'Sum' if role == 'measure' else 'Count'}</aggregation>
            <contains-null>true</contains-null>
          </metadata-record>""")
    sem = f" semantic-role='{SEMANTIC[h]}'" if h in SEMANTIC else ""
    ds_cols.append(f"      <column datatype='{dt}' name='[{esc(h)}]' role='{role}' "
                   f"type='{ty}'{sem} />")

for cid, (caption, dt, role, ty, formula, fmt) in CALCS.items():
    f_attr = f" default-format='{esc(fmt)}'" if fmt else ""
    ds_cols.append(
        f"      <column caption='{esc(caption)}' datatype='{dt}'{f_attr} name='[{cid}]' "
        f"role='{role}' type='{ty}'>\n"
        f"        <calculation class='tableau' formula='{esc(formula)}' />\n"
        f"      </column>")

DATASOURCE = f"""  <datasources>
    <datasource caption='India Car Registrations 2026' inline='true' name='{DS}' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='tableau_cars_flat' name='{LEAF}'>
            <connection character-set='UTF-8' class='textscan' directory='Data'
                        driver='' filename='{CSV_PATH.name}' force-character-set='no'
                        force-header='no' force-separator='no' header='yes' separator=','
                        text-qualifier='&quot;' />
          </named-connection>
        </named-connections>
        <relation connection='{LEAF}' name='{TABLE}' table='[{TABLE}]' type='table'>
          <columns character-set='UTF-8' header='yes' locale='en_US' separator=',' text-qualifier='&quot;'>
{chr(10).join(rel_cols)}
          </columns>
        </relation>
        <metadata-records>
{chr(10).join(meta)}
        </metadata-records>
      </connection>
{chr(10).join(ds_cols)}
    </datasource>
  </datasources>"""


# ---------------------------------------------------------------- helpers
def field_name(col):
    """Physical column name or calculated-field id."""
    return col if col in CALCS else f"[{col}]"


def instance(col, derivation, kind):
    prefix = {"None": "none", "Sum": "sum", "Month-Trunc": "tmn", "User": "usr"}[derivation]
    suffix = {"quantitative": "qk", "ordinal": "ok", "nominal": "nk"}[kind]
    ref = col if col in CALCS else col
    name = f"[{prefix}:{ref}:{suffix}]"
    xml = (f"            <column-instance column='[{esc(ref)}]' derivation='{derivation}' "
           f"name='{name}' pivot='key' type='{kind}' />")
    return name, xml


def col_ref(col):
    if col in CALCS:
        caption, dt, role, ty, formula, fmt = CALCS[col]
        f_attr = f" default-format='{esc(fmt)}'" if fmt else ""
        return (f"            <column caption='{esc(caption)}' datatype='{dt}'{f_attr} "
                f"name='[{col}]' role='{role}' type='{ty}'>\n"
                f"              <calculation class='tableau' formula='{esc(formula)}' />\n"
                f"            </column>")
    dt, role, ty, _ = TYPES[col]
    sem = f" semantic-role='{SEMANTIC[col]}'" if col in SEMANTIC else ""
    return (f"            <column datatype='{dt}' name='[{esc(col)}]' role='{role}' "
            f"type='{ty}'{sem} />")


def worksheet(name, title, mark, rows=None, cols=None, color=None, text=None, sort=None):
    """rows/cols/color/text: (column, derivation, kind). sort: (dim, measure, direction)."""
    specs = [s for s in (rows, cols, color, text) if s]
    used, deps, shelves, encodings = [], [], {"rows": "", "cols": ""}, []

    for key, spec in (("rows", rows), ("cols", cols)):
        if spec:
            n, x = instance(*spec)
            deps.append(x)
            shelves[key] = f"[{DS}].{n}"
    for enc, spec in (("color", color), ("text", text)):
        if spec:
            n, x = instance(*spec)
            deps.append(x)
            encodings.append(f"              <{enc} column='[{DS}].{n}' />")

    for c, *_ in specs:
        if c not in used:
            used.append(c)

    sort_xml = ""
    if sort:
        dim, measure, direction = sort
        dn, dx = instance(dim, "None", "nominal")
        mn, mx = instance(measure, "Sum", "quantitative")
        deps += [dx, mx]
        if measure not in used:
            used.append(measure)
        # Tableau 2026's schema rejects <computed-sort>/<sort> in a hand-written .twb,
        # so sorting is left to a single click in the UI (Guide step 6).
        sort_xml = ""

    colrefs = "\n".join(col_ref(c) for c in used)
    deps_xml = "\n".join(dict.fromkeys(deps))
    enc_xml = ("\n            <encodings>\n" + "\n".join(encodings) + "\n            </encodings>"
               if encodings else "")

    return f"""    <worksheet name='{esc(name)}'>
      <layout-options>
        <title>
          <formatted-text>
            <run fontcolor='#e6ecf5' fontsize='11'>{esc(title)}</run>
          </formatted-text>
        </title>
      </layout-options>
      <table>
        <view>
          <datasources>
            <datasource caption='India Car Registrations 2026' name='{DS}' />
          </datasources>
          <datasource-dependencies datasource='{DS}'>
{colrefs}
{deps_xml}
          </datasource-dependencies>
{sort_xml}          <aggregation value='true' />
        </view>
        <style>
          <style-rule element='worksheet'>
            <format attr='background-color' value='#111a2e' />
          </style-rule>
        </style>
        <panes>
          <pane id='1'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{mark}' />{enc_xml}
          </pane>
        </panes>
        <rows>{shelves['rows']}</rows>
        <cols>{shelves['cols']}</cols>
      </table>
    </worksheet>"""


SHEETS = [
    ("Total Cars", "Cars registered (1 Jan - 17 Jun 2026)", "Text",
     ("Registrations", "Sum", "quantitative"), None, None,
     ("Registrations", "Sum", "quantitative"), None),
    ("EV Share KPI", "Share of new cars that are electric", "Text",
     ("Calculation_ev_share", "Sum", "quantitative"), None, None,
     ("Calculation_ev_share", "Sum", "quantitative"), None),
    ("Monthly Trend", "Cars registered per day, by powertrain", "Area",
     ("Calculation_per_day", "Sum", "quantitative"), ("Month", "Month-Trunc", "ordinal"),
     ("Powertrain", "None", "nominal"), None, None),
    ("EV Share Curve", "EV share of new cars, month by month", "Line",
     ("Calculation_ev_share", "Sum", "quantitative"), ("Month", "Month-Trunc", "ordinal"),
     None, None, None),
    ("Top Brands", "Registrations by brand", "Bar", ("Brand", "None", "nominal"),
     ("Registrations", "Sum", "quantitative"), None, None,
     ("Brand", "Registrations", "DESC")),
    ("EV Brands", "Electric cars by brand", "Bar", ("Brand", "None", "nominal"),
     ("Calculation_ev_reg", "Sum", "quantitative"), None, None,
     ("Brand", "Calculation_ev_reg", "DESC")),
    ("State EV Share", "EV share by state", "Bar", ("State", "None", "nominal"),
     ("Calculation_ev_share", "Sum", "quantitative"), None, None,
     ("State", "Calculation_ev_share", "DESC")),
    ("Region Split", "Registrations by region", "Bar", ("Region", "None", "nominal"),
     ("Registrations", "Sum", "quantitative"), None, None,
     ("Region", "Registrations", "DESC")),
    ("Origin Country", "Where the brands come from", "Bar",
     ("Origin Country", "None", "nominal"), ("Registrations", "Sum", "quantitative"),
     None, None, ("Origin Country", "Registrations", "DESC")),
    ("State EV Detail", "EV share by state and brand", "Automatic",
     ("State", "None", "nominal"), ("Calculation_ev_share", "Sum", "quantitative"),
     None, None, None),
]
WORKSHEETS = [worksheet(*s) for s in SHEETS]


# ---------------------------------------------------------------- dashboards
def zone(sheet, x, y, w, h, zid):
    return (f"            <zone h='{h}' id='{zid}' name='{esc(sheet)}' w='{w}' x='{x}' y='{y}'>\n"
            f"              <zone-style>\n"
            f"                <format attr='border-color' value='#1f2b45' />\n"
            f"                <format attr='border-style' value='solid' />\n"
            f"                <format attr='border-width' value='1' />\n"
            f"                <format attr='margin' value='4' />\n"
            f"              </zone-style>\n"
            f"            </zone>")


def text_zone(title, zid, h=7000):
    return (f"            <zone h='{h}' id='{zid}' type-v2='text' w='100000' x='0' y='0'>\n"
            f"              <formatted-text>\n"
            f"                <run bold='true' fontcolor='#f59e0b' fontsize='16'>{esc(title)}</run>\n"
            f"              </formatted-text>\n"
            f"              <zone-style>\n"
            f"                <format attr='background-color' value='#0b1220' />\n"
            f"                <format attr='border-style' value='none' />\n"
            f"                <format attr='margin' value='4' />\n"
            f"              </zone-style>\n"
            f"            </zone>")


def dashboard(name, title, zones, sheet_cols):
    """sheet_cols: columns used by the sheets on this dashboard (Tableau needs them declared)."""
    deps = "\n".join(col_ref(c) for c in dict.fromkeys(sheet_cols))
    return f"""    <dashboard name='{esc(name)}'>
      <layout-options>
        <title>
          <formatted-text>
            <run bold='true' fontcolor='#f59e0b' fontsize='16'>{esc(title)}</run>
          </formatted-text>
        </title>
      </layout-options>
      <style>
        <style-rule element='dashboard'>
          <format attr='background-color' value='#0b1220' />
        </style-rule>
      </style>
      <size maxheight='800' maxwidth='1200' minheight='800' minwidth='1200' />
      <datasources>
        <datasource caption='India Car Registrations 2026' name='{DS}' />
      </datasources>
      <datasource-dependencies datasource='{DS}'>
{deps}
      </datasource-dependencies>
      <zones>
        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>
{text_zone(title, 2)}
{chr(10).join(zones)}
        </zone>
      </zones>
    </dashboard>"""


DASH1 = dashboard(
    "Overview", "India's Car Market 2026 - 22.9 lakh cars registered, 1 Jan to 17 Jun",
    [zone("Total Cars", 0, 7000, 25000, 15000, 11),
     zone("EV Share KPI", 25000, 7000, 25000, 15000, 12),
     zone("Origin Country", 50000, 7000, 50000, 15000, 13),
     zone("Monthly Trend", 0, 22000, 55000, 40000, 14),
     zone("Top Brands", 55000, 22000, 45000, 40000, 15),
     zone("Region Split", 0, 62000, 100000, 38000, 16)],
    ["Registrations", "Calculation_ev_share", "Calculation_ev_reg", "Calculation_per_day",
     "Origin Country", "Month", "Powertrain", "Brand", "Region"])

DASH2 = dashboard(
    "The EV Shift", "The EV Shift - 3.5% of new cars in January, 7.5% by June",
    [zone("EV Share Curve", 0, 7000, 100000, 35000, 21),
     zone("EV Brands", 0, 42000, 50000, 58000, 22),
     zone("State EV Share", 50000, 42000, 50000, 58000, 23)],
    ["Registrations", "Calculation_ev_share", "Calculation_ev_reg", "Month", "Brand", "State"])

WINDOWS = "\n".join(
    f"""    <window class='worksheet' name='{esc(s[0])}'>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
      </cards>
    </window>""" for s in SHEETS)
WINDOWS += """
    <window class='dashboard' name='Overview'>
      <viewpoints />
      <active id='-1' />
    </window>
    <window class='dashboard' name='The EV Shift'>
      <viewpoints />
      <active id='-1' />
    </window>"""

TWB = f"""<?xml version='1.0' encoding='utf-8' ?>
<workbook locale='en_US' source-build='2026.2.2 (20262.26.0819.2015)' source-platform='mac'
          version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <preferences>
    <preference name='ui.encoding.shelf.height' value='24' />
    <preference name='ui.shelf.height' value='26' />
  </preferences>
{DATASOURCE}
  <worksheets>
{chr(10).join(WORKSHEETS)}
  </worksheets>
  <dashboards>
{DASH1}
{DASH2}
  </dashboards>
  <windows source-height='30'>
{WINDOWS}
  </windows>
</workbook>
"""

if __name__ == "__main__":
    import zipfile
    OUT.write_text(TWB)
    # package as .twbx: Tableau Public will not open a workbook whose data lives outside it
    twbx = OUT.with_suffix(".twbx")
    with zipfile.ZipFile(twbx, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT, OUT.name)
        z.write(CSV_PATH, f"Data/{CSV_PATH.name}")  # extract's original source
    print(f"wrote {twbx} ({twbx.stat().st_size:,} bytes)")
