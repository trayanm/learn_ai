import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

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

os.makedirs("data", exist_ok=True)
df.to_parquet("data/driver_stats.parquet")
print("✅ Data saved to data/driver_stats.parquet")