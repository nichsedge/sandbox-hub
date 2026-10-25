# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=0.10.0",
# ]
# ///
"""pcomp Local Price Intelligence & Dashboard Generator.

Queries local JSON snapshots from indoscraping using embedded DuckDB
and renders a self-contained, interactive HTML dashboard with Chart.js.
No BigQuery, no cloud credentials, and no external daemon needed.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import duckdb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pcomp-report")

DEFAULT_DATA_DIR = Path.home() / "Projects" / "indoscraping" / "data" / "hardware"
DEFAULT_OUTPUT_HTML = (
    Path.home()
    / "Projects"
    / "sandbox-hub"
    / "analysis"
    / "dbt-bq"
    / "pcomp_dw"
    / "reports"
    / "pcomp_dashboard.html"
)


def load_hardware_data(data_dir: Path) -> duckdb.DuckDBPyConnection:
    """Load latest hardware json files into an in-memory DuckDB table."""
    conn = duckdb.connect(":memory:")

    glob_pattern = str(data_dir / "*" / "latest.json")
    matching_files = list(data_dir.glob("*/latest.json"))

    if not matching_files:
        raise FileNotFoundError(
            f"No 'latest.json' files found under {data_dir}. "
            "Please run 'uv run indoscraping run enterkomputer' and 'uv run indoscraping run viraindo' first."
        )

    logger.info(f"Ingesting {len(matching_files)} hardware catalog files from {data_dir}...")

    # Comprehensive multi-category hardware parsing and tier extraction in DuckDB
    conn.execute(f"""
        CREATE TABLE raw_catalog AS 
        SELECT 
            name,
            price,
            source,
            url,
            COALESCE(scraped_at, CURRENT_TIMESTAMP::VARCHAR) as scraped_at,
            CASE 
                WHEN lower(category) IN ('proc', 'processor') THEN 'CPU'
                WHEN lower(category) IN ('vga') THEN 'GPU'
                WHEN lower(category) IN ('memory', 'memory-ram') THEN 'RAM'
                WHEN lower(category) IN ('storage', 'solid-state-drive', 'hard-disk') THEN 'Storage'
                WHEN lower(category) IN ('motherboard') THEN 'Motherboard'
                WHEN lower(category) IN ('psu') THEN 'PSU'
                WHEN lower(category) IN ('casing') THEN 'Casing'
                WHEN lower(category) IN ('lcd') THEN 'Monitor'
                WHEN lower(category) IN ('cooler') THEN 'Cooler'
                WHEN lower(category) IN ('keyboard', 'keymouse') THEN 'Peripheral'
                ELSE 'Other'
            END AS std_category,
            COALESCE(NULLIF(regexp_extract(name, '(?i)(Asus|MSI|Gigabyte|ASRock|Zotac|Colorful|Palit|Galax|Sapphire|PowerColor|XFX|Inno3D|Kingston|Samsung|Corsair|Adata|Team|Klevv|Lexar|Seagate|WD|Western Digital|Deepcool|Thermalright|Seasonic|FSP|be quiet|Cooler Master|NZXT|Fractal|Lian Li|Antec|Thermaltake|Silverstone)', 1), ''), 'Other') AS brand,
            CASE 
                -- GPU Tiers
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rtx 4090%' THEN 'RTX 4090'
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rtx 4080%' THEN 'RTX 4080'
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rtx 4070 ti%' THEN 'RTX 4070 Ti'
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rtx 4070%' THEN 'RTX 4070'
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rtx 4060 ti%' THEN 'RTX 4060 Ti'
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rtx 4060%' THEN 'RTX 4060'
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rtx 3060%' THEN 'RTX 3060'
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rx 7900%' THEN 'RX 7900'
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rx 7800%' THEN 'RX 7800'
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rx 7700%' THEN 'RX 7700'
                WHEN lower(category) = 'vga' AND lower(name) LIKE '%rx 6600%' THEN 'RX 6600'
                WHEN lower(category) = 'vga' AND (lower(name) LIKE '%arc a770%' OR lower(name) LIKE '%arc a750%') THEN 'Intel Arc'

                -- CPU Tiers
                WHEN lower(category) IN ('proc', 'processor') AND lower(name) LIKE '%ryzen 9%' THEN 'AMD Ryzen 9'
                WHEN lower(category) IN ('proc', 'processor') AND lower(name) LIKE '%ryzen 7%' THEN 'AMD Ryzen 7'
                WHEN lower(category) IN ('proc', 'processor') AND lower(name) LIKE '%ryzen 5%' THEN 'AMD Ryzen 5'
                WHEN lower(category) IN ('proc', 'processor') AND lower(name) LIKE '%ryzen 3%' THEN 'AMD Ryzen 3'
                WHEN lower(category) IN ('proc', 'processor') AND lower(name) LIKE '%core i9%' THEN 'Intel Core i9'
                WHEN lower(category) IN ('proc', 'processor') AND lower(name) LIKE '%core i7%' THEN 'Intel Core i7'
                WHEN lower(category) IN ('proc', 'processor') AND lower(name) LIKE '%core i5%' THEN 'Intel Core i5'
                WHEN lower(category) IN ('proc', 'processor') AND lower(name) LIKE '%core i3%' THEN 'Intel Core i3'

                -- RAM Tiers
                WHEN lower(category) IN ('memory', 'memory-ram') AND lower(name) LIKE '%ddr5%' AND lower(name) LIKE '%32gb%' THEN 'DDR5 32GB'
                WHEN lower(category) IN ('memory', 'memory-ram') AND lower(name) LIKE '%ddr5%' AND lower(name) LIKE '%16gb%' THEN 'DDR5 16GB'
                WHEN lower(category) IN ('memory', 'memory-ram') AND lower(name) LIKE '%ddr5%' AND lower(name) LIKE '%64gb%' THEN 'DDR5 64GB'
                WHEN lower(category) IN ('memory', 'memory-ram') AND lower(name) LIKE '%ddr4%' AND lower(name) LIKE '%32gb%' THEN 'DDR4 32GB'
                WHEN lower(category) IN ('memory', 'memory-ram') AND lower(name) LIKE '%ddr4%' AND lower(name) LIKE '%16gb%' THEN 'DDR4 16GB'
                WHEN lower(category) IN ('memory', 'memory-ram') AND lower(name) LIKE '%ddr4%' AND lower(name) LIKE '%8gb%' THEN 'DDR4 8GB'

                -- Storage Tiers
                WHEN lower(category) IN ('storage', 'solid-state-drive') AND lower(name) LIKE '%nvme%' AND lower(name) LIKE '%2tb%' THEN 'NVMe 2TB'
                WHEN lower(category) IN ('storage', 'solid-state-drive') AND lower(name) LIKE '%nvme%' AND (lower(name) LIKE '%1tb%' OR lower(name) LIKE '%1000gb%') THEN 'NVMe 1TB'
                WHEN lower(category) IN ('storage', 'solid-state-drive') AND lower(name) LIKE '%nvme%' AND (lower(name) LIKE '%500gb%' OR lower(name) LIKE '%512gb%') THEN 'NVMe 500GB'
                WHEN lower(category) IN ('storage', 'solid-state-drive') AND lower(name) LIKE '%sata%' AND (lower(name) LIKE '%1tb%' OR lower(name) LIKE '%1000gb%') THEN 'SATA 1TB'
                WHEN lower(category) IN ('storage', 'solid-state-drive') AND lower(name) LIKE '%sata%' AND (lower(name) LIKE '%500gb%' OR lower(name) LIKE '%512gb%') THEN 'SATA 500GB'
                WHEN lower(category) IN ('storage', 'solid-state-drive') AND (lower(name) LIKE '%hdd%' OR lower(name) LIKE '%hard disk%') THEN 'HDD'

                -- Motherboard Tiers
                WHEN lower(category) = 'motherboard' AND (lower(name) LIKE '%z790%' OR lower(name) LIKE '%z890%') THEN 'Intel Z790/Z890'
                WHEN lower(category) = 'motherboard' AND lower(name) LIKE '%b760%' THEN 'Intel B760'
                WHEN lower(category) = 'motherboard' AND lower(name) LIKE '%h610%' THEN 'Intel H610'
                WHEN lower(category) = 'motherboard' AND (lower(name) LIKE '%x670%' OR lower(name) LIKE '%x870%') THEN 'AMD X670/X870'
                WHEN lower(category) = 'motherboard' AND lower(name) LIKE '%b650%' THEN 'AMD B650'
                WHEN lower(category) = 'motherboard' AND lower(name) LIKE '%b550%' THEN 'AMD B550'
                WHEN lower(category) = 'motherboard' AND lower(name) LIKE '%a620%' THEN 'AMD A620'

                -- PSU Tiers
                WHEN lower(category) = 'psu' AND (lower(name) LIKE '%1000w%' OR lower(name) LIKE '%1200w%') THEN '1000W+'
                WHEN lower(category) = 'psu' AND lower(name) LIKE '%850w%' THEN '850W'
                WHEN lower(category) = 'psu' AND lower(name) LIKE '%750w%' THEN '750W'
                WHEN lower(category) = 'psu' AND lower(name) LIKE '%650w%' THEN '650W'
                WHEN lower(category) = 'psu' AND lower(name) LIKE '%550w%' THEN '550W'
                WHEN lower(category) = 'psu' AND lower(name) LIKE '%500w%' THEN '500W'

                ELSE 'Standard'
            END AS tier,
            CASE 
                WHEN lower(name) LIKE '%tray%' THEN 'Tray'
                WHEN lower(name) LIKE '%box%' THEN 'Box'
                ELSE 'Standard'
            END AS packaging,
            CASE 
                WHEN lower(category) IN ('storage', 'solid-state-drive', 'memory', 'memory-ram') THEN
                    ROUND(price / NULLIF(
                        CASE 
                            WHEN upper(regexp_extract(name, '(?i)(\\d+)\\s*(GB|TB)', 2)) = 'TB' 
                            THEN TRY_CAST(regexp_extract(name, '(?i)(\\d+)\\s*(GB|TB)', 1) AS INT) * 1000
                            ELSE TRY_CAST(regexp_extract(name, '(?i)(\\d+)\\s*(GB|TB)', 1) AS INT)
                        END, 0
                    ))
                ELSE NULL
            END AS price_per_gb
        FROM read_json_auto('{glob_pattern}')
        WHERE price > 0
    """)

    return conn


def query_to_dicts(conn: duckdb.DuckDBPyConnection, sql: str) -> List[Dict[str, Any]]:
    """Execute SQL query and convert results to list of dictionaries without pandas."""
    cur = conn.execute(sql)
    cols = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def extract_analytics(conn: duckdb.DuckDBPyConnection) -> Dict[str, Any]:
    """Execute analytical queries in DuckDB and return dashboard data payload."""
    # 1. High-level KPIs
    kpis = query_to_dicts(conn, """
        SELECT 
            count(*) as total_items,
            count(DISTINCT source) as total_retailers,
            count(DISTINCT std_category) as total_categories,
            min(price) as min_price,
            avg(price)::int as avg_price,
            max(price) as max_price,
            count(*) FILTER (WHERE source = 'enterkomputer') as count_enterkomputer,
            count(*) FILTER (WHERE source = 'viraindo') as count_viraindo,
            max(scraped_at) as last_updated
        FROM raw_catalog
    """)[0]

    # 2. Category Distribution
    cat_dist = query_to_dicts(conn, """
        SELECT std_category as category, count(*) as count
        FROM raw_catalog
        GROUP BY std_category
        ORDER BY count DESC
    """)

    # 3. Retailer Price Comparison by Category
    retailer_comparison = query_to_dicts(conn, """
        SELECT 
            std_category as category,
            avg(price) FILTER (WHERE source = 'enterkomputer')::int as avg_enterkomputer,
            avg(price) FILTER (WHERE source = 'viraindo')::int as avg_viraindo,
            median(price) FILTER (WHERE source = 'enterkomputer')::int as median_enterkomputer,
            median(price) FILTER (WHERE source = 'viraindo')::int as median_viraindo,
            count(*) as total_count
        FROM raw_catalog
        GROUP BY std_category
        HAVING count(*) FILTER (WHERE source = 'enterkomputer') > 0 
           AND count(*) FILTER (WHERE source = 'viraindo') > 0
        ORDER BY total_count DESC
    """)

    # 4. GPU Benchmarks
    gpu_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price
        FROM raw_catalog WHERE std_category = 'GPU' AND tier != 'Standard'
        GROUP BY tier ORDER BY avg_price DESC
    """)

    # 5. CPU Benchmarks
    cpu_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price
        FROM raw_catalog WHERE std_category = 'CPU' AND tier != 'Standard'
        GROUP BY tier ORDER BY avg_price DESC
    """)

    # 6. RAM Benchmarks
    ram_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price
        FROM raw_catalog WHERE std_category = 'RAM' AND tier != 'Standard'
        GROUP BY tier ORDER BY avg_price DESC
    """)

    # 7. Storage Benchmarks
    storage_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price, avg(price_per_gb)::int as avg_price_per_gb
        FROM raw_catalog WHERE std_category = 'Storage' AND tier != 'Standard'
        GROUP BY tier ORDER BY avg_price DESC
    """)

    # 8. Motherboard Benchmarks
    mobo_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price
        FROM raw_catalog WHERE std_category = 'Motherboard' AND tier != 'Standard'
        GROUP BY tier ORDER BY avg_price DESC
    """)

    # 9. PSU Benchmarks
    psu_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price
        FROM raw_catalog WHERE std_category = 'PSU' AND tier != 'Standard'
        GROUP BY tier ORDER BY avg_price DESC
    """)

    # 10. Tray vs Box CPU Premium
    tray_vs_box = query_to_dicts(conn, """
        SELECT 
            tier,
            avg(price) FILTER (WHERE packaging = 'Tray')::int as avg_tray,
            avg(price) FILTER (WHERE packaging = 'Box')::int as avg_box,
            count(*) as count
        FROM raw_catalog
        WHERE std_category = 'CPU' AND tier IN ('AMD Ryzen 5', 'AMD Ryzen 7', 'Intel Core i5', 'Intel Core i7')
        GROUP BY tier
        HAVING avg_tray > 0 AND avg_box > 0
        ORDER BY count DESC
    """)

    # 11. Full Products Table (All 7,966+ rows)
    table_items = query_to_dicts(conn, """
        SELECT 
            name,
            std_category as category,
            tier,
            brand,
            packaging,
            source,
            price,
            price_per_gb,
            url
        FROM raw_catalog
        ORDER BY std_category, price ASC
    """)

    return {
        "kpis": kpis,
        "cat_dist": cat_dist,
        "retailer_comparison": retailer_comparison,
        "gpu_benchmarks": gpu_benchmarks,
        "cpu_benchmarks": cpu_benchmarks,
        "ram_benchmarks": ram_benchmarks,
        "storage_benchmarks": storage_benchmarks,
        "mobo_benchmarks": mobo_benchmarks,
        "psu_benchmarks": psu_benchmarks,
        "tray_vs_box": tray_vs_box,
        "table_items": table_items,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def render_html_report(analytics: Dict[str, Any], output_path: Path) -> None:
    """Generate modern, dark-themed standalone HTML dashboard."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    analytics_json = json.dumps(analytics, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>pcomp — Indonesian PC Hardware Price Intelligence</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: #1f293d;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --accent-cyan: #06b6d4;
      --accent-emerald: #10b981;
      --accent-purple: #8b5cf6;
      --accent-amber: #f59e0b;
      --accent-rose: #f43f5e;
      --enterkomputer: #3b82f6;
      --viraindo: #10b981;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text-main);
      line-height: 1.5;
      padding: 1.5rem 2rem 4rem;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 1.25rem;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .brand {{ display: flex; align-items: center; gap: 0.75rem; }}
    .brand-icon {{
      width: 42px;
      height: 42px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.3rem;
      color: white;
    }}
    .brand-text h1 {{ font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; }}
    .brand-text p {{ font-size: 0.85rem; color: var(--text-muted); }}
    .header-badge {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 9999px;
      padding: 0.4rem 1rem;
      font-size: 0.8rem;
      color: #94a3b8;
    }}
    .header-badge strong {{ color: var(--accent-emerald); }}

    /* KPI Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 1.25rem;
      margin-bottom: 2rem;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
      position: relative;
      overflow: hidden;
    }}
    .kpi-card::after {{
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--accent-cyan), var(--accent-emerald));
    }}
    .kpi-label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 0.4rem;
    }}
    .kpi-value {{
      font-size: 1.75rem;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.02em;
    }}
    .kpi-subtext {{ font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem; }}

    /* Category Nav Tabs */
    .section-nav {{
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1.5rem;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 0.75rem;
      overflow-x: auto;
    }}
    .nav-tab {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 0.5rem 1rem;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.4rem;
      white-space: nowrap;
      transition: all 0.15s ease;
    }}
    .nav-tab:hover {{ color: var(--text-main); background: #1f293d; }}
    .nav-tab.active {{
      background: #1e293b;
      color: var(--accent-cyan);
      border-color: var(--accent-cyan);
    }}

    /* Charts Section */
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2.5rem;
    }}
    .chart-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
    }}
    .chart-card h2 {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem; }}
    .chart-card p {{ font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1.25rem; }}
    .chart-container {{ position: relative; width: 100%; height: 290px; }}

    /* Table & Explorer Section */
    .explorer-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
    }}
    .explorer-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.25rem;
    }}
    .explorer-controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: center;
      width: 100%;
    }}
    .search-input {{
      flex: 1;
      min-width: 240px;
      background: #0d131f;
      border: 1px solid #2d3748;
      border-radius: 8px;
      padding: 0.6rem 1rem;
      color: white;
      font-size: 0.9rem;
      outline: none;
    }}
    .search-input:focus {{ border-color: var(--accent-cyan); }}
    .filter-btn-group {{ display: flex; gap: 0.4rem; flex-wrap: wrap; }}
    .filter-btn {{
      background: #1f2937;
      border: 1px solid #374151;
      color: #d1d5db;
      padding: 0.4rem 0.85rem;
      border-radius: 6px;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.15s ease;
    }}
    .filter-btn.active {{
      background: var(--accent-cyan);
      color: #000;
      font-weight: 700;
      border-color: var(--accent-cyan);
    }}
    .table-container {{
      overflow-x: auto;
      margin-top: 1rem;
      border: 1px solid var(--card-border);
      border-radius: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
      text-align: left;
    }}
    th {{
      background: #162032;
      color: #94a3b8;
      padding: 0.75rem 1rem;
      font-weight: 600;
      border-bottom: 1px solid var(--card-border);
    }}
    td {{
      padding: 0.7rem 1rem;
      border-bottom: 1px solid #1a2333;
      color: #e2e8f0;
    }}
    tr:hover td {{ background: #172236; }}
    .badge {{
      display: inline-block;
      padding: 0.2rem 0.6rem;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
    }}
    .badge-enterkomputer {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); }}
    .badge-viraindo {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4); }}
    .badge-tier {{ background: #334155; color: #cbd5e1; }}
    .badge-brand {{ background: #1e1b4b; color: #a5b4fc; border: 1px solid #4338ca; }}
    .badge-unit {{ background: #064e3b; color: #6ee7b7; font-size: 0.7rem; }}
    .price-cell {{
      font-weight: 700;
      color: var(--accent-emerald);
      font-variant-numeric: tabular-nums;
    }}
    .table-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 1rem;
      font-size: 0.85rem;
      color: var(--text-muted);
    }}
    .pagination-btn {{
      background: #1f2937;
      border: 1px solid #374151;
      color: white;
      padding: 0.35rem 0.8rem;
      border-radius: 6px;
      cursor: pointer;
    }}
    .pagination-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
    a.item-link {{ color: var(--accent-cyan); text-decoration: none; }}
    a.item-link:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>

  <header>
    <div class="brand">
      <div class="brand-icon">⚡</div>
      <div class="brand-text">
        <h1>pcomp — Indonesian PC Hardware Price Intelligence</h1>
        <p>Local DuckDB Analytics & Price Comparison Engine (EnterKomputer & Viraindo)</p>
      </div>
    </div>
    <div class="header-badge">
      Generated: <strong>{analytics["generated_at"]}</strong> • Engine: <strong>DuckDB (Local-First)</strong>
    </div>
  </header>

  <!-- Key Metrics Row -->
  <section class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-label">Total Tracked Products</div>
      <div class="kpi-value">{analytics["kpis"]["total_items"]:,}</div>
      <div class="kpi-subtext">{analytics["kpis"]["total_categories"]} hardware categories</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">EnterKomputer Catalog</div>
      <div class="kpi-value">{analytics["kpis"]["count_enterkomputer"]:,}</div>
      <div class="kpi-subtext">Live JSON API scrape</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Viraindo Catalog</div>
      <div class="kpi-value">{analytics["kpis"]["count_viraindo"]:,}</div>
      <div class="kpi-subtext">Pricelist table scrape</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Average Catalog Price</div>
      <div class="kpi-value">Rp {analytics["kpis"]["avg_price"]:,}</div>
      <div class="kpi-subtext">Range: Rp {analytics["kpis"]["min_price"]:,} – Rp {analytics["kpis"]["max_price"]:,}</div>
    </div>
  </section>

  <!-- Interactive Analytical Section Tabs -->
  <nav class="section-nav">
    <button class="nav-tab active" onclick="switchTab('tab-overview')">📊 Market Overview</button>
    <button class="nav-tab" onclick="switchTab('tab-gpu')">🎮 GPU Benchmarks</button>
    <button class="nav-tab" onclick="switchTab('tab-cpu')">🧠 CPU & Tray vs Box</button>
    <button class="nav-tab" onclick="switchTab('tab-ram')">⚡ RAM (DDR4 vs DDR5)</button>
    <button class="nav-tab" onclick="switchTab('tab-storage')">💾 Storage (NVMe / SATA Value)</button>
    <button class="nav-tab" onclick="switchTab('tab-mobo-psu')">🔌 Motherboard & PSU</button>
  </nav>

  <!-- TAB 1: Market Overview -->
  <div id="tab-overview" class="tab-content active">
    <section class="charts-grid">
      <div class="chart-card">
        <h2>Average Price: EnterKomputer vs Viraindo</h2>
        <p>Direct retailer comparison across identical hardware categories (IDR Millions)</p>
        <div class="chart-container">
          <canvas id="retailerCompChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h2>Catalog Share by Category</h2>
        <p>Distribution of {analytics["kpis"]["total_items"]:,} scraped inventory items</p>
        <div class="chart-container">
          <canvas id="categoryShareChart"></canvas>
        </div>
      </div>
    </section>
  </div>

  <!-- TAB 2: GPU Benchmarks -->
  <div id="tab-gpu" class="tab-content">
    <section class="charts-grid">
      <div class="chart-card" style="grid-column: 1 / -1;">
        <h2>GPU Series Price Benchmarks (Median IDR)</h2>
        <p>Market benchmarks across NVIDIA GeForce RTX, AMD Radeon RX, and Intel Arc series</p>
        <div class="chart-container" style="height: 350px;">
          <canvas id="gpuTiersChart"></canvas>
        </div>
      </div>
    </section>
  </div>

  <!-- TAB 3: CPU Benchmarks & Tray vs Box -->
  <div id="tab-cpu" class="tab-content">
    <section class="charts-grid">
      <div class="chart-card">
        <h2>CPU Series Benchmarks (Median IDR)</h2>
        <p>Market benchmark across AMD Ryzen Series & Intel Core Series</p>
        <div class="chart-container">
          <canvas id="cpuTiersChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h2>Tray vs Box OEM Price Premium</h2>
        <p>Direct cost difference: OEM Tray (no box/cooler) vs Retail Box</p>
        <div class="chart-container">
          <canvas id="trayBoxChart"></canvas>
        </div>
      </div>
    </section>
  </div>

  <!-- TAB 4: RAM Benchmarks -->
  <div id="tab-ram" class="tab-content">
    <section class="charts-grid">
      <div class="chart-card" style="grid-column: 1 / -1;">
        <h2>RAM Memory Capacity & Generation Benchmarks</h2>
        <p>Median prices for DDR5 vs DDR4 across 8GB, 16GB, 32GB, and 64GB kits</p>
        <div class="chart-container" style="height: 330px;">
          <canvas id="ramTiersChart"></canvas>
        </div>
      </div>
    </section>
  </div>

  <!-- TAB 5: Storage Benchmarks -->
  <div id="tab-storage" class="tab-content">
    <section class="charts-grid">
      <div class="chart-card">
        <h2>Storage Form Factor Benchmarks (Median IDR)</h2>
        <p>NVMe High-Speed vs SATA Budget SSDs across 500GB, 1TB, and 2TB</p>
        <div class="chart-container">
          <canvas id="storageTiersChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h2>SSD Unit Economics: Price per GB (IDR / GB)</h2>
        <p>Lowest price-per-gigabyte sweet spot across storage tiers</p>
        <div class="chart-container">
          <canvas id="storagePerGbChart"></canvas>
        </div>
      </div>
    </section>
  </div>

  <!-- TAB 6: Motherboard & PSU -->
  <div id="tab-mobo-psu" class="tab-content">
    <section class="charts-grid">
      <div class="chart-card">
        <h2>Motherboard Chipset Price Tiers</h2>
        <p>Intel (Z790/B760/H610) vs AMD (X670/B650/B550/A620) Chipsets</p>
        <div class="chart-container">
          <canvas id="moboTiersChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h2>Power Supply (PSU) Wattage Tiers</h2>
        <p>Median market prices across 500W to 1000W+ power supplies</p>
        <div class="chart-container">
          <canvas id="psuTiersChart"></canvas>
        </div>
      </div>
    </section>
  </div>

  <!-- Interactive Product Explorer Table -->
  <section class="explorer-card">
    <div class="explorer-header">
      <div>
        <h2>Hardware Product Explorer ({analytics["kpis"]["total_items"]:,} Products)</h2>
        <p>Instant search and multi-retailer catalog inspector powered by local DuckDB</p>
      </div>
    </div>

    <div class="explorer-controls">
      <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search product name, chipset, or brand (e.g. RTX 4070, B650, DDR5, NVMe, Corsair, Seasonic)..." oninput="handleSearch()">
      
      <div class="filter-btn-group" id="categoryFilters">
        <button class="filter-btn active" data-cat="all" onclick="setCategoryFilter('all')">All Categories</button>
        <button class="filter-btn" data-cat="GPU" onclick="setCategoryFilter('GPU')">GPU ({len([x for x in analytics['table_items'] if x['category'] == 'GPU']):,})</button>
        <button class="filter-btn" data-cat="CPU" onclick="setCategoryFilter('CPU')">CPU ({len([x for x in analytics['table_items'] if x['category'] == 'CPU']):,})</button>
        <button class="filter-btn" data-cat="RAM" onclick="setCategoryFilter('RAM')">RAM ({len([x for x in analytics['table_items'] if x['category'] == 'RAM']):,})</button>
        <button class="filter-btn" data-cat="Storage" onclick="setCategoryFilter('Storage')">Storage ({len([x for x in analytics['table_items'] if x['category'] == 'Storage']):,})</button>
        <button class="filter-btn" data-cat="Motherboard" onclick="setCategoryFilter('Motherboard')">Motherboard ({len([x for x in analytics['table_items'] if x['category'] == 'Motherboard']):,})</button>
        <button class="filter-btn" data-cat="PSU" onclick="setCategoryFilter('PSU')">PSU ({len([x for x in analytics['table_items'] if x['category'] == 'PSU']):,})</button>
        <button class="filter-btn" data-cat="Monitor" onclick="setCategoryFilter('Monitor')">Monitor ({len([x for x in analytics['table_items'] if x['category'] == 'Monitor']):,})</button>
        <button class="filter-btn" data-cat="Cooler" onclick="setCategoryFilter('Cooler')">Cooler ({len([x for x in analytics['table_items'] if x['category'] == 'Cooler']):,})</button>
        <button class="filter-btn" data-cat="Casing" onclick="setCategoryFilter('Casing')">Casing ({len([x for x in analytics['table_items'] if x['category'] == 'Casing']):,})</button>
        <button class="filter-btn" data-cat="Peripheral" onclick="setCategoryFilter('Peripheral')">Peripherals ({len([x for x in analytics['table_items'] if x['category'] == 'Peripheral']):,})</button>
      </div>

      <div class="filter-btn-group" id="retailerFilters">
        <button class="filter-btn active" data-ret="all" onclick="setRetailerFilter('all')">All Retailers</button>
        <button class="filter-btn" data-ret="enterkomputer" onclick="setRetailerFilter('enterkomputer')">EnterKomputer</button>
        <button class="filter-btn" data-ret="viraindo" onclick="setRetailerFilter('viraindo')">Viraindo</button>
      </div>
    </div>

    <div class="table-container">
      <table id="productTable">
        <thead>
          <tr>
            <th>Product Name</th>
            <th width="110">Category</th>
            <th width="150">Tier / Series</th>
            <th width="110">Brand</th>
            <th width="130">Retailer</th>
            <th width="150" style="text-align: right;">Price (IDR)</th>
          </tr>
        </thead>
        <tbody id="tableBody">
          <!-- Dynamically populated via JavaScript -->
        </tbody>
      </table>
    </div>

    <div class="table-footer">
      <div id="tableInfo">Showing 0 of 0 products</div>
      <div style="display: flex; gap: 0.5rem; align-items: center;">
        <button id="prevBtn" class="pagination-btn" onclick="changePage(-1)">Previous</button>
        <span id="pageIndicator">Page 1</span>
        <button id="nextBtn" class="pagination-btn" onclick="changePage(1)">Next</button>
      </div>
    </div>
  </section>

  <script>
    const data = {analytics_json};

    function formatRp(val) {{
      return "Rp " + Number(val).toLocaleString("id-ID");
    }}

    function switchTab(tabId) {{
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      event.currentTarget.classList.add('active');
    }}

    // Render All Charts on Load
    window.addEventListener("DOMContentLoaded", () => {{
      // 1. Retailer Price Comparison Bar Chart
      const retCtx = document.getElementById("retailerCompChart").getContext("2d");
      new Chart(retCtx, {{
        type: 'bar',
        data: {{
          labels: data.retailer_comparison.map(d => d.category),
          datasets: [
            {{ label: 'EnterKomputer (Avg Jt)', data: data.retailer_comparison.map(d => d.avg_enterkomputer / 1000000), backgroundColor: '#3b82f6', borderRadius: 6 }},
            {{ label: 'Viraindo (Avg Jt)', data: data.retailer_comparison.map(d => d.avg_viraindo / 1000000), backgroundColor: '#10b981', borderRadius: 6 }}
          ]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#9ca3af' }} }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }}
          }}
        }}
      }});

      // 2. Category Share Doughnut
      const shareCtx = document.getElementById("categoryShareChart").getContext("2d");
      new Chart(shareCtx, {{
        type: 'doughnut',
        data: {{
          labels: data.cat_dist.map(d => d.category),
          datasets: [{{
            data: data.cat_dist.map(d => d.count),
            backgroundColor: ['#06b6d4', '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899', '#64748b'],
            borderColor: '#111827', borderWidth: 2
          }}]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ position: 'right', labels: {{ color: '#9ca3af', font: {{ size: 11 }} }} }} }}
        }}
      }});

      // 3. GPU Tiers Horizontal Bar
      const gpuCtx = document.getElementById("gpuTiersChart").getContext("2d");
      new Chart(gpuCtx, {{
        type: 'bar',
        data: {{
          labels: data.gpu_benchmarks.map(d => d.tier),
          datasets: [{{
            label: 'Median Price (Jt)',
            data: data.gpu_benchmarks.map(d => (d.median_price / 1000000).toFixed(2)),
            backgroundColor: '#06b6d4', borderRadius: 6
          }}]
        }},
        options: {{
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ display: false }} }}
          }}
        }}
      }});

      // 4. CPU Tiers Horizontal Bar
      const cpuCtx = document.getElementById("cpuTiersChart").getContext("2d");
      new Chart(cpuCtx, {{
        type: 'bar',
        data: {{
          labels: data.cpu_benchmarks.map(d => d.tier),
          datasets: [{{
            label: 'Median Price (Jt)',
            data: data.cpu_benchmarks.map(d => (d.median_price / 1000000).toFixed(2)),
            backgroundColor: '#8b5cf6', borderRadius: 6
          }}]
        }},
        options: {{
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ display: false }} }}
          }}
        }}
      }});

      // 5. Tray vs Box CPU Chart
      const trayCtx = document.getElementById("trayBoxChart").getContext("2d");
      new Chart(trayCtx, {{
        type: 'bar',
        data: {{
          labels: data.tray_vs_box.map(d => d.tier),
          datasets: [
            {{ label: 'OEM Tray (Avg Jt)', data: data.tray_vs_box.map(d => (d.avg_tray / 1000000).toFixed(2)), backgroundColor: '#f59e0b', borderRadius: 6 }},
            {{ label: 'Retail Box (Avg Jt)', data: data.tray_vs_box.map(d => (d.avg_box / 1000000).toFixed(2)), backgroundColor: '#3b82f6', borderRadius: 6 }}
          ]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ labels: {{ color: '#9ca3af' }} }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }}
          }}
        }}
      }});

      // 6. RAM Benchmarks
      const ramCtx = document.getElementById("ramTiersChart").getContext("2d");
      new Chart(ramCtx, {{
        type: 'bar',
        data: {{
          labels: data.ram_benchmarks.map(d => d.tier),
          datasets: [{{
            label: 'Median Price (Jt)',
            data: data.ram_benchmarks.map(d => (d.median_price / 1000000).toFixed(2)),
            backgroundColor: '#10b981', borderRadius: 6
          }}]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }}
          }}
        }}
      }});

      // 7. Storage Benchmarks
      const stCtx = document.getElementById("storageTiersChart").getContext("2d");
      new Chart(stCtx, {{
        type: 'bar',
        data: {{
          labels: data.storage_benchmarks.map(d => d.tier),
          datasets: [{{
            label: 'Median Price (Jt)',
            data: data.storage_benchmarks.map(d => (d.median_price / 1000000).toFixed(2)),
            backgroundColor: '#06b6d4', borderRadius: 6
          }}]
        }},
        options: {{
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ display: false }} }}
          }}
        }}
      }});

      // 8. Storage Unit Price (IDR / GB)
      const stGbCtx = document.getElementById("storagePerGbChart").getContext("2d");
      const validGb = data.storage_benchmarks.filter(d => d.avg_price_per_gb > 0);
      new Chart(stGbCtx, {{
        type: 'bar',
        data: {{
          labels: validGb.map(d => d.tier),
          datasets: [{{
            label: 'Avg IDR / GB',
            data: validGb.map(d => d.avg_price_per_gb),
            backgroundColor: '#f43f5e', borderRadius: 6
          }}]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }}
          }}
        }}
      }});

      // 9. Motherboard Benchmarks
      const mbCtx = document.getElementById("moboTiersChart").getContext("2d");
      new Chart(mbCtx, {{
        type: 'bar',
        data: {{
          labels: data.mobo_benchmarks.map(d => d.tier),
          datasets: [{{
            label: 'Median Price (Jt)',
            data: data.mobo_benchmarks.map(d => (d.median_price / 1000000).toFixed(2)),
            backgroundColor: '#8b5cf6', borderRadius: 6
          }}]
        }},
        options: {{
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ display: false }} }}
          }}
        }}
      }});

      // 10. PSU Benchmarks
      const psuCtx = document.getElementById("psuTiersChart").getContext("2d");
      new Chart(psuCtx, {{
        type: 'bar',
        data: {{
          labels: data.psu_benchmarks.map(d => d.tier),
          datasets: [{{
            label: 'Median Price (Jt)',
            data: data.psu_benchmarks.map(d => (d.median_price / 1000000).toFixed(2)),
            backgroundColor: '#f59e0b', borderRadius: 6
          }}]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }}
          }}
        }}
      }});

      // Initial table render
      renderTable();
    }});

    // Table Filter and Pagination Logic
    let currentCategory = 'all';
    let currentRetailer = 'all';
    let searchQuery = '';
    let currentPage = 1;
    const pageSize = 50;
    let filteredItems = [];

    function setCategoryFilter(cat) {{
      currentCategory = cat;
      document.querySelectorAll('#categoryFilters .filter-btn').forEach(btn => {{
        btn.classList.toggle('active', btn.getAttribute('data-cat') === cat);
      }});
      currentPage = 1;
      renderTable();
    }}

    function setRetailerFilter(ret) {{
      currentRetailer = ret;
      document.querySelectorAll('#retailerFilters .filter-btn').forEach(btn => {{
        btn.classList.toggle('active', btn.getAttribute('data-ret') === ret);
      }});
      currentPage = 1;
      renderTable();
    }}

    function handleSearch() {{
      searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();
      currentPage = 1;
      renderTable();
    }}

    function changePage(delta) {{
      currentPage += delta;
      renderTable();
    }}

    function renderTable() {{
      filteredItems = data.table_items.filter(item => {{
        const matchCat = currentCategory === 'all' || item.category === currentCategory;
        const matchRet = currentRetailer === 'all' || item.source === currentRetailer;
        const matchSearch = !searchQuery || 
          item.name.toLowerCase().includes(searchQuery) || 
          item.tier.toLowerCase().includes(searchQuery) ||
          item.brand.toLowerCase().includes(searchQuery);
        return matchCat && matchRet && matchSearch;
      }});

      const totalPages = Math.ceil(filteredItems.length / pageSize) || 1;
      if (currentPage < 1) currentPage = 1;
      if (currentPage > totalPages) currentPage = totalPages;

      const startIndex = (currentPage - 1) * pageSize;
      const pageItems = filteredItems.slice(startIndex, startIndex + pageSize);

      const tbody = document.getElementById('tableBody');
      tbody.innerHTML = '';

      if (pageItems.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 2rem; color: #94a3b8;">No matching products found.</td></tr>';
      }} else {{
        pageItems.forEach(item => {{
          const tr = document.createElement('tr');
          const nameHtml = item.url 
            ? `<a href="${{item.url}}" target="_blank" rel="noopener noreferrer" class="item-link">${{item.name}}</a>`
            : item.name;

          const unitBadge = item.price_per_gb 
            ? `<span class="badge badge-unit">Rp ${{item.price_per_gb.toLocaleString("id-ID")}}/GB</span>`
            : '';

          tr.innerHTML = `
            <td>${{nameHtml}}</td>
            <td><span class="badge" style="background:#1e293b; color:#94a3b8;">${{item.category}}</span></td>
            <td><span class="badge badge-tier">${{item.tier}}</span></td>
            <td><span class="badge badge-brand">${{item.brand}}</span></td>
            <td><span class="badge badge-${{item.source}}">${{item.source}}</span></td>
            <td style="text-align: right;" class="price-cell">
              ${{formatRp(item.price)}}
              ${{unitBadge ? '<br>' + unitBadge : ''}}
            </td>
          `;
          tbody.appendChild(tr);
        }});
      }}

      // Update Pagination Controls
      document.getElementById('tableInfo').textContent = `Showing ${{filteredItems.length === 0 ? 0 : startIndex + 1}} to ${{Math.min(startIndex + pageSize, filteredItems.length)}} of ${{filteredItems.length.toLocaleString()}} products`;
      document.getElementById('pageIndicator').textContent = `Page ${{currentPage}} of ${{totalPages}}`;
      document.getElementById('prevBtn').disabled = currentPage <= 1;
      document.getElementById('nextBtn').disabled = currentPage >= totalPages;
    }}
  </script>
</body>
</html>
"""

    output_path.write_text(html_content, encoding="utf-8")
    logger.info(f"Dashboard successfully written to: {output_path} ({len(html_content)} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate local pcomp PC hardware price intelligence HTML report")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Path to hardware scraped data folder",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_HTML,
        help="Destination path for generated dashboard HTML",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Automatically launch the generated HTML report in your browser",
    )

    args = parser.parse_args()

    try:
        conn = load_hardware_data(args.data_dir)
        analytics = extract_analytics(conn)
        render_html_report(analytics, args.output)

        print(f"\n✨ pcomp local dashboard generated successfully!")
        print(f"📊 Report: file://{args.output.resolve()}\n")

        if args.open:
            webbrowser.open(f"file://{args.output.resolve()}")

    except Exception as e:
        logger.exception(f"Failed to generate report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
