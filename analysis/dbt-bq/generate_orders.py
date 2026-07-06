from datetime import date, datetime, timedelta

today = date.today()
now = datetime.now()

print("TRUNCATE TABLE dev.stg_orders; INSERT INTO dev.stg_orders VALUES")

rows = []
order_id = 1

# Generate data for D-3, D-2, D-1
for days_ago in [3, 2, 1]:
    order_date = today - timedelta(days=days_ago)

    for _ in range(3):
        rows.append(
            f"({order_id}, "
            f"DATE '{order_date}', "
            f"TIMESTAMP '{now:%Y-%m-%d %H:%M:%S}', "
            f"{100 + order_id})"
        )
        order_id += 1

print(",\n".join(rows) + ";")