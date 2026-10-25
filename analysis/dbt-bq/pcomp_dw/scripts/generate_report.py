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

    # Normalize categories & hardware tiers in a DuckDB analytical view
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
                WHEN lower(category) IN ('storage', 'solid-state-drive') THEN 'Storage'
                WHEN lower(category) IN ('motherboard') THEN 'Motherboard'
                WHEN lower(category) IN ('psu') THEN 'Power Supply'
                WHEN lower(category) IN ('casing') THEN 'Casing'
                ELSE 'Other'
            END AS std_category,
            CASE
                -- GPU Tiers
                WHEN lower(name) LIKE '%rtx 4090%' THEN 'NVIDIA RTX 4090'
                WHEN lower(name) LIKE '%rtx 4080%' THEN 'NVIDIA RTX 4080'
                WHEN lower(name) LIKE '%rtx 4070 ti%' THEN 'NVIDIA RTX 4070 Ti'
                WHEN lower(name) LIKE '%rtx 4070%' THEN 'NVIDIA RTX 4070'
                WHEN lower(name) LIKE '%rtx 4060 ti%' THEN 'NVIDIA RTX 4060 Ti'
                WHEN lower(name) LIKE '%rtx 4060%' THEN 'NVIDIA RTX 4060'
                WHEN lower(name) LIKE '%rtx 3060%' THEN 'NVIDIA RTX 3060'
                WHEN lower(name) LIKE '%rx 7900%' THEN 'AMD RX 7900'
                WHEN lower(name) LIKE '%rx 7800%' THEN 'AMD RX 7800'
                WHEN lower(name) LIKE '%rx 7700%' THEN 'AMD RX 7700'
                WHEN lower(name) LIKE '%rx 6600%' THEN 'AMD RX 6600'
                WHEN lower(name) LIKE '%arc a770%' OR lower(name) LIKE '%arc a750%' THEN 'Intel Arc 7-Series'

                -- CPU Tiers
                WHEN lower(name) LIKE '%ryzen 9%' THEN 'AMD Ryzen 9'
                WHEN lower(name) LIKE '%ryzen 7%' THEN 'AMD Ryzen 7'
                WHEN lower(name) LIKE '%ryzen 5%' THEN 'AMD Ryzen 5'
                WHEN lower(name) LIKE '%ryzen 3%' THEN 'AMD Ryzen 3'
                WHEN lower(name) LIKE '%core i9%' THEN 'Intel Core i9'
                WHEN lower(name) LIKE '%core i7%' THEN 'Intel Core i7'
                WHEN lower(name) LIKE '%core i5%' THEN 'Intel Core i5'
                WHEN lower(name) LIKE '%core i3%' THEN 'Intel Core i3'

                -- RAM Tiers
                WHEN lower(name) LIKE '%ddr5%' AND lower(name) LIKE '%32gb%' THEN 'DDR5 32GB'
                WHEN lower(name) LIKE '%ddr5%' AND lower(name) LIKE '%16gb%' THEN 'DDR5 16GB'
                WHEN lower(name) LIKE '%ddr4%' AND lower(name) LIKE '%32gb%' THEN 'DDR4 32GB'
                WHEN lower(name) LIKE '%ddr4%' AND lower(name) LIKE '%16gb%' THEN 'DDR4 16GB'
                WHEN lower(name) LIKE '%ddr4%' AND lower(name) LIKE '%8gb%' THEN 'DDR4 8GB'

                -- Storage Tiers
                WHEN lower(name) LIKE '%nvme%' AND lower(name) LIKE '%2tb%' THEN 'NVMe SSD 2TB'
                WHEN lower(name) LIKE '%nvme%' AND (lower(name) LIKE '%1tb%' OR lower(name) LIKE '%1000gb%') THEN 'NVMe SSD 1TB'
                WHEN lower(name) LIKE '%nvme%' AND (lower(name) LIKE '%500gb%' OR lower(name) LIKE '%512gb%') THEN 'NVMe SSD 500GB'
                WHEN lower(name) LIKE '%sata%' AND (lower(name) LIKE '%1tb%' OR lower(name) LIKE '%1000gb%') THEN 'SATA SSD 1TB'
                WHEN lower(name) LIKE '%sata%' AND (lower(name) LIKE '%500gb%' OR lower(name) LIKE '%512gb%') THEN 'SATA SSD 500GB'

                ELSE 'Standard'
            END AS tier
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
    kpi_query = """
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
    """
    kpis = query_to_dicts(conn, kpi_query)[0]

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
        SELECT 
            tier,
            count(*) as count,
            min(price) as min_price,
            median(price)::int as median_price,
            avg(price)::int as avg_price,
            max(price) as max_price
        FROM raw_catalog
        WHERE std_category = 'GPU' AND tier != 'Standard'
        GROUP BY tier
        ORDER BY avg_price DESC
    """)

    # 5. CPU Benchmarks
    cpu_benchmarks = query_to_dicts(conn, """
        SELECT 
            tier,
            count(*) as count,
            min(price) as min_price,
            median(price)::int as median_price,
            avg(price)::int as avg_price,
            max(price) as max_price
        FROM raw_catalog
        WHERE std_category = 'CPU' AND tier != 'Standard'
        GROUP BY tier
        ORDER BY avg_price DESC
    """)

    # 6. Sample / Top Products Table (up to 3000 rows for fast browser rendering)
    table_items = query_to_dicts(conn, """
        SELECT 
            name,
            std_category as category,
            tier,
            source,
            price,
            url
        FROM raw_catalog
        ORDER BY std_category, tier, price ASC
        LIMIT 3000
    """)

    return {
        "kpis": kpis,
        "cat_dist": cat_dist,
        "retailer_comparison": retailer_comparison,
        "gpu_benchmarks": gpu_benchmarks,
        "cpu_benchmarks": cpu_benchmarks,
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
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}
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
    .brand-text h1 {{
      font-size: 1.5rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}
    .brand-text p {{
      font-size: 0.85rem;
      color: var(--text-muted);
    }}
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
      top: 0;
      left: 0;
      right: 0;
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
    .kpi-subtext {{
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }}

    /* Charts Section */
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
    .chart-card h2 {{
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 0.25rem;
    }}
    .chart-card p {{
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-bottom: 1.25rem;
    }}
    .chart-container {{
      position: relative;
      width: 100%;
      height: 290px;
    }}

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
    .search-input:focus {{
      border-color: var(--accent-cyan);
    }}
    .filter-btn-group {{
      display: flex;
      gap: 0.4rem;
      flex-wrap: wrap;
    }}
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
    tr:hover td {{
      background: #172236;
    }}
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
    .pagination-btn:disabled {{
      opacity: 0.4;
      cursor: not-allowed;
    }}
    a.item-link {{
      color: var(--accent-cyan);
      text-decoration: none;
    }}
    a.item-link:hover {{
      text-decoration: underline;
    }}
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

  <!-- Interactive Charts Grid -->
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
      <p>Distribution of scraped inventory items across hardware components</p>
      <div class="chart-container">
        <canvas id="categoryShareChart"></canvas>
      </div>
    </div>
    <div class="chart-card">
      <h2>GPU Price Tiers (Median IDR)</h2>
      <p>Market benchmark across NVIDIA GeForce RTX, AMD Radeon RX & Intel Arc</p>
      <div class="chart-container">
        <canvas id="gpuTiersChart"></canvas>
      </div>
    </div>
    <div class="chart-card">
      <h2>CPU Price Tiers (Median IDR)</h2>
      <p>Market benchmark across AMD Ryzen Series & Intel Core Series</p>
      <div class="chart-container">
        <canvas id="cpuTiersChart"></canvas>
      </div>
    </div>
  </section>

  <!-- Interactive Product Explorer Table -->
  <section class="explorer-card">
    <div class="explorer-header">
      <div>
        <h2>Hardware Product Explorer</h2>
        <p>Instant search and multi-retailer catalog inspector powered by local DuckDB data</p>
      </div>
    </div>

    <div class="explorer-controls">
      <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search product name, chipset, or brand (e.g. RTX 4070, Ryzen 7, NVMe, Corsair)..." oninput="handleSearch()">
      
      <div class="filter-btn-group" id="categoryFilters">
        <button class="filter-btn active" onclick="setCategoryFilter('all')">All Categories</button>
        <button class="filter-btn" onclick="setCategoryFilter('GPU')">GPU</button>
        <button class="filter-btn" onclick="setCategoryFilter('CPU')">CPU</button>
        <button class="filter-btn" onclick="setCategoryFilter('RAM')">RAM</button>
        <button class="filter-btn" onclick="setCategoryFilter('Storage')">Storage</button>
        <button class="filter-btn" onclick="setCategoryFilter('Motherboard')">Motherboard</button>
        <button class="filter-btn" onclick="setCategoryFilter('Power Supply')">PSU</button>
        <button class="filter-btn" onclick="setCategoryFilter('Casing')">Casing</button>
      </div>

      <div class="filter-btn-group" id="retailerFilters">
        <button class="filter-btn active" onclick="setRetailerFilter('all')">All Retailers</button>
        <button class="filter-btn" onclick="setRetailerFilter('enterkomputer')">EnterKomputer</button>
        <button class="filter-btn" onclick="setRetailerFilter('viraindo')">Viraindo</button>
      </div>
    </div>

    <div class="table-container">
      <table id="productTable">
        <thead>
          <tr>
            <th>Product Name</th>
            <th width="110">Category</th>
            <th width="160">Tier / Series</th>
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

    // Format currency to IDR
    function formatRp(val) {{
      return "Rp " + Number(val).toLocaleString("id-ID");
    }}

    // Render Charts
    window.addEventListener("DOMContentLoaded", () => {{
      // 1. Retailer Price Comparison Bar Chart
      const retCtx = document.getElementById("retailerCompChart").getContext("2d");
      const cats = data.retailer_comparison.map(d => d.category);
      const enterAvg = data.retailer_comparison.map(d => d.avg_enterkomputer / 1000000);
      const viraAvg = data.retailer_comparison.map(d => d.avg_viraindo / 1000000);

      new Chart(retCtx, {{
        type: 'bar',
        data: {{
          labels: cats,
          datasets: [
            {{
              label: 'EnterKomputer (Avg Jt)',
              data: enterAvg,
              backgroundColor: '#3b82f6',
              borderRadius: 6
            }},
            {{
              label: 'Viraindo (Avg Jt)',
              data: viraAvg,
              backgroundColor: '#10b981',
              borderRadius: 6
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ labels: {{ color: '#9ca3af' }} }}
          }},
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
            backgroundColor: [
              '#06b6d4', '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899', '#64748b'
            ],
            borderColor: '#111827',
            borderWidth: 2
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ position: 'right', labels: {{ color: '#9ca3af', font: {{ size: 11 }} }} }}
          }}
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
            backgroundColor: '#06b6d4',
            borderRadius: 6
          }}]
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
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
            backgroundColor: '#8b5cf6',
            borderRadius: 6
          }}]
        }},
        options: {{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }} }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ display: false }} }}
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
    const pageSize = 40;
    let filteredItems = [];

    function setCategoryFilter(cat) {{
      currentCategory = cat;
      document.querySelectorAll('#categoryFilters .filter-btn').forEach(btn => {{
        btn.classList.toggle('active', btn.textContent.includes(cat) || (cat === 'all' && btn.textContent.includes('All')));
      }});
      currentPage = 1;
      renderTable();
    }}

    function setRetailerFilter(ret) {{
      currentRetailer = ret;
      document.querySelectorAll('#retailerFilters .filter-btn').forEach(btn => {{
        btn.classList.toggle('active', btn.textContent.toLowerCase().includes(ret) || (ret === 'all' && btn.textContent.includes('All')));
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
        const matchSearch = !searchQuery || item.name.toLowerCase().includes(searchQuery) || item.tier.toLowerCase().includes(searchQuery);
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
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 2rem; color: #94a3b8;">No matching products found.</td></tr>';
      }} else {{
        pageItems.forEach(item => {{
          const tr = document.createElement('tr');
          const nameHtml = item.url 
            ? `<a href="${{item.url}}" target="_blank" rel="noopener noreferrer" class="item-link">${{item.name}}</a>`
            : item.name;

          tr.innerHTML = `
            <td>${{nameHtml}}</td>
            <td><span class="badge" style="background:#1e293b; color:#94a3b8;">${{item.category}}</span></td>
            <td><span class="badge badge-tier">${{item.tier}}</span></td>
            <td><span class="badge badge-${{item.source}}">${{item.source}}</span></td>
            <td style="text-align: right;" class="price-cell">${{formatRp(item.price)}}</td>
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
