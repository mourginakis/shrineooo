#!/usr/bin/env python3.12

#%% ========================================
from pprint import pprint
from sqlalchemy import create_engine, text

from src.api_chatbot import gpt5_web
from src.secrets_ import POSTGRES_CREDENTIALS, POSTGRES_URL
engine = create_engine(POSTGRES_URL)

# sqlalchemy rawsql is preferred over psycopg2 because the API
# is more readable and it auto manages connection pools.

#%% ========================================



def seed_notes():
    # 1. get 2 coins from the cmcmaster table where status is active and cmcnotes.note is NULL, ordered ascending by rank

    sql = \
"""
SELECT m.id, m.name, m.urls
FROM cmcmaster AS m
JOIN cmcnotes  AS n ON n.id = m.id
WHERE m.status = 'active'
  AND n.note IS NULL
ORDER BY m.rank ASC NULLS LAST
LIMIT 2;
"""
    conn = engine.connect()
    rows = conn.execute(text(sql))
    rows = rows.mappings().fetchall()
    conn.close()
    print(f"got: {str([row['name'] for row in rows])}")
    # print(f"Found {len(rows)} ids")
    # pprint(rows)
    # return rows

    for row in rows:
        prompt = f"""
        Please write a research report on the following coin:
        {row['name']}

        I have aggregated a number of links that you can use as reference, if you can't
        find information on your own. Some of these links are for things like telegram and twiter and stuff,
        and might entirely be worth ignoring. But the websites and technical stuff might be worth reading.

        The goal here is to create a "fingerprint" for this token, to explore in-depth what the crypto 
        ecosystem looks like, and how this network, among other crypto networks, fits into the current 
        state of the crypto ecosystem. I would say no more than 6 paragraphs for this token, 
        explaining what it is, what its core features are, and any negative information about 
        it--but be sure to include ample information, especially regarding the fingerprint. We want a really good, unbiased, and 
        illuminating view into this specific token. This report will be a single part of a greater collage 
        of reports which will be aggregated together to aim to explore hundreds of different tokens/blockchains.

        Some relevant links:
        {row['urls']}

        """
        print(prompt)

        response = gpt5_web(prompt)
        print(response)

        # upload response to cmcnotes.note
        sql = \
"""
UPDATE cmcnotes
SET note = :note
WHERE id = :id
"""
        conn = engine.connect()
        conn.execute(text(sql), {"note": response, "id": row['id']})
        conn.commit()
        conn.close()
        print(f"Uploaded response to cmcnotes.note for {row['name']}")

        # break

    return rows


rows = seed_notes()
# pprint(rows)
#%%
