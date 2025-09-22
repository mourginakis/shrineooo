#%%
import time
import requests
from pprint import pprint
from secrets_ import CMC_API_KEY

# Coinmarketcap Universe Scraper
# This endpoint is free with an account
# But it is still rate-limited.
# https://coinmarketcap.com/api/documentation/v1/#operation/getV1CryptocurrencyMap
# Recommended to use CMC ID instead of cryptocurrency symbols to 
# identify cryptocurrencies in your application logic.

URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/map"


def get_cmc_map():
    headers = {
        "Accept": "application/json",
        "X-CMC_PRO_API_KEY": CMC_API_KEY,
    }

    start = 1

    params = {
        "start": start,
        "limit": 5000,
        "listing_status": "active,inactive,untracked",
        "aux": "platform,first_historical_data,last_historical_data,is_active,status",
        "sort": "id",
    }

    rows = []

    while True:
        # ingest data
        params["start"] = start
        response = requests.get(URL, headers=headers, params=params)
        response.raise_for_status()
        payload = response.json()
        data = payload.get("data") or []

        rows.extend(data)
        print(f"+{len(data)} rows (total: {len(rows)})")

        # print the last 5 rows
        # print(f"Last 5 rows: {rows[-5:]}")

        if len(data) < params["limit"]:
            break

        start += len(data)
        time.sleep(2)

    # count rows, sanity check
    print(f"Total rows: {len(rows)}")
    unique_ids = {row["id"] for row in rows}
    print(f"Unique IDs: {len(unique_ids)} == {len(rows)}")

    return rows

rows = get_cmc_map()

#%%

def destructure_row(row):
    p = row.get("platform") or {}
    return {
        "id":                     row.get("id"),
        "rank":                   row.get("rank"),
        "name":                   row.get("name"),
        "symbol":                 row.get("symbol"),
        "slug":                   row.get("slug"),
        "is_active":              row.get("is_active"),
        "status":                 row.get("status"),
        "first_historical_data":  row.get("first_historical_data"),
        "last_historical_data":   row.get("last_historical_data"),
        "platform_id":            p.get("id"),
        "platform_name":          p.get("name"),
        "platform_symbol":        p.get("symbol"),
        "platform_slug":          p.get("slug"),
        "platform_token_address": p.get("token_address"),
    }

destructured_rows = [destructure_row(row) for row in rows]


# write the rows to a csv using pandas (cast rank to int?)
import pandas as pd
df = pd.DataFrame(destructured_rows)
df.to_csv("cmcmap.csv", index=False)
print("Wrote cmc_map.csv")


