#!/usr/bin/env python3
"""
Indonesian Sharia Banking Synthetic Data Generator
Generates realistic CSV seeds for dbt data warehouse simulation.
Domains covered:
1. Retail Banking (Customers, Wadiah & Mudharabah Accounts, Daily Transactions)
2. Financing / Pembiayaan (Murabahah & Musyarakah contracts, Kolektibilitas OJK)
3. Monthly Gross Income Pool for Mudharabah Profit Sharing (Nisbah)
4. Sharia Purification & Charity Fund (Ta'zir / Penalty & Non-Halal income)
"""

import os
import random
from datetime import datetime, timedelta
import pandas as pd

# Set random seed for reproducibility
random.seed(42)

SEED_DIR = os.path.join(os.path.dirname(__file__), "..", "dbt_project", "seeds")
os.makedirs(SEED_DIR, exist_ok=True)


BRANCHES = [
    {"code": "KC001", "name": "Jakarta Thamrin Main Branch", "city": "Jakarta Pusat"},
    {"code": "KC002", "name": "Surabaya Darmo Branch", "city": "Surabaya"},
    {"code": "KC003", "name": "Bandung Asia Afrika Branch", "city": "Bandung"},
    {"code": "KC004", "name": "Banda Aceh Masjid Raya Branch", "city": "Banda Aceh"},
    {"code": "KC005", "name": "Makassar Pettarani Branch", "city": "Makassar"},
]

FIRST_NAMES = [
    "Ahmad", "Muhammad", "Siti", "Nur", "Fatimah", "Budi", "Dewi", "Rizal",
    "Indah", "Rahmat", "Hasan", "Zainab", "Umar", "Aisyah", "Fajar", "Taufik",
    "Fitri", "Eko", "Tri", "Agus", "Haryanto", "Kartika", "Rina", "Bambang"
]

LAST_NAMES = [
    "Pratama", "Hidayat", "Saputra", "Wibowo", "Kusuma", "Santoso", "Wijaya",
    "Siregar", "Nasution", "Laksana", "Utami", "Nugroho", "Suharto", "Firmansyah",
    "Subakti", "Maulana", "Arifin", "Rahman", "Setiawan", "Bahri"
]

def generate_nik():
    # 16 digit Indonesian NIK formula simulation
    prov = random.choice(["31", "32", "35", "11", "73"])
    city = random.choice(["71", "73", "15", "01"])
    date_part = f"{random.randint(1, 28):02d}{random.randint(1, 12):02d}{random.randint(70, 99):02d}"
    serial = f"{random.randint(1, 9999):04d}"
    return f"{prov}{city}{date_part}{serial}"

def main():
    print("Generating Sharia Banking synthetic datasets...")
    
    # 1. CUSTOMERS
    num_customers = 100
    customers = []
    for i in range(1, num_customers + 1):
        cust_id = f"CUST-{i:05d}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        branch = random.choice(BRANCHES)
        segment = random.choice(["RETAIL", "RETAIL", "RETAIL", "PRIORITY", "SME", "CORPORATE"])
        birth_date = (datetime(2002, 1, 1) - timedelta(days=random.randint(6000, 18000))).strftime("%Y-%m-%d")
        
        customers.append({
            "customer_id": cust_id,
            "nik": generate_nik(),
            "full_name": f"{first_name} {last_name}",
            "customer_segment": segment,
            "branch_code": branch["code"],
            "branch_name": branch["name"],
            "city": branch["city"],
            "birth_date": birth_date,
            "is_sharia_compliant_flag": True,
            "created_at": "2026-01-01"
        })
    df_customers = pd.DataFrame(customers)
    df_customers.to_csv(os.path.join(SEED_DIR, "raw_customers.csv"), index=False)
    print(f"Generated {len(df_customers)} raw_customers records.")

    # 2. ACCOUNTS (Wadiah & Mudharabah)
    accounts = []
    account_seq = 1
    for cust in customers:
        # Create Wadiah account for all
        acc_id_w = f"ACC-{account_seq:06d}"
        account_seq += 1
        accounts.append({
            "account_id": acc_id_w,
            "customer_id": cust["customer_id"],
            "account_number": f"7100{random.randint(100000, 999999)}",
            "product_type": "SAVINGS",
            "akad_type": "WADIAH_YAD_DHAMANAH",
            "currency": "IDR",
            "indicative_nisbah_customer_pct": 0.0, # Wadiah has no guaranteed nisbah (bonus at bank's discretion / Athaya)
            "status": "ACTIVE",
            "opened_date": "2026-01-01"
        })
        
        # Create Mudharabah account for ~60% of customers
        if random.random() < 0.6:
            acc_id_m = f"ACC-{account_seq:06d}"
            account_seq += 1
            nisbah_cust = random.choice([30.0, 35.0, 40.0, 45.0, 50.0]) # Nisbah Nasabah %
            accounts.append({
                "account_id": acc_id_m,
                "customer_id": cust["customer_id"],
                "account_number": f"7200{random.randint(100000, 999999)}",
                "product_type": random.choice(["SAVINGS_MUDHARABAH", "DEPOSIT_MUDHARABAH"]),
                "akad_type": "MUDHARABAH_MUTLAQAH",
                "currency": "IDR",
                "indicative_nisbah_customer_pct": nisbah_cust,
                "status": "ACTIVE",
                "opened_date": "2026-01-01"
            })

    df_accounts = pd.DataFrame(accounts)
    df_accounts.to_csv(os.path.join(SEED_DIR, "raw_accounts.csv"), index=False)
    print(f"Generated {len(df_accounts)} raw_accounts records.")

    # 3. FINANCING CONTRACTS (Pembiayaan: Murabahah & Musyarakah)
    financing_contracts = []
    contract_seq = 1
    # Sample ~35 customers with financing
    financing_custs = random.sample(customers, 35)
    for cust in financing_custs:
        contract_id = f"FIN-{contract_seq:05d}"
        contract_seq += 1
        akad = random.choice(["MURABAHAH", "MURABAHAH", "MUSYARAKAH"])
        principal = random.choice([25000000, 50000000, 100000000, 250000000, 500000000, 1000000000])
        
        if akad == "MURABAHAH":
            margin_rate_pct = random.choice([8.5, 9.0, 10.0, 11.5])
            tenor_months = random.choice([12, 24, 36, 60])
            total_margin = principal * (margin_rate_pct / 100.0) * (tenor_months / 12.0)
            total_financing = principal + total_margin
            monthly_installment = total_financing / tenor_months
        else: # MUSYARAKAH
            margin_rate_pct = random.choice([9.5, 10.5, 12.0]) # Expected profit share equivalent
            tenor_months = random.choice([12, 24, 36])
            total_margin = principal * (margin_rate_pct / 100.0) * (tenor_months / 12.0)
            total_financing = principal + total_margin
            monthly_installment = total_financing / tenor_months

        # OJK Asset Quality / Kolektibilitas (1-Lancar, 2-DPK, 3-Kurang Lancar, 4-Diragukan, 5-Macet)
        kolektibilitas = random.choices([1, 2, 3, 4, 5], weights=[0.85, 0.08, 0.04, 0.02, 0.01])[0]

        financing_contracts.append({
            "contract_id": contract_id,
            "customer_id": cust["customer_id"],
            "contract_number": f"FIN-2026-{random.randint(1000, 9999)}",
            "akad_type": akad,
            "financing_sector": random.choice(["CONSUMER_KPR", "CONSUMER_AUTO", "SME_WORKING_CAPITAL", "CORPORATE_PROJECT"]),
            "principal_amount": round(principal, 2),
            "margin_amount": round(total_margin, 2),
            "total_financing_amount": round(total_financing, 2),
            "monthly_installment": round(monthly_installment, 2),
            "tenor_months": tenor_months,
            "start_date": "2026-01-01",
            "end_date": (datetime(2026, 1, 1) + timedelta(days=30*tenor_months)).strftime("%Y-%m-%d"),
            "ojk_kolektibilitas": kolektibilitas,
            "outstanding_principal": round(principal * random.uniform(0.7, 0.95), 2)
        })

    df_financing = pd.DataFrame(financing_contracts)
    df_financing.to_csv(os.path.join(SEED_DIR, "raw_financing_contracts.csv"), index=False)
    print(f"Generated {len(df_financing)} raw_financing_contracts records.")

    # 4. DAILY TRANSACTIONS (30 Days simulation: Jan 1 to Jan 30, 2026)
    transactions = []
    tx_seq = 1
    start_dt = datetime(2026, 1, 1)
    
    # Pre-populate initial balance deposits
    for acc in accounts:
        init_amount = float(random.randint(5000000, 150000000))
        transactions.append({
            "transaction_id": f"TX-{tx_seq:08d}",
            "account_id": acc["account_id"],
            "transaction_date": "2026-01-01",
            "transaction_type": "INITIAL_DEPOSIT",
            "db_cr_flag": "CR",
            "amount": init_amount,
            "channel": "BRANCH",
            "description": "Initial account balance deposit"
        })
        tx_seq += 1

    # Daily transactional flow over 30 days
    for day_idx in range(1, 30):
        current_date = (start_dt + timedelta(days=day_idx)).strftime("%Y-%m-%d")
        
        # Random deposits & withdrawals for accounts
        for acc in random.sample(accounts, int(len(accounts) * 0.4)):
            tx_type = random.choice(["CASH_DEPOSIT", "ATM_WITHDRAWAL", "QRIS_PAYMENT", "BI_FAST_TRANSFER", "PAYROLL"])
            db_cr = "CR" if tx_type in ["CASH_DEPOSIT", "PAYROLL"] else "DB"
            amt = float(random.randint(50000, 5000000))
            
            transactions.append({
                "transaction_id": f"TX-{tx_seq:08d}",
                "account_id": acc["account_id"],
                "transaction_date": current_date,
                "transaction_type": tx_type,
                "db_cr_flag": db_cr,
                "amount": amt,
                "channel": random.choice(["MOBILE_BANKING", "ATM", "BRANCH", "QRIS"]),
                "description": f"Customer transaction - {tx_type}"
            })
            tx_seq += 1

        # Financing Installment Repayments (Angsuran Pembiayaan)
        if day_idx in [10, 15, 20, 25]: # Repayment dates
            for fin in financing_contracts:
                # 90% of customers pay on time
                if random.random() < 0.90:
                    cust_wadiah_accs = [a for a in accounts if a["customer_id"] == fin["customer_id"]]
                    if cust_wadiah_accs:
                        acc_id = cust_wadiah_accs[0]["account_id"]
                        transactions.append({
                            "transaction_id": f"TX-{tx_seq:08d}",
                            "account_id": acc_id,
                            "transaction_date": current_date,
                            "transaction_type": "ANGSURAN_PEMBIAYAAN",
                            "db_cr_flag": "DB",
                            "amount": fin["monthly_installment"],
                            "channel": "AUTO_DEBIT",
                            "description": f"Payment for contract {fin['contract_number']}"
                        })
                        tx_seq += 1

    df_transactions = pd.DataFrame(transactions)
    df_transactions.to_csv(os.path.join(SEED_DIR, "raw_daily_transactions.csv"), index=False)
    print(f"Generated {len(df_transactions)} raw_daily_transactions records.")

    # 5. BANK GROSS INCOME POOL FOR NISBAH PROFIT SHARING (January 2026)
    bank_income_pool = [
        {
            "period_month": "2026-01",
            "income_source": "MURABAHAH_MARGIN_REVENUE",
            "gross_amount": 1500000000.0, # IDR 1.5 Billion
            "description": "Gross profit realized from Murabahah financing installments"
        },
        {
            "period_month": "2026-01",
            "income_source": "MUSYARAKAH_PROFIT_SHARE",
            "gross_amount": 850000000.0, # IDR 850 Million
            "description": "Profit share from Musyarakah enterprise financing"
        },
        {
            "period_month": "2026-01",
            "income_source": "SUKUK_TREASURY_YIELD",
            "gross_amount": 450000000.0, # IDR 450 Million
            "description": "Coupon yield from Sovereign & Corporate Sukuk portfolio"
        }
    ]
    df_income_pool = pd.DataFrame(bank_income_pool)
    df_income_pool.to_csv(os.path.join(SEED_DIR, "raw_bank_income_pool.csv"), index=False)
    print(f"Generated {len(df_income_pool)} raw_bank_income_pool records.")

    # 6. SHARIA PURIFICATION & CHARITY FUND (Dana Kebajikan / Qardh Hasan)
    purification_records = []
    pur_seq = 1
    for fin in financing_contracts:
        if fin["ojk_kolektibilitas"] > 1: # Late/overdue financing
            tazir_penalty = float(random.randint(50000, 500000))
            purification_records.append({
                "record_id": f"PUR-{pur_seq:05d}",
                "period_month": "2026-01",
                "source_type": "TAZIR_LATE_PENALTY",
                "contract_id": fin["contract_id"],
                "amount": tazir_penalty,
                "status": "ALLOCATED_TO_CHARITY",
                "description": f"Ta'zir penalty charged on overdue contract {fin['contract_number']}"
            })
            pur_seq += 1

    purification_records.append({
        "record_id": f"PUR-{pur_seq:05d}",
        "period_month": "2026-01",
        "source_type": "NON_HALAL_INTEREST_PURIFICATION",
        "contract_id": "N/A",
        "amount": 12500000.0,
        "status": "ALLOCATED_TO_CHARITY",
        "description": "Legacy conventional Nostro account interest purified to Qardh Hasan fund"
    })
    
    df_purification = pd.DataFrame(purification_records)
    df_purification.to_csv(os.path.join(SEED_DIR, "raw_purification_fund.csv"), index=False)
    print(f"Generated {len(df_purification)} raw_purification_fund records.")

    print("\nAll synthetic Sharia Banking CSV seeds generated successfully!")

if __name__ == "__main__":
    main()
