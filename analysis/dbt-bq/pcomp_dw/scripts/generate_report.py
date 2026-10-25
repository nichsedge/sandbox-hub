# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "duckdb>=0.10.0",
# ]
# ///
"""pcomp Local Price Intelligence & Dashboard Generator.

Queries local JSON snapshots from indoscraping using embedded DuckDB,
joins live PassMark 3D Graphics & CPU Compute benchmark datasets,
calculates Price-to-Performance value scores (points per IDR 1 Million),
and renders a self-contained, interactive HTML dashboard with Chart.js.
No BigQuery, no cloud credentials, and no external daemon needed.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pcomp-report")

DEFAULT_DATA_DIR = Path.home() / "Projects" / "indoscraping" / "data" / "hardware"
DEFAULT_BENCHMARK_FILE = (
    Path.home()
    / "Projects"
    / "indoscraping"
    / "data"
    / "benchmarks"
    / "passmark"
    / "latest.json"
)
DEFAULT_AI_CACHE_FILE = (
    Path.home()
    / "Projects"
    / "sandbox-hub"
    / "analysis"
    / "dbt-bq"
    / "pcomp_dw"
    / "data"
    / "ai_classified_hardware.json"
)
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
DEFAULT_PUBLIC_EXPORT_HTML = (
    Path.home()
    / "Projects"
    / "nichsedge.github.io"
    / "public"
    / "pcomp"
    / "index.html"
)


def load_ai_cache(cache_file: Path) -> dict[str, dict[str, str]]:
    """Load cached AI classifications from disk."""
    if not cache_file.exists():
        return {}
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not load AI cache from {cache_file}: {e}")
        return {}


def save_ai_cache(cache_file: Path, cache_data: dict[str, dict[str, str]]) -> None:
    """Save AI classifications dictionary to disk."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)
    logger.info(f"AI classification cache saved: {len(cache_data)} items at {cache_file}")


def classify_with_agent(
    names_to_classify: list[str],
    agent: str = "auto",
    batch_size: int = 15,
) -> dict[str, dict[str, str]]:
    """Classify unknown hardware product names using local CLI agents (agy or pi)."""
    if not names_to_classify:
        return {}

    results: dict[str, dict[str, str]] = {}
    batches = [
        names_to_classify[i : i + batch_size]
        for i in range(0, len(names_to_classify), batch_size)
    ]

    has_pi = shutil.which("pi") is not None
    has_agy = shutil.which("agy") is not None

    preferred_agent = agent
    if preferred_agent == "auto":
        preferred_agent = "pi" if has_pi else ("agy" if has_agy else "none")

    if preferred_agent == "none":
        logger.warning("Neither 'agy' nor 'pi' CLI was found. Skipping AI fallback classification.")
        return {}

    logger.info(
        f"Invoking agent '{preferred_agent}' to classify {len(names_to_classify)} unclassified hardware items..."
    )

    for idx, batch in enumerate(batches, 1):
        logger.info(f"Classifying batch {idx}/{len(batches)} ({len(batch)} items)...")
        prompt = (
            "You are an expert PC hardware classifier. Classify these computer hardware items into a single "
            "JSON dictionary mapping the exact original name to {\"tier\": \"<silicon chip model or series>\", \"brand\": \"<brand name>\"}.\n"
            "For tier, be specific to the chip/series family (e.g. 'RTX PRO 4500 Blackwell', 'Radeon 550', 'Bristol Ridge A8', 'Core 2 Duo').\n"
            "Items to classify:\n"
        )
        for i, item in enumerate(batch, 1):
            prompt += f"{i}. {item}\n"
        prompt += "\nReturn ONLY a raw valid JSON object without markdown backticks, fences, or explanations."

        cmd = []
        timeout_seconds = 45
        if preferred_agent == "pi":
            cmd = ["pi", "-p", "--no-session", "--no-tools", prompt]
            timeout_seconds = 30
        elif preferred_agent == "agy":
            cmd = ["agy", "--dangerously-skip-permissions", "-p", prompt]
            timeout_seconds = 60

        try:
            res = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            raw_output = res.stdout.strip()
            clean_output = re.sub(r"^```(?:json)?\s*", "", raw_output, flags=re.MULTILINE)
            clean_output = re.sub(r"```\s*$", "", clean_output, flags=re.MULTILINE).strip()

            parsed = json.loads(clean_output)
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    if isinstance(v, dict) and "tier" in v:
                        results[k] = {
                            "tier": str(v.get("tier", "Standard")),
                            "brand": str(v.get("brand", "Other")),
                        }
                logger.info(f"Successfully classified {len(parsed)} items in batch {idx}.")
        except (json.JSONDecodeError, KeyError, subprocess.SubprocessError) as e:
            logger.warning(f"Batch {idx} agent classification failed ({e}).")

    return results


def load_hardware_data(
    data_dir: Path,
    ai_cache_file: Path,
    benchmark_file: Path | None = None,
    use_ai_fallback: bool = False,
    agent: str = "auto",
) -> duckdb.DuckDBPyConnection:
    """Load hardware catalog and online benchmark ratings into DuckDB."""
    conn = duckdb.connect(":memory:")

    # Explicitly load EnterKomputer and Viraindo catalogs only
    catalog_files = [
        str(data_dir / "enterkomputer" / "latest.json"),
        str(data_dir / "viraindo" / "latest.json"),
    ]
    existing_catalog_files = [f for f in catalog_files if os.path.exists(f)]

    if not existing_catalog_files:
        # Fallback to glob if single subdirectories differ
        existing_catalog_files = [
            str(f) for f in data_dir.glob("*/latest.json") if "benchmarks" not in str(f)
        ]

    if not existing_catalog_files:
        raise FileNotFoundError(
            f"No hardware catalog files found under {data_dir}. "
            "Please run 'uv run indoscraping run enterkomputer' and 'uv run indoscraping run viraindo' first."
        )

    logger.info(f"Ingesting {len(existing_catalog_files)} retailer catalog files from {data_dir}...")
    file_list_sql = ", ".join(f"'{f}'" for f in existing_catalog_files)

    # 1. Load persistent AI cache into DuckDB
    ai_cache = load_ai_cache(ai_cache_file)
    conn.execute("CREATE TABLE ai_cache (name VARCHAR PRIMARY KEY, tier VARCHAR, brand VARCHAR)")
    for name, info in ai_cache.items():
        clean_k = re.sub(r"[\r\n\t]+", " ", name).strip()
        clean_k = re.sub(r" +", " ", clean_k)
        conn.execute(
            "INSERT OR REPLACE INTO ai_cache VALUES (?, ?, ?)",
            [clean_k, info.get("tier", "Standard"), info.get("brand", "Other")],
        )

    # 2. Raw catalog ingestion with dynamic grammar extraction
    conn.execute(
        """
        CREATE TABLE raw_catalog AS 
        WITH cleaned_input AS (
            SELECT 
                regexp_replace(regexp_replace(trim(name), '[\\r\\n\\t]+', ' ', 'g'), ' +', ' ', 'g') as name,
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
                END AS std_category
            FROM read_json_auto([{file_list_sql}])
            WHERE price > 0
        )
        SELECT 
            ci.name,
            ci.price,
            ci.source,
            ci.url,
            ci.scraped_at,
            ci.std_category,
            COALESCE(
                ac.brand,
                NULLIF(regexp_extract(ci.name, '(?i)(Asus|ROG|TUF|MSI|Gigabyte|Aorus|ASRock|Zotac|Colorful|Palit|Galax|Sapphire|PowerColor|XFX|Inno3D|Kingston|Samsung|Corsair|Adata|XPG|Team|Teamgroup|Klevv|Lexar|Seagate|WD|Western Digital|Deepcool|Thermalright|Seasonic|FSP|be quiet|Cooler Master|NZXT|Fractal|Lian Li|Antec|Thermaltake|Silverstone|Leadtek|VenomRX|Acer|AOC|ViewSonic|BenQ|LG|Dell|Lenovo|Philips|Logitech|Razer|SteelSeries)', 1), ''),
                'Other'
            ) AS brand,
            COALESCE(
                ac.tier,
                CASE 
                    -- Dynamic GPU Grammar
                    WHEN ci.std_category = 'GPU' AND regexp_matches(ci.name, '(?i)(RTX\\s*[0-9]{3,4}M?(?:\\s*(?:Ti\\s*SUPER|Ti|SUPER))?|GTX\\s*[0-9]{3,4}M?(?:\\s*Ti)?|GT\\s*[0-9]{3,4}|RX\\s*[0-9]{3,4}(?:\\s*(?:XTX|XT|GRE))?|Radeon\\s*(?:AI\\s*PRO\\s*|PRO\\s*)?(?:W[0-9]{4}|WX[0-9]{4}|R?[0-9]{4})[A-Z]*|Arc\\s*(?:Pro\\s*)?[A-Z]?[0-9]{2,3}|Quadro\\s*(?:RTX\\s*)?[A-Z0-9]+)')
                        THEN upper(regexp_replace(regexp_extract(ci.name, '(?i)(RTX\\s*[0-9]{3,4}M?(?:\\s*(?:Ti\\s*SUPER|Ti|SUPER))?|GTX\\s*[0-9]{3,4}M?(?:\\s*Ti)?|GT\\s*[0-9]{3,4}|RX\\s*[0-9]{3,4}(?:\\s*(?:XTX|XT|GRE))?|Radeon\\s*(?:AI\\s*PRO\\s*|PRO\\s*)?(?:W[0-9]{4}|WX[0-9]{4}|R?[0-9]{4})[A-Z]*|Arc\\s*(?:Pro\\s*)?[A-Z]?[0-9]{2,3}|Quadro\\s*(?:RTX\\s*)?[A-Z0-9]+)', 1), '\\s+', ' ', 'g'))

                    -- Dynamic CPU Grammar
                    WHEN ci.std_category = 'CPU' AND lower(ci.name) LIKE '%threadripper%' THEN 'AMD Threadripper'
                    WHEN ci.std_category = 'CPU' AND lower(ci.name) LIKE '%epyc%' THEN 'AMD EPYC'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Ryzen\\s*(?:PRO\\s*)?9') THEN 'AMD Ryzen 9'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Ryzen\\s*(?:PRO\\s*)?7') THEN 'AMD Ryzen 7'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Ryzen\\s*(?:PRO\\s*)?5') THEN 'AMD Ryzen 5'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Ryzen\\s*(?:PRO\\s*)?3') THEN 'AMD Ryzen 3'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Core\\s*Ultra\\s*9') THEN 'Intel Core Ultra 9'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Core\\s*Ultra\\s*7') THEN 'Intel Core Ultra 7'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Core\\s*Ultra\\s*5') THEN 'Intel Core Ultra 5'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Core\\s*i9') THEN 'Intel Core i9'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Core\\s*i7') THEN 'Intel Core i7'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Core\\s*i5') THEN 'Intel Core i5'
                    WHEN ci.std_category = 'CPU' AND regexp_matches(ci.name, '(?i)Core\\s*i3') THEN 'Intel Core i3'
                    WHEN ci.std_category = 'CPU' AND lower(ci.name) LIKE '%xeon%' THEN 'Intel Xeon'
                    WHEN ci.std_category = 'CPU' AND lower(ci.name) LIKE '%pentium%' THEN 'Intel Pentium'
                    WHEN ci.std_category = 'CPU' AND lower(ci.name) LIKE '%athlon%' THEN 'AMD Athlon'
                    WHEN ci.std_category = 'CPU' AND lower(ci.name) LIKE '%celeron%' THEN 'Intel Celeron'

                    -- Dynamic RAM Grammar
                    WHEN ci.std_category = 'RAM' AND regexp_matches(ci.name, '(?i)DDR5') AND regexp_matches(ci.name, '(?i)(8|16|24|32|48|64|96|128)\\s*GB')
                        THEN 'DDR5 ' || regexp_extract(ci.name, '(?i)(8|16|24|32|48|64|96|128)\\s*GB', 1) || 'GB'
                    WHEN ci.std_category = 'RAM' AND regexp_matches(ci.name, '(?i)DDR4') AND regexp_matches(ci.name, '(?i)(8|16|24|32|48|64)\\s*GB')
                        THEN 'DDR4 ' || regexp_extract(ci.name, '(?i)(8|16|24|32|48|64)\\s*GB', 1) || 'GB'
                    WHEN ci.std_category = 'RAM' AND regexp_matches(ci.name, '(?i)DDR3') THEN 'DDR3'

                    -- Dynamic Storage Grammar
                    WHEN ci.std_category = 'Storage' AND regexp_matches(ci.name, '(?i)(NVMe|PCIe|M\\.2)') AND regexp_matches(ci.name, '(?i)(4|2|1)\\s*TB')
                        THEN 'NVMe ' || regexp_extract(ci.name, '(?i)(4|2|1)\\s*TB', 1) || 'TB'
                    WHEN ci.std_category = 'Storage' AND regexp_matches(ci.name, '(?i)(NVMe|PCIe|M\\.2)') AND regexp_matches(ci.name, '(?i)(500|512|250|256)\\s*GB')
                        THEN 'NVMe ' || regexp_extract(ci.name, '(?i)(500|512|250|256)\\s*GB', 1) || 'GB'
                    WHEN ci.std_category = 'Storage' AND regexp_matches(ci.name, '(?i)SATA') AND regexp_matches(ci.name, '(?i)(2|1)\\s*TB')
                        THEN 'SATA ' || regexp_extract(ci.name, '(?i)(2|1)\\s*TB', 1) || 'TB'
                    WHEN ci.std_category = 'Storage' AND regexp_matches(ci.name, '(?i)SATA') AND regexp_matches(ci.name, '(?i)(500|512|240|256|120|128)\\s*GB')
                        THEN 'SATA ' || regexp_extract(ci.name, '(?i)(500|512|240|256|120|128)\\s*GB', 1) || 'GB'
                    WHEN ci.std_category = 'Storage' AND regexp_matches(ci.name, '(?i)SSD') AND regexp_matches(ci.name, '(?i)(4|2|1)\\s*TB')
                        THEN 'SSD ' || regexp_extract(ci.name, '(?i)(4|2|1)\\s*TB', 1) || 'TB'
                    WHEN ci.std_category = 'Storage' AND regexp_matches(ci.name, '(?i)SSD') AND regexp_matches(ci.name, '(?i)(500|512|250|256|120|128)\\s*GB')
                        THEN 'SSD ' || regexp_extract(ci.name, '(?i)(500|512|250|256|120|128)\\s*GB', 1) || 'GB'
                    WHEN ci.std_category = 'Storage' AND regexp_matches(ci.name, '(?i)(HDD|Hard Disk|IronWolf|SkyHawk|BarraCuda|WD Purple|WD Red)') THEN 'HDD'
                    WHEN ci.std_category = 'Storage' AND regexp_matches(ci.name, '(?i)(MicroSD|SDHC|SDXC|Flashdisk|Flash Drive|Cruzer)') THEN 'Flash / SD'

                    -- Dynamic Motherboard Chipsets
                    WHEN ci.std_category = 'Motherboard' AND regexp_matches(ci.name, '(?i)(Z890|Z790|Z690|B860|B760|B660|H810|H610|H510|W790)')
                        THEN 'Intel ' || upper(regexp_extract(ci.name, '(?i)(Z890|Z790|Z690|B860|B760|B660|H810|H610|H510|W790)', 1))
                    WHEN ci.std_category = 'Motherboard' AND regexp_matches(ci.name, '(?i)(X870E|X870|X670E|X670|B850|B650E|B650|B550|A620|B450|A520|A320|WRX90|TRX50)')
                        THEN 'AMD ' || upper(regexp_extract(ci.name, '(?i)(X870E|X870|X670E|X670|B850|B650E|B650|B550|A620|B450|A520|A320|WRX90|TRX50)', 1))

                    -- Dynamic PSU Wattage
                    WHEN ci.std_category = 'PSU' AND TRY_CAST(regexp_extract(ci.name, '(?i)([0-9]{3,4})\\s*W', 1) AS INT) >= 1000 THEN '1000W+'
                    WHEN ci.std_category = 'PSU' AND TRY_CAST(regexp_extract(ci.name, '(?i)([0-9]{3,4})\\s*W', 1) AS INT) >= 850 THEN '850W'
                    WHEN ci.std_category = 'PSU' AND TRY_CAST(regexp_extract(ci.name, '(?i)([0-9]{3,4})\\s*W', 1) AS INT) >= 750 THEN '750W'
                    WHEN ci.std_category = 'PSU' AND TRY_CAST(regexp_extract(ci.name, '(?i)([0-9]{3,4})\\s*W', 1) AS INT) >= 650 THEN '650W'
                    WHEN ci.std_category = 'PSU' AND TRY_CAST(regexp_extract(ci.name, '(?i)([0-9]{3,4})\\s*W', 1) AS INT) >= 550 THEN '550W'
                    WHEN ci.std_category = 'PSU' AND TRY_CAST(regexp_extract(ci.name, '(?i)([0-9]{3,4})\\s*W', 1) AS INT) >= 500 THEN '500W'
                    WHEN ci.std_category = 'PSU' AND TRY_CAST(regexp_extract(ci.name, '(?i)([0-9]{3,4})\\s*W', 1) AS INT) >= 400 THEN '400W-450W'

                    ELSE 'Standard'
                END
            ) AS tier,
            CASE 
                WHEN lower(ci.name) LIKE '%tray%' THEN 'Tray'
                WHEN lower(ci.name) LIKE '%box%' THEN 'Box'
                ELSE 'Standard'
            END AS packaging,
            CASE 
                WHEN ci.std_category IN ('Storage', 'RAM') THEN
                    ROUND(ci.price / NULLIF(
                        CASE 
                            WHEN upper(regexp_extract(ci.name, '(?i)([0-9]+)\\s*(GB|TB)', 2)) = 'TB' 
                            THEN TRY_CAST(regexp_extract(ci.name, '(?i)([0-9]+)\\s*(GB|TB)', 1) AS INT) * 1000
                            ELSE TRY_CAST(regexp_extract(ci.name, '(?i)([0-9]+)\\s*(GB|TB)', 1) AS INT)
                        END, 0
                    ))
                ELSE NULL
            END AS price_per_gb,
            (ac.tier IS NOT NULL) AS is_ai_classified
        FROM cleaned_input ci
        LEFT JOIN ai_cache ac ON ac.name = ci.name
        """.replace("{file_list_sql}", file_list_sql)
    )

    # 3. Check unclassified items and run AI fallback if enabled
    unclassified_rows = conn.execute("""
        SELECT DISTINCT name, std_category 
        FROM raw_catalog 
        WHERE tier = 'Standard' AND std_category IN ('GPU', 'CPU')
    """).fetchall()

    if unclassified_rows and use_ai_fallback:
        unclassified_names = [r[0] for r in unclassified_rows]
        new_classifications = classify_with_agent(
            unclassified_names, agent=agent, batch_size=15
        )
        if new_classifications:
            ai_cache.update(new_classifications)
            save_ai_cache(ai_cache_file, ai_cache)
            return load_hardware_data(
                data_dir, ai_cache_file, benchmark_file=benchmark_file, use_ai_fallback=False, agent=agent
            )

    # 4. Ingest and join real scraped PassMark benchmark datasets
    bench_file = benchmark_file or DEFAULT_BENCHMARK_FILE
    if bench_file and bench_file.exists():
        logger.info(f"Ingesting live online benchmark ratings from {bench_file}...")
        conn.execute(f"""
            CREATE TABLE raw_benchmarks AS 
            SELECT name, category, score, benchmark, segment 
            FROM read_json_auto('{bench_file}')
        """)

        # GPU Desktop Benchmarks Link
        conn.execute("""
            CREATE TABLE gpu_tier_benchmarks AS 
            WITH gpu_unique_tiers AS (
                SELECT DISTINCT tier 
                FROM raw_catalog 
                WHERE std_category = 'GPU' AND tier != 'Standard'
            ),
            matched_gpus AS (
                SELECT 
                    gt.tier,
                    b.name as bench_name,
                    b.score as bench_score,
                    b.benchmark as bench_type,
                    ROW_NUMBER() OVER (
                        PARTITION BY gt.tier 
                        ORDER BY 
                            CASE WHEN lower(b.name) LIKE '%laptop%' OR lower(b.name) LIKE '%mobile%' THEN 1 ELSE 0 END ASC,
                            length(b.name) ASC
                    ) as rn
                FROM gpu_unique_tiers gt
                JOIN raw_benchmarks b ON b.category = 'GPU' 
                    AND regexp_matches(b.name, '(?i)' || replace(gt.tier, ' ', '\\s*'))
            )
            SELECT tier, bench_name, bench_score, bench_type 
            FROM matched_gpus 
            WHERE rn = 1
        """)

        # CPU Series Benchmarks Link
        conn.execute("""
            CREATE TABLE cpu_series_benchmarks AS 
            WITH cpu_bench_series AS (
                SELECT 
                    name,
                    score,
                    CASE 
                        WHEN lower(name) LIKE '%threadripper%' THEN 'AMD Threadripper'
                        WHEN lower(name) LIKE '%epyc%' THEN 'AMD EPYC'
                        WHEN regexp_matches(name, '(?i)Ryzen\\s*(?:PRO\\s*)?9') THEN 'AMD Ryzen 9'
                        WHEN regexp_matches(name, '(?i)Ryzen\\s*(?:PRO\\s*)?7') THEN 'AMD Ryzen 7'
                        WHEN regexp_matches(name, '(?i)Ryzen\\s*(?:PRO\\s*)?5') THEN 'AMD Ryzen 5'
                        WHEN regexp_matches(name, '(?i)Ryzen\\s*(?:PRO\\s*)?3') THEN 'AMD Ryzen 3'
                        WHEN regexp_matches(name, '(?i)Core\\s*Ultra\\s*9') THEN 'Intel Core Ultra 9'
                        WHEN regexp_matches(name, '(?i)Core\\s*Ultra\\s*7') THEN 'Intel Core Ultra 7'
                        WHEN regexp_matches(name, '(?i)Core\\s*Ultra\\s*5') THEN 'Intel Core Ultra 5'
                        WHEN regexp_matches(name, '(?i)Core\\s*i9') THEN 'Intel Core i9'
                        WHEN regexp_matches(name, '(?i)Core\\s*i7') THEN 'Intel Core i7'
                        WHEN regexp_matches(name, '(?i)Core\\s*i5') THEN 'Intel Core i5'
                        WHEN regexp_matches(name, '(?i)Core\\s*i3') THEN 'Intel Core i3'
                        WHEN lower(name) LIKE '%xeon%' THEN 'Intel Xeon'
                        WHEN lower(name) LIKE '%pentium%' THEN 'Intel Pentium'
                        WHEN lower(name) LIKE '%athlon%' THEN 'AMD Athlon'
                        WHEN lower(name) LIKE '%celeron%' THEN 'Intel Celeron'
                        ELSE 'Standard'
                    END AS tier
                FROM raw_benchmarks 
                WHERE category = 'CPU'
            )
            SELECT 
                tier,
                median(score)::int as median_score,
                max(score) as max_score,
                count(*) as tested_models
            FROM cpu_bench_series 
            WHERE tier != 'Standard'
            GROUP BY tier
        """)

        # Create enriched catalog with real benchmark value score (score per IDR 1 Million)
        conn.execute("""
            CREATE TABLE enriched_catalog AS 
            SELECT 
                rc.*,
                gb.bench_name as gpu_bench_name,
                gb.bench_score as gpu_bench_score,
                cb.max_score as cpu_bench_score,
                cb.median_score as cpu_median_score,
                CASE 
                    WHEN rc.std_category = 'GPU' AND gb.bench_score IS NOT NULL 
                        THEN round(gb.bench_score / (rc.price / 1000000), 1)
                    WHEN rc.std_category = 'CPU' AND cb.max_score IS NOT NULL 
                        THEN round(cb.max_score / (rc.price / 1000000), 1)
                    ELSE NULL
                END AS value_score
            FROM raw_catalog rc
            LEFT JOIN gpu_tier_benchmarks gb ON gb.tier = rc.tier
            LEFT JOIN cpu_series_benchmarks cb ON cb.tier = rc.tier
        """)
    else:
        logger.warning("No benchmark file found. Run 'indoscraping run passmark' to scrape online benchmarks.")
        conn.execute("""
            CREATE TABLE enriched_catalog AS 
            SELECT rc.*, NULL::VARCHAR as gpu_bench_name, NULL::INT as gpu_bench_score, NULL::INT as cpu_bench_score, NULL::INT as cpu_median_score, NULL::FLOAT as value_score 
            FROM raw_catalog rc
        """)
        conn.execute("CREATE TABLE gpu_tier_benchmarks (tier VARCHAR, bench_name VARCHAR, bench_score INT, bench_type VARCHAR)")
        conn.execute("CREATE TABLE cpu_series_benchmarks (tier VARCHAR, median_score INT, max_score INT, tested_models INT)")

    return conn


def query_to_dicts(conn: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    """Execute SQL query and convert results to list of dictionaries without pandas."""
    cur = conn.execute(sql)
    cols = [desc[0] for desc in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def extract_analytics(conn: duckdb.DuckDBPyConnection) -> dict[str, Any]:
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
            count(*) FILTER (WHERE tier != 'Standard') as count_classified,
            count(*) FILTER (WHERE is_ai_classified = true) as count_ai_classified,
            count(*) FILTER (WHERE std_category IN ('GPU', 'CPU')) as count_core_silicon,
            count(*) FILTER (WHERE std_category IN ('GPU', 'CPU') AND tier != 'Standard') as count_core_classified,
            count(*) FILTER (WHERE tier = 'Standard' AND std_category IN ('GPU', 'CPU')) as count_unclassified_chips,
            count(*) FILTER (WHERE value_score IS NOT NULL) as count_benchmark_enriched,
            max(scraped_at) as last_updated
        FROM enriched_catalog
    """)[0]

    # 2. Category Distribution
    cat_dist = query_to_dicts(conn, """
        SELECT std_category as category, count(*) as count
        FROM enriched_catalog
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
        FROM enriched_catalog
        GROUP BY std_category
        HAVING count(*) FILTER (WHERE source = 'enterkomputer') > 0 
           AND count(*) FILTER (WHERE source = 'viraindo') > 0
        ORDER BY total_count DESC
    """)

    # 4. GPU Benchmarks & Best Value (Points per IDR 1M)
    gpu_value_rankings = query_to_dicts(conn, """
        SELECT 
            gb.tier,
            gb.bench_name,
            gb.bench_score,
            median(ec.price)::int as median_price,
            round(gb.bench_score / (median(ec.price) / 1000000), 1) as value_score,
            count(*) as count
        FROM enriched_catalog ec
        JOIN gpu_tier_benchmarks gb ON gb.tier = ec.tier
        WHERE ec.std_category = 'GPU'
        GROUP BY gb.tier, gb.bench_name, gb.bench_score
        ORDER BY value_score DESC
        LIMIT 20
    """)

    # 5. GPU Efficiency Frontier Scatter Plot Data (Price vs PassMark G3D Mark)
    gpu_scatter_data = query_to_dicts(conn, """
        SELECT 
            gb.tier,
            round(median(ec.price) / 1000000, 2) as x,
            gb.bench_score as y,
            round(gb.bench_score / (median(ec.price) / 1000000), 1) as value_score,
            count(*) as count
        FROM enriched_catalog ec
        JOIN gpu_tier_benchmarks gb ON gb.tier = ec.tier
        WHERE ec.std_category = 'GPU'
        GROUP BY gb.tier, gb.bench_score
        ORDER BY x ASC
    """)

    # 6. CPU Value Rankings (PassMark Max Score / Price in Juta)
    cpu_value_rankings = query_to_dicts(conn, """
        SELECT 
            cb.tier,
            cb.max_score as bench_score,
            cb.median_score,
            cb.tested_models,
            median(ec.price)::int as median_price,
            round(cb.max_score / (median(ec.price) / 1000000), 1) as value_score,
            count(*) as count
        FROM enriched_catalog ec
        JOIN cpu_series_benchmarks cb ON cb.tier = ec.tier
        WHERE ec.std_category = 'CPU'
        GROUP BY cb.tier, cb.max_score, cb.median_score, cb.tested_models
        ORDER BY value_score DESC
        LIMIT 15
    """)

    # 7. Standard GPU Series Benchmarks (by price)
    gpu_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price
        FROM enriched_catalog WHERE std_category = 'GPU' AND tier != 'Standard'
        GROUP BY tier 
        ORDER BY median_price DESC
        LIMIT 25
    """)

    # 8. Standard CPU Series Benchmarks (by price)
    cpu_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price
        FROM enriched_catalog WHERE std_category = 'CPU' AND tier != 'Standard'
        GROUP BY tier 
        ORDER BY median_price DESC
    """)

    # 9. RAM Benchmarks
    ram_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price
        FROM enriched_catalog WHERE std_category = 'RAM' AND tier != 'Standard'
        GROUP BY tier 
        ORDER BY median_price DESC
        LIMIT 15
    """)

    # 10. Storage Benchmarks
    storage_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price, avg(price_per_gb)::int as avg_price_per_gb
        FROM enriched_catalog WHERE std_category = 'Storage' AND tier != 'Standard'
        GROUP BY tier 
        ORDER BY median_price DESC
        LIMIT 15
    """)

    # 11. Motherboard Benchmarks
    mobo_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price
        FROM enriched_catalog WHERE std_category = 'Motherboard' AND tier != 'Standard'
        GROUP BY tier 
        ORDER BY median_price DESC
        LIMIT 20
    """)

    # 12. PSU Benchmarks
    psu_benchmarks = query_to_dicts(conn, """
        SELECT tier, count(*) as count, min(price) as min_price, median(price)::int as median_price, avg(price)::int as avg_price, max(price) as max_price
        FROM enriched_catalog WHERE std_category = 'PSU' AND tier != 'Standard'
        GROUP BY tier 
        ORDER BY median_price DESC
    """)

    # 13. Tray vs Box CPU Premium
    tray_vs_box = query_to_dicts(conn, """
        SELECT 
            tier,
            avg(price) FILTER (WHERE packaging = 'Tray')::int as avg_tray,
            avg(price) FILTER (WHERE packaging = 'Box')::int as avg_box,
            count(*) as count
        FROM enriched_catalog
        WHERE std_category = 'CPU' AND tier IN ('AMD Ryzen 5', 'AMD Ryzen 7', 'Intel Core i5', 'Intel Core i7')
        GROUP BY tier
        HAVING avg_tray > 0 AND avg_box > 0
        ORDER BY count DESC
    """)

    # 14. Full Products Table (All products with value scores)
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
            value_score,
            is_ai_classified,
            (tier = 'Standard' AND std_category IN ('GPU', 'CPU')) as is_unclassified_chip,
            url
        FROM enriched_catalog
        ORDER BY std_category, price ASC
    """)

    return {
        "kpis": kpis,
        "cat_dist": cat_dist,
        "retailer_comparison": retailer_comparison,
        "gpu_value_rankings": gpu_value_rankings,
        "gpu_scatter_data": gpu_scatter_data,
        "cpu_value_rankings": cpu_value_rankings,
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


def render_html_report(analytics: dict[str, Any], output_path: Path) -> None:
    """Generate modern, interactive HTML dashboard with sorting, filtering, and value analytics."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    analytics_json = json.dumps(analytics, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>pcomp — Indonesian PC Hardware Price Intelligence & Value Engine</title>
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
      margin-bottom: 0.35rem;
    }}
    .kpi-value {{
      font-size: 1.6rem;
      font-weight: 700;
      color: #fff;
      font-variant-numeric: tabular-nums;
    }}
    .kpi-subtext {{
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }}

    /* Section Tabs */
    .section-nav {{
      display: flex;
      gap: 0.5rem;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 0.75rem;
      margin-bottom: 1.5rem;
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
      white-space: nowrap;
      transition: all 0.2s ease;
    }}
    .nav-tab:hover {{
      color: var(--text-main);
      background: #172236;
    }}
    .nav-tab.active {{
      background: #1e293b;
      color: var(--accent-cyan);
      border-color: var(--accent-cyan);
    }}
    .nav-tab-highlight {{
      color: var(--accent-emerald) !important;
      border-color: rgba(16, 185, 129, 0.3) !important;
    }}
    .nav-tab-highlight.active {{
      background: rgba(16, 185, 129, 0.15) !important;
      color: #34d399 !important;
      border-color: var(--accent-emerald) !important;
    }}

    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}

    /* Charts Layout */
    .charts-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
      gap: 1.5rem;
      margin-bottom: 2rem;
    }}
    .chart-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
    }}
    .chart-card h2 {{
      font-size: 1.05rem;
      font-weight: 600;
      margin-bottom: 0.25rem;
    }}
    .chart-card p {{
      font-size: 0.8rem;
      color: var(--text-muted);
      margin-bottom: 1rem;
    }}
    .chart-container {{
      position: relative;
      height: 320px;
      width: 100%;
    }}

    /* Explorer Table */
    .explorer-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      margin-top: 2rem;
    }}
    .explorer-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
      flex-wrap: wrap;
      gap: 1rem;
    }}
    .explorer-controls {{
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }}
    .search-input {{
      background: #0d131f;
      border: 1px solid var(--card-border);
      color: var(--text-main);
      padding: 0.65rem 1rem;
      border-radius: 8px;
      font-size: 0.9rem;
      width: 100%;
    }}
    .search-input:focus {{
      outline: none;
      border-color: var(--accent-cyan);
    }}
    .filter-btn-group {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      align-items: center;
    }}
    .filter-label {{
      font-size: 0.75rem;
      text-transform: uppercase;
      color: var(--text-muted);
      font-weight: 600;
      margin-right: 0.25rem;
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
    .filter-btn-emerald.active {{
      background: var(--accent-emerald);
      color: #000;
      border-color: var(--accent-emerald);
      font-weight: 700;
    }}
    .filter-btn-alert {{
      background: rgba(244, 63, 94, 0.15);
      border-color: rgba(244, 63, 94, 0.4);
      color: #fb7185;
    }}
    .filter-btn-alert.active {{
      background: var(--accent-rose);
      color: #fff;
      border-color: var(--accent-rose);
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
      cursor: pointer;
      user-select: none;
      transition: background 0.15s;
    }}
    th:hover {{ background: #1c2b44; color: #fff; }}
    th .sort-icon {{
      display: inline-block;
      margin-left: 0.35rem;
      font-size: 0.75rem;
      color: #64748b;
    }}
    th.sorted .sort-icon {{ color: var(--accent-cyan); }}
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
    .badge-value {{ background: rgba(16, 185, 129, 0.25); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.5); font-weight: 700; }}
    .badge-top-value {{ background: linear-gradient(135deg, #059669, #0284c7); color: #fff; font-size: 0.7rem; font-weight: 800; border-radius: 9999px; padding: 0.15rem 0.5rem; }}
    .badge-ai {{ background: rgba(139, 92, 246, 0.25); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4); font-size: 0.7rem; }}
    .badge-unclassified {{ background: rgba(244, 63, 94, 0.25); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.5); }}
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
        <h1>pcomp — Indonesian PC Hardware Price & Value Intelligence</h1>
        <p>DuckDB Price Intelligence & Live PassMark Benchmark Scoring Engine</p>
      </div>
    </div>
    <div class="header-badge">
      Generated: <strong>{analytics["generated_at"]}</strong> • Engine: <strong>DuckDB + PassMark G3D/CPU Mark</strong>
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
      <div class="kpi-label">Core Silicon Recognition</div>
      <div class="kpi-value">{round((analytics["kpis"]["count_core_classified"] / max(analytics["kpis"]["count_core_silicon"], 1)) * 100, 1)}%</div>
      <div class="kpi-subtext">{analytics["kpis"]["count_classified"]:,} hardware tiered ({analytics["kpis"]["count_ai_classified"]} by AI cache)</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Benchmark Enriched Items</div>
      <div class="kpi-value">{analytics["kpis"]["count_benchmark_enriched"]:,}</div>
      <div class="kpi-subtext">Scored by live online PassMark ratings</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">EnterKomputer / Viraindo</div>
      <div class="kpi-value">{analytics["kpis"]["count_enterkomputer"]:,} / {analytics["kpis"]["count_viraindo"]:,}</div>
      <div class="kpi-subtext">Live JSON API + Web Pricelist scrape</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Average Catalog Price</div>
      <div class="kpi-value">Rp {analytics["kpis"]["avg_price"]:,}</div>
      <div class="kpi-subtext">Range: Rp {analytics["kpis"]["min_price"]:,} – Rp {analytics["kpis"]["max_price"]:,}</div>
    </div>
  </section>

  <!-- Interactive Analytical Section Tabs -->
  <nav class="section-nav">
    <button class="nav-tab active nav-tab-highlight" onclick="switchTab('tab-value')">💎 Best Value (Price-to-Performance)</button>
    <button class="nav-tab" onclick="switchTab('tab-overview')">📊 Market Overview</button>
    <button class="nav-tab" onclick="switchTab('tab-gpu')">🎮 GPU Benchmarks</button>
    <button class="nav-tab" onclick="switchTab('tab-cpu')">🧠 CPU & Tray vs Box</button>
    <button class="nav-tab" onclick="switchTab('tab-ram')">⚡ RAM (DDR4 vs DDR5)</button>
    <button class="nav-tab" onclick="switchTab('tab-storage')">💾 Storage (NVMe / SATA Value)</button>
    <button class="nav-tab" onclick="switchTab('tab-mobo-psu')">🔌 Motherboard & PSU</button>
  </nav>

  <!-- TAB 0: Best Value (Price-to-Performance) -->
  <div id="tab-value" class="tab-content active">
    <section class="charts-grid">
      <div class="chart-card" style="grid-column: 1 / -1;">
        <h2>GPU Efficiency Frontier: Price vs 3D Graphics Performance</h2>
        <p>Live scatter plot of Median Price (IDR Millions) vs PassMark G3D Mark. Points near top-left represent optimal price-to-performance champions.</p>
        <div class="chart-container" style="height: 420px;">
          <canvas id="gpuScatterChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h2>Top 15 GPU Bang-for-Buck (Points / Rp 1M)</h2>
        <p>Ranked by pure 3D graphics performance delivered per million Rupiah</p>
        <div class="chart-container" style="height: 380px;">
          <canvas id="gpuValueChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h2>Top 15 CPU Compute Value (Points / Rp 1M)</h2>
        <p>Ranked by multi-threaded computing power delivered per million Rupiah</p>
        <div class="chart-container" style="height: 380px;">
          <canvas id="cpuValueChart"></canvas>
        </div>
      </div>
    </section>
  </div>

  <!-- TAB 1: Market Overview -->
  <div id="tab-overview" class="tab-content">
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
        <h2>GPU Silicon Benchmarks (Median Price in IDR Millions)</h2>
        <p>Dynamic market benchmark across NVIDIA RTX 50/40/30, AMD Radeon RX 9000/7000, and Intel Arc</p>
        <div class="chart-container" style="height: 480px;">
          <canvas id="gpuTiersChart"></canvas>
        </div>
      </div>
    </section>
  </div>

  <!-- TAB 3: CPU Benchmarks & Tray vs Box -->
  <div id="tab-cpu" class="tab-content">
    <section class="charts-grid">
      <div class="chart-card">
        <h2>CPU Series Benchmarks (Median IDR Millions)</h2>
        <p>Market benchmark across AMD Ryzen/Threadripper & Intel Core Ultra/Core Series</p>
        <div class="chart-container" style="height: 380px;">
          <canvas id="cpuTiersChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h2>Tray vs Box OEM Price Premium</h2>
        <p>Direct cost difference: OEM Tray (no box/cooler) vs Retail Box</p>
        <div class="chart-container" style="height: 380px;">
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
        <p>Median prices for DDR5 vs DDR4 across standard and non-binary kits (8GB to 128GB)</p>
        <div class="chart-container" style="height: 360px;">
          <canvas id="ramTiersChart"></canvas>
        </div>
      </div>
    </section>
  </div>

  <!-- TAB 5: Storage Benchmarks -->
  <div id="tab-storage" class="tab-content">
    <section class="charts-grid">
      <div class="chart-card">
        <h2>Storage Form Factor Benchmarks (Median IDR Millions)</h2>
        <p>High-Speed NVMe PCIe vs SATA SSDs & HDDs (250GB to 4TB)</p>
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
        <h2>Motherboard Chipset Price Tiers (Median IDR Millions)</h2>
        <p>Intel (Z890/Z790/B760/H610) vs AMD (X870E/X870/B650/B550/A620)</p>
        <div class="chart-container" style="height: 360px;">
          <canvas id="moboTiersChart"></canvas>
        </div>
      </div>
      <div class="chart-card">
        <h2>Power Supply (PSU) Wattage Tiers (Median IDR Millions)</h2>
        <p>Median market prices across 400W to 1000W+ power supplies</p>
        <div class="chart-container" style="height: 360px;">
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
        <p>Instant multi-criteria search, column sorting, and benchmark value inspector</p>
      </div>
    </div>

    <div class="explorer-controls">
      <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search product name, chipset, or brand (e.g. RTX 4070, B650, DDR5, NVMe, Seasonic)..." oninput="handleSearch()">
      
      <!-- Category Filter Buttons -->
      <div class="filter-btn-group" id="categoryFilters">
        <span class="filter-label">Category:</span>
        <button class="filter-btn active" data-cat="all" onclick="setCategoryFilter('all')">All</button>
        <button class="filter-btn" data-cat="GPU" onclick="setCategoryFilter('GPU')">GPU</button>
        <button class="filter-btn" data-cat="CPU" onclick="setCategoryFilter('CPU')">CPU</button>
        <button class="filter-btn" data-cat="RAM" onclick="setCategoryFilter('RAM')">RAM</button>
        <button class="filter-btn" data-cat="Storage" onclick="setCategoryFilter('Storage')">Storage</button>
        <button class="filter-btn" data-cat="Motherboard" onclick="setCategoryFilter('Motherboard')">Motherboard</button>
        <button class="filter-btn" data-cat="PSU" onclick="setCategoryFilter('PSU')">PSU</button>
        <button class="filter-btn" data-cat="Monitor" onclick="setCategoryFilter('Monitor')">Monitor</button>
        <button class="filter-btn" data-cat="Cooler" onclick="setCategoryFilter('Cooler')">Cooler</button>
        <button class="filter-btn" data-cat="Casing" onclick="setCategoryFilter('Casing')">Casing</button>
        <button class="filter-btn" data-cat="Peripheral" onclick="setCategoryFilter('Peripheral')">Peripherals</button>
        <button class="filter-btn filter-btn-alert" data-cat="unclassified" onclick="setCategoryFilter('unclassified')">⚠️ Unclassified</button>
      </div>

      <!-- Price Range Quick Filters -->
      <div class="filter-btn-group" id="priceFilters">
        <span class="filter-label">Price Bracket:</span>
        <button class="filter-btn active" data-price="all" onclick="setPriceFilter('all')">All Prices</button>
        <button class="filter-btn" data-price="u3" onclick="setPriceFilter('u3')">&lt; Rp 3M</button>
        <button class="filter-btn" data-price="3-10" onclick="setPriceFilter('3-10')">Rp 3M – 10M</button>
        <button class="filter-btn" data-price="10-25" onclick="setPriceFilter('10-25')">Rp 10M – 25M</button>
        <button class="filter-btn" data-price="o25" onclick="setPriceFilter('o25')">&gt; Rp 25M</button>
      </div>

      <!-- Retailer & Special Filters -->
      <div class="filter-btn-group" id="retailerFilters">
        <span class="filter-label">Retailer:</span>
        <button class="filter-btn active" data-ret="all" onclick="setRetailerFilter('all')">All Retailers</button>
        <button class="filter-btn" data-ret="enterkomputer" onclick="setRetailerFilter('enterkomputer')">EnterKomputer</button>
        <button class="filter-btn" data-ret="viraindo" onclick="setRetailerFilter('viraindo')">Viraindo</button>
        <span style="border-left: 1px solid #374151; height: 16px; margin: 0 0.3rem;"></span>
        <button class="filter-btn filter-btn-emerald" id="topValueBtn" onclick="toggleTopValueFilter()">💎 Top Value Only</button>
      </div>
    </div>

    <div class="table-container">
      <table id="productTable">
        <thead>
          <tr>
            <th onclick="sortTable('name')">Product Name <span class="sort-icon" id="sort-name">⇅</span></th>
            <th width="110" onclick="sortTable('category')">Category <span class="sort-icon" id="sort-category">⇅</span></th>
            <th width="170" onclick="sortTable('tier')">Tier / Silicon Model <span class="sort-icon" id="sort-tier">⇅</span></th>
            <th width="120" onclick="sortTable('brand')">Brand <span class="sort-icon" id="sort-brand">⇅</span></th>
            <th width="130" onclick="sortTable('source')">Retailer <span class="sort-icon" id="sort-source">⇅</span></th>
            <th width="150" style="text-align: right;" onclick="sortTable('price')">Price (IDR) <span class="sort-icon" id="sort-price">▲</span></th>
            <th width="140" style="text-align: right;" onclick="sortTable('value_score')">Value Score <span class="sort-icon" id="sort-value_score">⇅</span></th>
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
      setTimeout(() => {{
        if (typeof Chart !== 'undefined' && Chart.instances) {{
          Object.values(Chart.instances).forEach(c => {{
            try {{ c.resize(); }} catch(e) {{}}
          }});
        }}
        window.dispatchEvent(new Event('resize'));
      }}, 50);
    }}

    // Render All Charts on Load
    window.addEventListener("DOMContentLoaded", () => {{
      // 0. GPU Scatter Plot (Efficiency Frontier)
      const scatterCtx = document.getElementById("gpuScatterChart").getContext("2d");
      new Chart(scatterCtx, {{
        type: 'scatter',
        data: {{
          datasets: [{{
            label: 'GPU Models',
            data: data.gpu_scatter_data.map(d => ({{ x: d.x, y: d.y, tier: d.tier, value: d.value_score, count: d.count }})),
            backgroundColor: '#06b6d4',
            borderColor: '#38bdf8',
            pointRadius: 6,
            pointHoverRadius: 9
          }}]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: (ctx) => {{
                  const pt = ctx.raw;
                  return `${{pt.tier}}: Rp ${{pt.x}}M | PassMark: ${{pt.y.toLocaleString()}} (${{pt.value}} pts/M)`;
                }}
              }}
            }}
          }},
          scales: {{
            x: {{
              title: {{ display: true, text: 'Median Price (IDR Millions)', color: '#9ca3af' }},
              ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }}
            }},
            y: {{
              title: {{ display: true, text: 'PassMark G3D Mark Score', color: '#9ca3af' }},
              ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }}
            }}
          }}
        }}
      }});

      // 0b. GPU Value Bar Chart (Points / Rp 1M)
      const gpuValCtx = document.getElementById("gpuValueChart").getContext("2d");
      new Chart(gpuValCtx, {{
        type: 'bar',
        data: {{
          labels: data.gpu_value_rankings.map(d => d.tier),
          datasets: [{{
            label: 'Score / Rp 1M',
            data: data.gpu_value_rankings.map(d => d.value_score),
            backgroundColor: '#10b981', borderRadius: 6
          }}]
        }},
        options: {{
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: (ctx) => `${{ctx.raw}} pts/M (Rp ${{ (data.gpu_value_rankings[ctx.dataIndex].median_price / 1e6).toFixed(2) }}M)`
              }}
            }}
          }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ display: false }} }}
          }}
        }}
      }});

      // 0c. CPU Value Bar Chart (PassMark / Rp 1M)
      const cpuValCtx = document.getElementById("cpuValueChart").getContext("2d");
      new Chart(cpuValCtx, {{
        type: 'bar',
        data: {{
          labels: data.cpu_value_rankings.map(d => d.tier),
          datasets: [{{
            label: 'Compute / Rp 1M',
            data: data.cpu_value_rankings.map(d => d.value_score),
            backgroundColor: '#8b5cf6', borderRadius: 6
          }}]
        }},
        options: {{
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: (ctx) => `${{ctx.raw}} pts/M (Rp ${{ (data.cpu_value_rankings[ctx.dataIndex].median_price / 1e6).toFixed(2) }}M)`
              }}
            }}
          }},
          scales: {{
            x: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ color: '#1f293d' }} }},
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ display: false }} }}
          }}
        }}
      }});

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
            backgroundColor: ['#06b6d4', '#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899', '#64748b', '#0ea5e9', '#14b8a6', '#f43f5e'],
            borderColor: '#111827', borderWidth: 2
          }}]
        }},
        options: {{
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ position: 'right', labels: {{ color: '#9ca3af', font: {{ size: 11 }} }} }} }}
        }}
      }});

      // 3. GPU Tiers Horizontal Bar (Top 25)
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
          plugins: {{ 
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: (ctx) => `Rp ${{ctx.raw}} Jt (${{data.gpu_benchmarks[ctx.dataIndex].count}} items)`
              }}
            }}
          }},
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
          plugins: {{ 
            legend: {{ display: false }},
            tooltip: {{
              callbacks: {{
                label: (ctx) => `Rp ${{ctx.raw}} Jt (${{data.cpu_benchmarks[ctx.dataIndex].count}} items)`
              }}
            }}
          }},
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
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ display: false }} }}
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
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ display: false }} }}
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
            y: {{ ticks: {{ color: '#9ca3af' }}, grid: {{ display: false }} }}
          }}
        }}
      }});

      // Initial table render
      renderTable();
    }});

    // Table Filter, Column Sorting, and Pagination Logic
    let currentCategory = 'all';
    let currentRetailer = 'all';
    let currentPriceFilter = 'all';
    let topValueOnly = false;
    let searchQuery = '';
    let sortColumn = 'price';
    let sortDirection = 'asc';
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

    function setPriceFilter(pRange) {{
      currentPriceFilter = pRange;
      document.querySelectorAll('#priceFilters .filter-btn').forEach(btn => {{
        btn.classList.toggle('active', btn.getAttribute('data-price') === pRange);
      }});
      currentPage = 1;
      renderTable();
    }}

    function setRetailerFilter(ret) {{
      currentRetailer = ret;
      document.querySelectorAll('#retailerFilters .filter-btn').forEach(btn => {{
        if (btn.hasAttribute('data-ret')) {{
          btn.classList.toggle('active', btn.getAttribute('data-ret') === ret);
        }}
      }});
      currentPage = 1;
      renderTable();
    }}

    function toggleTopValueFilter() {{
      topValueOnly = !topValueOnly;
      document.getElementById('topValueBtn').classList.toggle('active', topValueOnly);
      currentPage = 1;
      renderTable();
    }}

    function handleSearch() {{
      searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();
      currentPage = 1;
      renderTable();
    }}

    function sortTable(column) {{
      if (sortColumn === column) {{
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
      }} else {{
        sortColumn = column;
        sortDirection = (column === 'value_score' || column === 'price_per_gb') ? 'desc' : 'asc';
      }}
      updateSortIndicators();
      currentPage = 1;
      renderTable();
    }}

    function updateSortIndicators() {{
      document.querySelectorAll('th').forEach(th => th.classList.remove('sorted'));
      document.querySelectorAll('.sort-icon').forEach(icon => icon.textContent = '⇅');

      const activeTh = document.querySelector(`th[onclick*="'${{sortColumn}}'"]`);
      const activeIcon = document.getElementById(`sort-${{sortColumn}}`);
      if (activeTh) activeTh.classList.add('sorted');
      if (activeIcon) activeIcon.textContent = sortDirection === 'asc' ? '▲' : '▼';
    }}

    function changePage(delta) {{
      currentPage += delta;
      renderTable();
    }}

    function renderTable() {{
      filteredItems = data.table_items.filter(item => {{
        // Category Filter
        let matchCat = false;
        if (currentCategory === 'all') {{
          matchCat = true;
        }} else if (currentCategory === 'unclassified') {{
          matchCat = Boolean(item.is_unclassified_chip);
        }} else {{
          matchCat = item.category === currentCategory;
        }}

        // Retailer Filter
        const matchRet = currentRetailer === 'all' || item.source === currentRetailer;

        // Price Range Filter
        let matchPrice = true;
        if (currentPriceFilter === 'u3') matchPrice = item.price < 3000000;
        else if (currentPriceFilter === '3-10') matchPrice = item.price >= 3000000 && item.price <= 10000000;
        else if (currentPriceFilter === '10-25') matchPrice = item.price > 10000000 && item.price <= 25000000;
        else if (currentPriceFilter === 'o25') matchPrice = item.price > 25000000;

        // Top Value Filter
        let matchTopVal = true;
        if (topValueOnly) {{
          matchTopVal = item.value_score && item.value_score >= 2000;
        }}

        // Search Query Filter
        const matchSearch = !searchQuery || 
          item.name.toLowerCase().includes(searchQuery) || 
          item.tier.toLowerCase().includes(searchQuery) ||
          item.brand.toLowerCase().includes(searchQuery);

        return matchCat && matchRet && matchPrice && matchTopVal && matchSearch;
      }});

      // Column Sorting
      filteredItems.sort((a, b) => {{
        let valA = a[sortColumn];
        let valB = b[sortColumn];

        if (valA === null || valA === undefined) return 1;
        if (valB === null || valB === undefined) return -1;

        if (typeof valA === 'string') {{
          const cmp = valA.localeCompare(valB);
          return sortDirection === 'asc' ? cmp : -cmp;
        }}
        return sortDirection === 'asc' ? valA - valB : valB - valA;
      }});

      const totalPages = Math.ceil(filteredItems.length / pageSize) || 1;
      if (currentPage < 1) currentPage = 1;
      if (currentPage > totalPages) currentPage = totalPages;

      const startIndex = (currentPage - 1) * pageSize;
      const pageItems = filteredItems.slice(startIndex, startIndex + pageSize);

      const tbody = document.getElementById('tableBody');
      tbody.innerHTML = '';

      if (pageItems.length === 0) {{
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 2rem; color: #94a3b8;">No matching products found.</td></tr>';
      }} else {{
        pageItems.forEach(item => {{
          const tr = document.createElement('tr');
          const nameHtml = item.url 
            ? `<a href="${{item.url}}" target="_blank" rel="noopener noreferrer" class="item-link">${{item.name}}</a>`
            : item.name;

          const unitBadge = item.price_per_gb 
            ? `<span class="badge badge-unit">Rp ${{item.price_per_gb.toLocaleString("id-ID")}}/GB</span>`
            : '';

          const aiBadge = item.is_ai_classified 
            ? `<span class="badge badge-ai">✨ AI Classified</span>` 
            : '';

          const unclassifiedBadge = item.is_unclassified_chip 
            ? `<span class="badge badge-unclassified">⚠️ Unclassified</span>` 
            : '';

          let valueBadge = '';
          if (item.value_score) {{
            const isHighVal = item.value_score >= 3000;
            valueBadge = `
              <span class="badge badge-value">${{item.value_score.toLocaleString()}} pts/M</span>
              ${{isHighVal ? '<span class="badge badge-top-value">🏆 Top Value</span>' : ''}}
            `;
          }} else {{
            valueBadge = '<span style="color:#64748b; font-size: 0.8rem;">—</span>';
          }}

          tr.innerHTML = `
            <td>
              ${{nameHtml}}
              ${{aiBadge ? '<br>' + aiBadge : ''}}
              ${{unclassifiedBadge ? '<br>' + unclassifiedBadge : ''}}
            </td>
            <td><span class="badge" style="background:#1e293b; color:#94a3b8;">${{item.category}}</span></td>
            <td><span class="badge badge-tier">${{item.tier}}</span></td>
            <td><span class="badge badge-brand">${{item.brand}}</span></td>
            <td><span class="badge badge-${{item.source}}">${{item.source}}</span></td>
            <td style="text-align: right;" class="price-cell">
              ${{formatRp(item.price)}}
              ${{unitBadge ? '<br>' + unitBadge : ''}}
            </td>
            <td style="text-align: right;">
              ${{valueBadge}}
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
        "--benchmark-file",
        type=Path,
        default=DEFAULT_BENCHMARK_FILE,
        help="Path to scraped PassMark hardware benchmark JSON",
    )
    parser.add_argument(
        "--ai-cache",
        type=Path,
        default=DEFAULT_AI_CACHE_FILE,
        help="Path to AI classification cache JSON",
    )
    parser.add_argument(
        "--ai-fallback",
        action="store_true",
        help="Enable AI agent (agy/pi) fallback classification for unclassified hardware models",
    )
    parser.add_argument(
        "--agent",
        choices=["auto", "agy", "pi"],
        default="auto",
        help="Agent engine for fallback classification (default: auto)",
    )
    parser.add_argument(
        "--export-public",
        action="store_true",
        help="Export generated dashboard directly to public web directory (nichsedge.github.io/public/pcomp/)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Automatically launch the generated HTML report in your browser",
    )

    args = parser.parse_args()

    try:
        conn = load_hardware_data(
            data_dir=args.data_dir,
            ai_cache_file=args.ai_cache,
            benchmark_file=args.benchmark_file,
            use_ai_fallback=args.ai_fallback,
            agent=args.agent,
        )
        analytics = extract_analytics(conn)
        render_html_report(analytics, args.output)

        print("\n✨ pcomp local dashboard generated successfully!")
        print(f"📊 Report: file://{args.output.resolve()}")
        print(f"🔬 Total Items: {analytics['kpis']['total_items']:,}")
        print(f"🎯 Core Silicon Recognition: {round((analytics['kpis']['count_core_classified'] / max(analytics['kpis']['count_core_silicon'], 1)) * 100, 1)}% ({analytics['kpis']['count_core_classified']:,}/{analytics['kpis']['count_core_silicon']:,} GPU/CPU)")
        print(f"💎 Benchmark Enriched: {analytics['kpis']['count_benchmark_enriched']:,} items with live PassMark scores")
        print(f"⚙️ Internal Hardware Tiered: {analytics['kpis']['count_classified']:,} items")
        print(f"🤖 AI Cache Items: {analytics['kpis']['count_ai_classified']}\n")

        if args.export_public:
            render_html_report(analytics, DEFAULT_PUBLIC_EXPORT_HTML)
            print(f"🌐 Public static dashboard exported to: {DEFAULT_PUBLIC_EXPORT_HTML}")
            print("   Live at: https://nichsedge.me/pcomp/ (upon git push in nichsedge.github.io)\n")

        if args.open:
            webbrowser.open(f"file://{args.output.resolve()}")

    except Exception:
        logger.exception("Failed to generate report")
        sys.exit(1)


if __name__ == "__main__":
    main()
