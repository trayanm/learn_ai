import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from sqlalchemy import create_engine

# Generate timestamps for the last 10 days
end_date = datetime.now()
dates = [end_date - timedelta(days=i) for i in range(10)]

rows = []
for driver_id in range(1001, 1011):
    for d in dates:
        rows.append({
            "driver_id": driver_id,
            "event_timestamp": d,
            "conv_rate": np.random.rand(),
            "acc_rate": np.random.rand(),
            "avg_daily_trips": np.random.randint(10, 50)
        })

df = pd.DataFrame(rows)

# Ensure event_timestamp is datetime type
df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])

# Save to parquet (for backup)
os.makedirs("data", exist_ok=True)
df.to_parquet("data/driver_stats.parquet")

# Save to PostgreSQL
engine = create_engine('postgresql://postgres:edno@localhost:5432/ai_feast_db')
df.to_sql('driver_stats', engine, if_exists='replace', index=False)

print("✅ Data saved to data/driver_stats.parquet")
print("✅ Data saved to PostgreSQL table 'driver_stats'")
print(f"Data shape: {df.shape}")
print("Sample data:")
print(df.head())