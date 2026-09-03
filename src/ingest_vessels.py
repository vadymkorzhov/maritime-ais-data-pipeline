import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine,text
from pathlib import Path
import os
import pandas as pd
import json



CONFIG_PATH = Path(__file__).parent.parent/ "config.json"
load_dotenv(Path(__file__).parent.parent / ".env")

DB_USER = os.getenv("MARITIME_DB_USER")
DB_PASSWORD = os.getenv("MARITIME_DB_PASSWORD")
DB_HOST = os.getenv("MARITIME_DB_HOST")
DB_PORT = os.getenv("MARITIME_DB_PORT")
DB_NAME = os.getenv("MARITIME_DB_NAME")

def extract_vessels(url):

    response = requests.get(url,timeout=30)
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

    vessels_df = vessels_df.drop_duplicates(
        subset=["mmsi", "seen"]
    )
    vessels_df["seen"] = pd.to_datetime(
        vessels_df["seen"],
        utc=True
    )
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
        conn.execute(text(
            """INSERT INTO raw.vessel_positions_raw (mmsi, name, sog,cog, lat, lon, seen)
             SELECT mmsi, name, sog,cog, lat, lon, seen 
             FROM raw.vessel_positions_tmp 
             ON CONFLICT (mmsi,seen) DO NOTHING;""")
        )




def main():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    url = config["url"]
    data = extract_vessels(url)
    vessels = transform_vessels(data)
    load_vessels(vessels)
    print("Data Loaded Successfully")


if __name__ == "__main__":
    main()