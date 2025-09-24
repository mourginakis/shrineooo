#%% ========================================
import time
from dataclasses import dataclass
from itertools import batched
from sqlalchemy import create_engine, text
import pandas as pd
from secrets_ import POSTGRES_URL

# defers DB connection until connect/execute
engine = create_engine(POSTGRES_URL)

#%% ========================================


#%% ========================================

def _create_table_cmcmaster():
    """Creates the master CMC map table. 
    You should never need to call this."""
    sql = \
"""
CREATE TABLE cmcmaster (
    id                      INT4 PRIMARY KEY,
    rank                    INT4,
    name                    TEXT,
    symbol                  TEXT,
    slug                    TEXT,
    status                  TEXT,
    is_active               INT2,
    first_historical_data   TIMESTAMPTZ,
    last_historical_data    TIMESTAMPTZ,
    platform_id             INT4,
    platform_name           TEXT,
    platform_symbol         TEXT,
    platform_slug           TEXT,
    platform_token_address  TEXT
);

CREATE INDEX cmcmaster_rank_idx ON cmcmaster(rank);
CREATE INDEX cmcmaster_slug_idx ON cmcmaster(slug);
CREATE INDEX cmcmaster_platform_id_idx ON cmcmaster(platform_id);
CREATE INDEX cmcmaster_first_historical_data_idx ON cmcmaster(first_historical_data);
CREATE INDEX cmcmaster_status_idx ON cmcmaster(status);
"""
    conn = engine.connect()
    conn.execute(text(sql))
    conn.commit()
    conn.close()
    print("Created table cmcmaster")

# _create_table_cmcmaster()

#%% ========================================


# note: just query this with a view if you want slug, rank, etc.
def _create_table_cmcnotes():
    """Creates the notes table."""
    sql = \
"""
CREATE TABLE cmcnotes (
    id INT4 PRIMARY KEY,
    note TEXT
)
"""
    conn = engine.connect()
    conn.execute(text(sql))
    conn.commit()
    conn.close()
    print("Created table cmcnotes")

# _create_table_cmcnotes()

#%% ========================================


def seed_cmcnotes():
    """Seeds the notes table with the coin ids from the master table."""
    sql = """
    INSERT INTO cmcnotes (id)
    SELECT id FROM cmcmaster
    ON CONFLICT (id) DO NOTHING;
    """
    conn = engine.connect()
    conn.execute(text(sql))
    conn.commit()
    conn.close()
    print("Seeded table cmcnotes")

# seed_cmcnotes()


#%% ========================================

def bulk_upsert_cmcmaster(rows):
    BATCH_SIZE=1000
    sql = \
"""
INSERT INTO cmcmaster (
    id, rank, name, symbol, slug, status, is_active,
    first_historical_data, last_historical_data,
    platform_id, platform_name, platform_symbol,
    platform_slug, platform_token_address
)
VALUES (
    :id, :rank, :name, :symbol, :slug, :status, :is_active,
    :first_historical_data, :last_historical_data,
    :platform_id, :platform_name, :platform_symbol,
    :platform_slug, :platform_token_address
)
ON CONFLICT (id) DO UPDATE
SET
    rank = EXCLUDED.rank,
    name = EXCLUDED.name,
    symbol = EXCLUDED.symbol,
    slug = EXCLUDED.slug,
    status = EXCLUDED.status,
    is_active = EXCLUDED.is_active,
    first_historical_data = EXCLUDED.first_historical_data,
    last_historical_data = EXCLUDED.last_historical_data,
    platform_id = EXCLUDED.platform_id,
    platform_name = EXCLUDED.platform_name,
    platform_symbol = EXCLUDED.platform_symbol,
    platform_slug = EXCLUDED.platform_slug,
    platform_token_address = EXCLUDED.platform_token_address
"""
    print(f"Upserting {len(rows)} total rows")

    conn = engine.connect()
    i = 0
    t0 = time.time()
    for chunk in batched(rows, BATCH_SIZE):
        conn.execute(text(sql), list(chunk))
        conn.commit()
        i += len(chunk)
        t1 = time.time()
        dt = t1 - t0
        projected_total = dt * (len(rows)/ i)
        print(f"Upserted {i}/{len(rows)} rows, elapsed {dt:.2f}s of {projected_total:.2f}s projected")
    conn.close()
    print("Done!")


#%% ========================================
from api_cmc import get_cmc_map1

rows = get_cmc_map1()
print(f"got {len(rows)} rows")


#%% ========================================
bulk_upsert_cmcmaster(rows)


#%% ========================================
