#!/usr/bin/env python3.12

#%% ========================================
import time
from pprint import pprint
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine, text

from src.api_chatbot import gpt5_web, gpt5_web_flex_mini, gpt5
from src.secrets_ import POSTGRES_CREDENTIALS, POSTGRES_URL
engine = create_engine(POSTGRES_URL)

# sqlalchemy rawsql is preferred over psycopg2 because the API
# is more readable and it auto manages connection pools.


# pprint(rows)
#%% ========================================


def hydrate_cmcnotes():
    sql = \
"""
SELECT *
FROM cmcnotes
WHERE webprint_gpt5mini IS NULL
ORDER BY rank ASC
LIMIT 10
"""
    # connect and return a list[dict]
    conn = engine.connect()
    rows = conn.execute(text(sql))
    rows = rows.mappings().fetchall()
    conn.close()
    print(f"got: {str([row['name'] for row in rows])} fresh from db")

    for row in rows:
        slugtxt = f"Platform-Slug: {row.get('platform_slug')}" if row.get('platform_slug') else ""
        prompt = f"""
        Please write a research report on the following coin:
        Name: {row['name']}. Slug: {row['slug']}. {slugtxt}

        I have aggregated a number of links that you can use as reference. Use my links to guide you,
        but favor your own web search to find information on your own. Make sure to look through many 
        different sources (at least 7 different sources).

        Some of these links are for things like telegram and twiter and are likely entirely worth ignoring.
        The websites with branding, about-us, and technical stuff might be worth reading.

        The goal here is to create a "fingerprint" for this token. This means we want to explore
        in-depth what this crypto project/network/token is, what its core features are, what is
        strengths/weaknesses are, and any negative information about it. 
        The idea is to create a really good, unbiased, and illuminating view into this specific token,
        specifically regarding how this network, among other crypto networks, fits into the current
        ecosystem.

        No more than 6 paragraphs for this report please. Be sure to include ample information,
        especially regarding the fingerprint of what it is, and how it fits into a larger crypto ecosystem.
        This report will be a single part of a greater collage of reports which will be aggregated together
        to aim to explore hundreds of different tokens/blockchains.

        Some relevant links:
        {row['urls']}

        Return ONLY the full report. Do NOT add extraneous text afterwards. Do NOT prompt the user
        for information. Do NOT suggest to reformat the information.
        Return only the report, intended to be presented to a user in a professional manner.

        """
        print(prompt)

        # response = gpt5_web(prompt)
        response = gpt5_web_flex_mini(prompt)
        print(response)

        sql2 = \
"""
UPDATE cmcnotes
SET webprint_gpt5mini = :webprint_gpt5mini
WHERE id = :id
"""
        conn = engine.connect()
        conn.execute(text(sql2), {"webprint_gpt5mini": response, "id": row['id']})
        conn.commit()
        conn.close()
        print(f"Uploaded response to cmcnotes.webprint_gpt5mini for {row['name']}")

    return rows



rows = hydrate_cmcnotes()
print(f"updated {len(rows)} ids")
pprint(rows)
print("done")



# %%


def hydrate_webprint_distill1s():
    sql = \
"""
SELECT *
FROM cmcnotes
WHERE webprint_distill1s IS NULL
AND webprint_gpt5mini IS NOT NULL
ORDER BY rank ASC
LIMIT 500
"""
    conn = engine.connect()
    rows = conn.execute(text(sql))
    rows = rows.mappings().fetchall()
    conn.close()
    print(f"got: {str([row['name'] for row in rows])} fresh from db")

    for row in rows:

        prompt = f"""
        In only one sentence, describe what this crypto project is and
        the nature of this project. Start with '[name of project] is...'.
        Do not bother defining the ticker/symbol, unless critical to the 
        description. Do your best to refrain from heavy use of acronyms, 
        unless they present critical or highly relevant information.
        Return only one sentence (~30 words). Be as succinct and vivid 
        as possible, with as high information density per token as possible:
        INPUT:
        <<<
        {row['webprint_gpt5mini']}
        >>>
        """

        print(prompt)
        response = gpt5(prompt)
        print(response)

        sql2 = \
"""
UPDATE cmcnotes
SET webprint_distill1s = :webprint_distill1s
WHERE id = :id
"""
        conn = engine.connect()
        conn.execute(text(sql2), {"webprint_distill1s": response, "id": row['id']})
        conn.commit()
        conn.close()
        print(f"Uploaded response to cmcnotes.webprint_distill1s for {row['name']}")


    return rows

rows = hydrate_webprint_distill1s()
print(f"updated {len(rows)} ids")
pprint(rows)
print("done")

# %%


def hydrate_webprint_distill1s_fun() -> int:
    # concurrent hydration version
    # retrieve some null rows to work on
    t0 = time.time()
    sql = """
    SELECT *
    FROM cmcnotes
    WHERE webprint_distill1s_fun IS NULL
    AND webprint_gpt5mini IS NOT NULL
    ORDER BY rank ASC
    LIMIT 200
    """
    conn = engine.connect()
    rows = conn.execute(text(sql))
    rows = rows.mappings().fetchall()
    conn.close()
    print(f"retrieved {len(rows)} rows from db...")

    # define the worker
    def worker(row: dict) -> None:
        # make request to inference api
        prompt = f"""
        In only one sentence, describe what this crypto project is and
        the nature of this project. Start with '[name of project] is...'.
        Do not bother defining the ticker/symbol, unless critical to the 
        description. Imbue your response with sublime and profound humor,
        illuminating the nature of the project, surfacing any irony,
        using sarcasm and wit to poke holes at stupid or naive assumptions,
        and using reverence and admiration for projects which are genuinely
        revolutionary or innovative, keeping in mind the timeframe in which
        these innovations were introduced.
        Do your best to refrain from heavy use of acronyms, 
        unless they present critical or highly relevant information.
        Return only one sentence (~30 words). Be as succinct and vivid 
        as possible, with as high information density per token as possible.

        In order to come up with the best possible response, come up with 5
        alternate responses, ponder each one, and then select the best one 
        from those 5 based off of (1, primarily) the quality of the information it 
        provides, and (2, secondarily), the quality, nuance, and depth of the humor it presents.

        INPUT:
        <<<
        {row['webprint_gpt5mini']}
        >>>
        """
        response = gpt5(prompt)

        # insert into db
        # engine.connect() is safe across threads bc it pulls from a pool.
        # (don't use the same instance across threads)
        sql2 = """
        UPDATE cmcnotes
        SET webprint_distill1s_fun = :webprint_distill1s_fun
        WHERE id = :id
        """
        conn = engine.connect()
        conn.execute(text(sql2), {"webprint_distill1s_fun": response, "id": row['id']})
        conn.commit()
        conn.close()
        print(f".", end="", flush=True)


    # run the workers concurrently (yes this works in ipython)
    rows = [dict(r) for r in rows]
    with ThreadPoolExecutor(max_workers=10) as ex:
        # yes this will surface errors
        list(ex.map(worker, rows))
    dt = time.time() - t0
    print(f"done!")
    return dt


elapsed = hydrate_webprint_distill1s_fun()
print(f"elapsed: {elapsed:.2f}")

#%%
