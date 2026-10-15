"""Génère le notebook Kaggle d'analyse (en anglais), qui lit le dataset publié.

Usage :
    uv run python kaggle/build_notebook.py
    uv run jupyter nbconvert --to notebook --execute kaggle/notebook/french-housing-prices.ipynb   # test local
"""
from pathlib import Path

import nbformat as nbf

OUT = Path(__file__).parent / "notebook" / "french-housing-prices.ipynb"

nb = nbf.v4.new_notebook()
cells = []


def md(text: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(text.strip()))


def code(text: str) -> None:
    cells.append(nbf.v4.new_code_cell(text.strip()))


md("""
# French housing prices 2021–2025: what 600,000 sales tell us

This notebook explores the **[French Housing Prices DVF 2021-2025 (Cleaned)](https://www.kaggle.com/datasets/kevinnkameni/french-housing-prices-dvf)**
dataset: every sale of a single apartment or house in Paris, Lyon, Marseille, Bordeaux and Montpellier's departments,
from the French government's open data (DVF).

The raw DVF files are hard to use correctly (prices repeated on every row of a sale, multi-home sales, parcels in two
communes…). The dataset was produced by a **data engineering pipeline** that fixes these issues and tests the result:
Python ingestion, **dbt** transformations with 25 data quality tests, **Airflow** orchestration, PostgreSQL.

- 💻 Pipeline code: [github.com/MKkevin2712/dvf-pipeline](https://github.com/MKkevin2712/dvf-pipeline)
- 🌍 Interactive dashboard (React): [mkkevin2712.github.io/dvf-pipeline](https://mkkevin2712.github.io/dvf-pipeline/)

All the analysis below is written in **SQL with DuckDB**, which queries the Parquet file directly.
""")

code("""
import glob
import subprocess
import sys

try:
    import duckdb
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "duckdb"], check=True)
    import duckdb

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False})

# Locate the dataset (Kaggle input folder, or a local copy)
SALES = (glob.glob("/kaggle/input/**/home_sales.parquet", recursive=True)
         + glob.glob("../dataset/home_sales.parquet"))[0]
con = duckdb.connect()
con.execute(f"CREATE VIEW sales AS SELECT * FROM '{SALES}'")

DEPARTMENTS = {"75": "Paris", "69": "Rhône (Lyon)", "13": "Bouches-du-Rhône (Marseille)",
               "33": "Gironde (Bordeaux)", "34": "Hérault (Montpellier)"}
sql = lambda q: con.execute(q).df()
sql("SELECT count(*) AS sales, min(sale_date) AS first_sale, max(sale_date) AS last_sale FROM sales")
""")

md("## 1. The big picture: price per m² by department")
code("""
overview = sql('''
    SELECT department_code, property_type,
           count(*)                                                  AS sales,
           round(median(price_per_m2_eur))                           AS median_price_per_m2,
           round(median(price_eur))                                  AS median_price,
           round(median(living_area_m2))                             AS median_area_m2
    FROM sales
    WHERE year = 2025
    GROUP BY ALL
    ORDER BY median_price_per_m2 DESC
''')
overview.insert(1, "department", overview["department_code"].map(DEPARTMENTS))
overview
""")
md("""
Paris is in a league of its own: **about 10,000 €/m²** for an apartment, roughly 2.5 to 3 times the other big cities.
In Paris, the median apartment is only **~43 m²**, yet costs around 400,000 €.
""")

md("""
## 2. How prices moved since 2021

Monthly medians are noisy (fewer sales some months), so the chart shows a **3-month rolling average**.
""")
code("""
monthly = sql('''
    SELECT department_code, month, median(price_per_m2_eur) AS median_price_per_m2, count(*) AS sales
    FROM sales
    WHERE property_type = 'Apartment'
    GROUP BY ALL
    ORDER BY department_code, month
''')
monthly["smoothed"] = monthly.groupby("department_code")["median_price_per_m2"].transform(lambda s: s.rolling(3).mean())
# Index 100 = average of 2021, to compare cities with very different price levels
base = monthly[monthly["month"].dt.year == 2021].groupby("department_code")["median_price_per_m2"].mean()
monthly["index"] = 100 * monthly["smoothed"] / monthly["department_code"].map(base)

fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
for dep, g in monthly.groupby("department_code"):
    axes[0].plot(g["month"], g["smoothed"], label=DEPARTMENTS[dep])
    axes[1].plot(g["month"], g["index"], label=DEPARTMENTS[dep])
axes[0].set_title("Apartments: median price per m² (3-month rolling)")
axes[0].set_ylabel("€/m²")
axes[1].set_title("Same, as an index (2021 average = 100)")
axes[1].axhline(100, color="grey", lw=0.8, ls="--")
axes[1].legend(fontsize=8)
plt.tight_layout(); plt.show()
""")
code("""
yearly = sql('''
    SELECT department_code, year, median(price_per_m2_eur) AS median_price_per_m2
    FROM sales WHERE property_type = 'Apartment' GROUP BY ALL
''').pivot(index="department_code", columns="year", values="median_price_per_m2")
change = pd.DataFrame({
    "department": yearly.index.map(DEPARTMENTS),
    "2021 → peak": (yearly.max(axis=1) / yearly[2021] - 1),
    "peak → 2025": (yearly[2025] / yearly.max(axis=1) - 1),
    "2021 → 2025": (yearly[2025] / yearly[2021] - 1),
}).set_index("department")
change.style.format("{:+.1%}").background_gradient(cmap="RdYlGn_r", axis=None)
""")
md("""
Two different stories:
- **Paris, Lyon and Bordeaux fell by 8 to 11 % from their peak** (2021 for Paris, 2022 for Lyon and Bordeaux):
  the jump in mortgage rates in 2022–2023 hit the most expensive markets hardest.
- **Marseille and Montpellier are still about 10 % above their 2021 level**: cheaper markets held up better.
""")

md("## 3. Where it is most and least expensive (2025)")
code("""
communes = sql('''
    SELECT commune_name, department_code, count(*) AS sales, median(price_per_m2_eur) AS median_price_per_m2
    FROM sales
    WHERE year = 2025 AND property_type = 'Apartment'
    GROUP BY ALL
    HAVING count(*) >= 30          -- a median on fewer sales is not reliable
''')
top = communes.nlargest(12, "median_price_per_m2").sort_values("median_price_per_m2")
bottom = communes.nsmallest(12, "median_price_per_m2").sort_values("median_price_per_m2", ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].barh(top["commune_name"], top["median_price_per_m2"], color="#d7301f")
axes[0].set_title("Most expensive (apartments, ≥ 30 sales)")
axes[1].barh(bottom["commune_name"], bottom["median_price_per_m2"], color="#2b8cbe")
axes[1].set_title("Most affordable (apartments, ≥ 30 sales)")
for ax in axes:
    ax.set_xlabel("Median €/m²")
plt.tight_layout(); plt.show()
""")

md("""
## 4. Map of prices by commune

Each circle is a commune (median 2025 apartment price per m²); its size reflects the number of sales.
""")
code("""
geo = sql('''
    SELECT commune_name, department_code,
           median(latitude) AS lat, median(longitude) AS lon,
           count(*) AS sales, round(median(price_per_m2_eur)) AS median_price_per_m2
    FROM sales
    WHERE year = 2025 AND property_type = 'Apartment' AND latitude IS NOT NULL
    GROUP BY ALL
    HAVING count(*) >= 10
''')
options = {
    "lat": "lat", "lon": "lon", "size": "sales", "color": "median_price_per_m2",
    "color_continuous_scale": "OrRd", "size_max": 28, "zoom": 4.6, "center": {"lat": 45.6, "lon": 3.2},
    "hover_name": "commune_name", "height": 560, "title": "Median apartment price per m², 2025",
    "hover_data": {"median_price_per_m2": True, "sales": True, "lat": False, "lon": False},
}
if hasattr(px, "scatter_map"):                 # plotly ≥ 5.24
    fig = px.scatter_map(geo, map_style="carto-positron", **options)
else:
    fig = px.scatter_mapbox(geo, mapbox_style="carto-positron", **options)
fig.show()
""")

md("""
## 5. Small flats are more expensive per m²

A classic effect: kitchen and bathroom cost the same in a 20 m² studio and a 100 m² flat, and studios are in high
demand (students, investors). Let's check whether it holds everywhere.
""")
code("""
by_size = sql('''
    SELECT department_code,
           CASE WHEN living_area_m2 < 25 THEN '1. < 25 m²'
                WHEN living_area_m2 < 40 THEN '2. 25–40 m²'
                WHEN living_area_m2 < 60 THEN '3. 40–60 m²'
                WHEN living_area_m2 < 90 THEN '4. 60–90 m²'
                ELSE '5. ≥ 90 m²' END                             AS size_band,
           median(price_per_m2_eur)                               AS median_price_per_m2
    FROM sales
    WHERE property_type = 'Apartment' AND year >= 2024
    GROUP BY ALL
''')
pivot = by_size.pivot(index="size_band", columns="department_code", values="median_price_per_m2")
premium = (pivot.iloc[0] / pivot.iloc[-1] - 1).rename(index=DEPARTMENTS)
ax = (pivot / pivot.iloc[-1]).rename(columns=DEPARTMENTS).plot(marker="o", figsize=(9, 4.5))
ax.set_ylabel("Price per m² relative to ≥ 90 m² flats")
ax.set_title("Price per m² by apartment size (2024–2025)")
plt.tight_layout(); plt.show()
premium.map("{:+.0%}".format).to_frame("studio premium vs ≥ 90 m²")
""")
md("""
Studios cost **30 to 60 % more per m²** than large flats everywhere… **except in Paris**, where the trend reverses:
large flats are concentrated in the most prestigious districts (6th, 7th, 16th), which pushes their price per m² up.
""")

md("## 6. The new-build premium")
code("""
sql('''
    SELECT department_code,
           round(median(price_per_m2_eur) FILTER (WHERE is_new_build))       AS new_build,
           round(median(price_per_m2_eur) FILTER (WHERE NOT is_new_build))   AS existing,
           round(100 * (median(price_per_m2_eur) FILTER (WHERE is_new_build)
                 / median(price_per_m2_eur) FILTER (WHERE NOT is_new_build) - 1)) AS premium_pct,
           count(*) FILTER (WHERE is_new_build)                               AS new_build_sales
    FROM sales
    WHERE property_type = 'Apartment' AND year >= 2024
    GROUP BY ALL
    ORDER BY premium_pct DESC
''').assign(department=lambda d: d["department_code"].map(DEPARTMENTS))
""")
md("""
Outside Paris, **new apartments sell at a clear premium (+19 % to +54 %)**: better energy performance, lower notary
fees and, until 2024, tax incentives for investors. Paris has too few new-build sales (about 50) to draw a conclusion.
""")

md("""
## Takeaways

1. **Paris, Lyon and Bordeaux corrected by 8–11 %** from their peak, while cheaper markets (Marseille, Montpellier)
   held up better.
2. **Location dominates**: within a department, the price per m² can vary by a factor of three between communes.
3. **Small flats and new builds carry a premium** per m², except in Paris, where large flats in prime districts
   lead the market.
4. **Data quality matters**: without the cleaning done upstream (prices repeated on every row, multi-home sales),
   prices per m² would be badly wrong.

If this was useful, an upvote is appreciated. The full pipeline (Airflow, dbt, tests, React dashboard) is on
[GitHub](https://github.com/MKkevin2712/dvf-pipeline). *Kevin Moukam Nkameni*
""")

nb["cells"] = cells
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nb["metadata"]["language_info"] = {"name": "python"}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, OUT)
print(f"{len(cells)} cellules → {OUT}")
