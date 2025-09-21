#!/usr/bin/env python3.12

#%%
from pprint import pprint
from secrets_ import POSTGRES_CREDENTIALS, POSTGRES_URL


# %%
# psycopg2 example
# psycopg2 is low-level
# cur.fetchall() - gets data from SELECT queries
# conn.commit() - saves data from INSERT/UPDATE/DELETE/CREATE
import psycopg2
conn = psycopg2.connect(**POSTGRES_CREDENTIALS)
cur = conn.cursor()
cur.execute("SELECT * FROM xusers")
records = cur.fetchall()
cur.close()
conn.close()
pprint(records)



#%%
# sqlalchemy example (without pandas)
# sqlalchemy is nice becuse it manages connection pools
from sqlalchemy import create_engine, text
import pandas as pd

# without pandas
engine = create_engine(POSTGRES_URL)
connection = engine.connect()
result = connection.execute(text("SELECT * FROM xusers"))
records = result.fetchall()
connection.close()
pprint(records)

#%%
# sqlalchemy example (with pandas)
# pandas does not support SQL UPDATE so its kind of useless
# unless you're just doing read operations
import pandas as pd
connection = engine.connect()
df = pd.read_sql_query(text("SELECT * FROM xusers"), connection)
pprint(df)
connection.close()


# %%
