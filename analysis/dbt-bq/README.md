# 🚀 Sandbox Hub: Data Engineering & Analytics Engineering Workspace

A structured monorepo containing production-grade Data Warehouse simulations, dbt models, Airflow orchestrations, and BigQuery analytics engineering research.

---

## 🏛️ Repository Architecture & Modules

```text
dbt-bq/
├── .venv/                         # Shared Python virtual environment
├── pyproject.toml                 # Root project dependencies & lockfile
├── uv.lock                        # Fast UV dependency lockfile
├── README.md                      # Workspace documentation index
│
├── sharia_banking_dw/             # 🕌 MODULE 1: Sharia Banking Data Warehouse Simulation
│   ├── dags/                      # Airflow Astronomer Cosmos DAGs
│   │   └── sharia_banking_cosmos_dag.py
│   ├── dbt_project/               # dbt DuckDB project (sharia_dw)
│   │   ├── dbt_project.yml
│   │   ├── profiles.yml
│   │   ├── seeds/                 # Raw Indonesian Sharia banking synthetic seeds
│   │   └── models/                # Medallion layer SQL models (stg, int, marts)
│   ├── scripts/                   # Data generator & execution runner
│   │   ├── generate_sharia_data.py
│   │   └── run_sharia_dw.py
│   ├── airflow.cfg                # Airflow config (load_examples = False)
│   ├── airflow.db                 # Airflow metadata database
│   ├── standalone_admin_password.txt # Airflow UI credentials (admin / admin)
│   └── README.md                  # Comprehensive Sharia DW guide
│
└── bigquery_experiments/          # ☁️ MODULE 2: BigQuery Experiments & Research Articles
    ├── sans/                      # dbt BigQuery project
    ├── compiled_sql/              # Compiled BigQuery SQL queries
    ├── docs/                      # Research articles (Insert-overwrite & indirect selection)
    └── README.md                  # BigQuery sandbox guide
```

---

## 📚 Module Overview & Quick Links

| Module | Engine & Stack | Key Features & Focus Areas | Documentation Link |
| :--- | :--- | :--- | :--- |
| **Sharia Banking DW** | `dbt-duckdb`, `astronomer-cosmos`, `apache-airflow` | Indonesian Sharia banking financial simulation, Nisbah profit sharing, OJK NPF asset quality, Zakat & Purification | [sharia_banking_dw/README.md](file:///home/al/Projects/sandbox-hub/analysis/dbt-bq/sharia_banking_dw/README.md) |
| **BigQuery Experiments** | `dbt-bigquery`, Google BigQuery | BigQuery dynamic vs static partition insert overwrite strategies, dbt indirect test selection | [bigquery_experiments/README.md](file:///home/al/Projects/sandbox-hub/analysis/dbt-bq/bigquery_experiments/README.md) |

---

## ⚡ Quickstart Commands

### 1. Execute Full Sharia Banking Simulation & Reports
```bash
uv run python sharia_banking_dw/scripts/run_sharia_dw.py
```

### 2. Launch Local Airflow Web UI (`http://localhost:8080`)
```bash
export AIRFLOW_HOME=$(pwd)/sharia_banking_dw
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/sharia_banking_dw/dags

uv run airflow standalone
```
- **Username**: `admin`
- **Password**: `admin`

### 3. Run dbt Commands directly
```bash
# Run Sharia DW dbt project
cd sharia_banking_dw/dbt_project
uv run dbt seed --profiles-dir .
uv run dbt run --profiles-dir .
uv run dbt test --profiles-dir .
```

---

## 📄 Artifacts & Technical Guides

- [Walkthrough Guide](file:///home/al/.gemini/antigravity/brain/ac10290a-2230-4fb5-a422-1b8a2510b019/walkthrough.md): Comprehensive summary of the completed Sharia Banking Data Warehouse simulation and verification outputs.
- [Implementation Plan](file:///home/al/.gemini/antigravity/brain/ac10290a-2230-4fb5-a422-1b8a2510b019/implementation_plan.md): Architectural design document for workspace restructuring and Medallion data modeling.
