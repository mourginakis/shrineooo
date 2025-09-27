#%% ========================================
from dataclasses import dataclass, asdict
from sqlalchemy import create_engine, text
import pandas as pd

from src.secrets_ import POSTGRES_URL
from src.api_x import Profile

engine = create_engine(POSTGRES_URL)

# X/Twitter is one giant DiGraph. We can represent it
# with two tables:
# xusers:   DiGraph vertex table
# xfollows: DiGraph edge table


#%% ========================================


def _create_table_xusers():
    # DiGraph vertex table
    sql = \
"""
CREATE TABLE xusers (
    id                 INT8 PRIMARY KEY,
    screen_name        TEXT NOT NULL,
    name               TEXT,
    description        TEXT,
    followers_count    INT4,
    urlpinned          TEXT,
    urlprofile         TEXT
);
CREATE INDEX xusers_screen_name_idx ON xusers(screen_name);
"""
    conn = engine.connect()
    conn.execute(text(sql))
    conn.commit()
    conn.close()
    print("Created table xusers")

def _create_table_xfollows():
    # DiGraph edge table

    sql = \
"""
CREATE TABLE xfollows (
    source_id INT8 NOT NULL
        REFERENCES xusers(id) ON DELETE CASCADE,
    target_id INT8 NOT NULL
        REFERENCES xusers(id) ON DELETE CASCADE,

    -- enforce no duplicates, also creates pair index
    -- block self following
    PRIMARY KEY   (source_id, target_id),
    CHECK         (source_id <> target_id)
);
"""
    conn = engine.connect()
    conn.execute(text(sql))
    conn.commit()
    conn.close()
    print("Created table xfollows")

# _create_table_xusers()
# _create_table_xfollows()


#%% ========================================

def upsert_users(profiles: Profile) -> int:
    """Upsert a list of profiles into the xusers table."""
    if not profiles:
        return 0

    rows = [asdict(p) for p in profiles]

    sql = """
    INSERT INTO xusers (
        id, screen_name, name, description, followers_count, urlpinned, urlprofile
    )
    VALUES (:id, :screen_name, :name, :description, :followers_count, :urlpinned, :urlprofile)
    ON CONFLICT (id) DO UPDATE SET
        screen_name      = EXCLUDED.screen_name,
        name             = EXCLUDED.name,
        description      = EXCLUDED.description,
        followers_count  = EXCLUDED.followers_count,
        urlpinned        = EXCLUDED.urlpinned,
        urlprofile       = EXCLUDED.urlprofile
    """
    conn = engine.connect()
    conn.execute(text(sql), rows)
    conn.commit()
    conn.close()
    print(f"Upserted {len(rows)} users")
    return len(rows)


def upsert_branch(id: int, profiles: list[Profile]) -> tuple[int, int]:
    """Upserts a branch (existing root node -> new profiles + edges)
    Checks first to make sure that the root profile exists."""
    # Automatically fails if the root profile isn't in xusers:
    # the INSERT into xfollows will raise a foreign-key violation 
    # and the transaction will roll back
    if not profiles:
        return (0, 0)
    # prepare data
    profiles = [asdict(p) for p in profiles]
    edges    = [{'source_id': id, 'target_id': p['id']} for p in profiles]
    # prepare sql statements
    sql1 = """
    INSERT INTO xusers (
        id, screen_name, name, description, followers_count, urlpinned, urlprofile
    )
    VALUES (:id, :screen_name, :name, :description, :followers_count, :urlpinned, :urlprofile)
    ON CONFLICT (id) DO UPDATE SET
        screen_name      = EXCLUDED.screen_name,
        name             = EXCLUDED.name,
        description      = EXCLUDED.description,
        followers_count  = EXCLUDED.followers_count,
        urlpinned        = EXCLUDED.urlpinned,
        urlprofile       = EXCLUDED.urlprofile
    """
    sql2 = """
    INSERT INTO xfollows (source_id, target_id)
    VALUES (:source_id, :target_id)
    ON CONFLICT DO NOTHING
    """
    conn = engine.connect()
    trans = conn.begin()
    try:
        conn.execute(text(sql1), profiles)
        conn.execute(text(sql2), edges)
        trans.commit()
    except Exception as e:
        trans.rollback()
        raise e
    finally:
        conn.close()
    return (len(profiles), len(edges))


def get_intersection(ids: list[int]) -> list[Profile]:
    raise NotImplementedError()


    

# %%
