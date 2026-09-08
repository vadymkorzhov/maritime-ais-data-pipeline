import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine,text
from pathlib import Path
import os
import pandas as pd
import json
import boto3
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent/ "config.json"
load_dotenv(Path(__file__).parent.parent / ".env")

DB_USER = os.getenv("MARITIME_DB_USER")
DB_PASSWORD = os.getenv("MARITIME_DB_PASSWORD")
DB_HOST = os.getenv("MARITIME_DB_HOST")
DB_PORT = os.getenv("MARITIME_DB_PORT")
DB_NAME = os.getenv("MARITIME_DB_NAME")

def extract_vessels(url,bbox):

    response = requests.get(url,params = {"bbox":bbox},timeout=30)
    response.raise_for_status()

    data = response.json()
    return data

def transform_vessels(data):
    vessels = []
    for vessel in data["features"]:
        properties = vessel["properties"]
        coordinates = vessel["geometry"]["coordinates"]
        info = {"mmsi": properties.get("mmsi"),
                "name": properties.get("name"),
                "sog": properties.get("sog"),
                "cog": properties.get("cog"),
                "lat": coordinates[1],
                "lon": coordinates[0],
                "seen": properties.get("seen"), }
        vessels.append(info)

    vessels_df = pd.DataFrame.from_records(vessels)

    before = len(vessels_df)

    if len(vessels_df) == 0:
        logger.warning("API returned 0 vessel observations")
    else: logger.info(f"Received {before} observations from API")

    vessels_df = vessels_df.dropna(subset=["mmsi","seen"])
    vessels_df = vessels_df[
        vessels_df["lat"].between(-90, 90) &
        vessels_df["lon"].between(-180, 180)
        ]
    after_validation = len(vessels_df)
    invalid_rows = before - after_validation
    if invalid_rows > 0:
        logger.warning(f"Removed {invalid_rows} invalid rows")

    vessels_df = vessels_df.drop_duplicates(
        subset=["mmsi", "seen"]
    )
    vessels_df["seen"] = pd.to_datetime(
        vessels_df["seen"],
        utc=True
    )

    final_rows = len(vessels_df)

    logger.info(f"Dropped {after_validation - final_rows} duplicate rows")
    logger.info(f"Saved {final_rows} observations")
    return vessels_df

def load_vessels(vessels_df):
    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    vessels_df.to_sql(
        name="vessel_positions_tmp",
        con=engine,
        schema="raw",
        if_exists="replace",
        index=False
    )
    with engine.begin() as conn:
        result = conn.execute(text(
            """INSERT INTO raw.vessel_positions_raw (mmsi, name, sog,cog, lat, lon, seen)
             SELECT mmsi, name, sog,cog, lat, lon, seen 
             FROM raw.vessel_positions_tmp 
             ON CONFLICT (mmsi,seen) DO NOTHING;""")
        )
        rowcount = result.rowcount
        logger.info(f"Data received: {rowcount} rows of observations")
        logger.info(f"Skipped {len(vessels_df) - rowcount} duplicate observation records")


def save_raw_to_s3(data,bucket_name):
    s3 = boto3.client("s3")

    now = datetime.now(timezone.utc)

    key = (
        f"raw/ais/"
        f"{now:%Y/%m/%d}/"
        f"{now:%H%M%S}.json"
    )
    s3.put_object(
        Bucket=bucket_name,
        Key=key,
        Body=json.dumps(data),
        ContentType="application/json"
    )

    logger.info(f"Saved raw data to s3://{bucket_name}/{key}")


def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    url = config["url"]
    bbox = config["bbox"]
    bucket_name = config["bucket_name"]
    data = extract_vessels(url,bbox)
    save_raw_to_s3(data, bucket_name)
    vessels = transform_vessels(data)
    load_vessels(vessels)
    logger.info("Data Loaded Successfully")


if __name__ == "__main__":
    main()