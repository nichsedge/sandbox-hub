from datetime import date, datetime, timedelta

today = date.today()
now = datetime.now()

print("TRUNCATE TABLE dev.stg_orders;")
print("INSERT INTO dev.stg_orders (order_id, order_date, updated_at, amount) VALUES")

rows = []
order_id = 1

# Generate data for D-3, D-2, D-1 relative to CURRENT_DATE()
for days_ago in [3, 2, 1]:
    for _ in range(3):
        rows.append(
            f"({order_id}, DATE_SUB(CURRENT_DATE(), INTERVAL {days_ago} DAY), CURRENT_TIMESTAMP(), {100 + order_id})"
        )
        order_id += 1

print(",\n".join(rows) + ";")