from feast import Entity, FeatureView, Field
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres import PostgreSQLSource
from feast.types import Float32, Int64
from datetime import timedelta

# Define the driver entity
driver = Entity(
    name="driver_id",
    description="Driver identifier",
    value_type=Int64,  # Fix deprecation warning
)

# Define the PostgreSQL data source
driver_stats_source = PostgreSQLSource(
    name="driver_stats_source",
    query="SELECT * FROM driver_stats",
    timestamp_field="event_timestamp",
)

# Define the feature view
driver_stats_fv = FeatureView(
    name="driver_stats",
    entities=[driver],
    ttl=timedelta(days=1),  # Time to live for features
    schema=[
        Field(name="conv_rate", dtype=Float32),
        Field(name="acc_rate", dtype=Float32),
        Field(name="avg_daily_trips", dtype=Int64),
    ],
    source=driver_stats_source,
)
