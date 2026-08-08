# ☁️ BigQuery & dbt Technical Analysis Sandbox

A technical research sandbox containing BigQuery dbt projects, SQL compilation experiments, and deep-dive technical articles.

---

## 📁 Directory Structure

```text
bigquery_experiments/
├── sans/                                        # dbt BigQuery project (sans)
│   ├── dbt_project.yml                          # BigQuery dbt project config
│   ├── models/                                  # BigQuery SQL models
│   │   ├── fact_orders_static.sql
│   │   └── indirect_selection/                  # dbt indirect selection test models
│   ├── macros/                                  # dbt BigQuery test macros
│   └── tests/                                   # Custom SQL data quality tests
├── compiled_sql/                                # Compiled BigQuery SQL queries
└── docs/                                        # Technical research articles
    ├── dbt_bq_insert_overwrite_dynamic_vs_static.md
    └── dbt_indirect_selection.md
```

---

## 📚 Technical Research & Analysis Articles

### 1. `dbt_bq_insert_overwrite_dynamic_vs_static.md`
Deep-dive analysis comparing **Dynamic vs Static Partition Insert-Overwrite strategies in dbt BigQuery**:
- Explains why dynamic partition overwrite (`copy` or `insert overwrite`) can result in silent data duplication or missing partition replacement if partition filters are omitted.
- Outlines best practices for atomic partition replacement in BigQuery using `static` partition replacement declarations.

### 2. `dbt_indirect_selection.md`
Analysis of dbt's **Indirect Test Selection Behavior**:
- Details how dbt selects attached data quality tests when filtering models (e.g. `--select model_name+`).
- Demonstrates how indirect selection mode (`eager`, `cautious`, `buildable`, `empty`) impacts test execution scope and CI build execution time.

---

## 🚀 How to Run BigQuery dbt Experiments

To compile and run models against Google Cloud BigQuery (requires GCP credentials):

```bash
cd bigquery_experiments/sans
uv run dbt compile
uv run dbt run --profile sans
uv run dbt test --profile sans
```
