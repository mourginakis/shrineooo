#%% ========================================
from dataclasses import dataclass, asdict
from sqlalchemy import create_engine, text, bindparam, ARRAY, BIGINT
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

def _upsert_users(profiles: Profile) -> int:
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
    Fails if the root id isn't already in the database."""
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
    # this fn was written by chatgpt <3
    if not ids:
        return []
    # dedup while preserving order
    uniq_ids = list(dict.fromkeys(int(i) for i in ids))
    stmt = text("""
    with input_ids(source_id) as (
      select unnest(:source_ids)
    ),
    common_targets as (
      select f.target_id
      from xfollows f
      join input_ids i on i.source_id = f.source_id
      group by f.target_id
      having count(distinct f.source_id) = (select count(*) from input_ids)
    )
    select
      u.id, u.screen_name, u.name, u.description,
      u.followers_count, u.urlpinned, u.urlprofile
    from common_targets ct
    join xusers u on u.id = ct.target_id
    order by u.followers_count desc nulls last, u.screen_name
    """).bindparams(bindparam("source_ids", type_=ARRAY(BIGINT)))
    conn = engine.connect()
    try:
        rs = conn.execute(stmt, {"source_ids": uniq_ids})
        rows = [dict(r._mapping) for r in rs]
    finally:
        conn.close()
    return [Profile(**row) for row in rows]


#%% ========================================
# this is necessary to seed the db with root node

jackalxhunt = Profile(
    id=1967223627314757632,
    screen_name="jackalxhunt",
    name="jackal",
    description="master tracker",
    followers_count=0,
    urlpinned="",
    urlprofile="https://x.com/jackalxhunt",
)
print(f"Updating db with jackalxhunt root node...", end="")
nupdated = _upsert_users([jackalxhunt])
print(f"done!")

