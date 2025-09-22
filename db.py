#%% ========================================
from sqlalchemy import create_engine, text
import pandas as pd
from secrets_ import POSTGRES_URL




#%% ========================================
def _create_table_cmcmaster():
    """Creates the master CMC map table"""
    sql = \
"""
CREATE TABLE cmcmaster (
    id    INT4 PRIMARY KEY,
    rank  INT4,
    name  TEXT
)
"""
    engine = create_engine(POSTGRES_URL)
    conn = engine.connect()
    conn.execute(text(sql))
    conn.commit()
    conn.close()
    print("Created table cmcmaster")

_create_table_cmcmaster()



#%% ========================================
