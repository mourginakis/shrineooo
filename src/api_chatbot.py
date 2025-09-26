#%% ========================================
import json
from openai import OpenAI
from openai.types.responses import Response

from pprint import pprint
import time

from src.secrets_ import OPENAI_API_KEY

mins15 = 15 * 60
client = OpenAI(api_key=OPENAI_API_KEY, timeout=mins15)

# USAGE:
# https://platform.openai.com/settings/organization/usage
# https://platform.openai.com/batches/

# PRICING/MODELS:
# https://platform.openai.com/docs/pricing

# RESPONSES API:
# https://platform.openai.com/docs/api-reference/responses/create

# BATCH API:
# https://platform.openai.com/docs/guides/batch



# PRICING SNAPSHOT (SEPTEMBER 2025):
# Model	                  Input	     Cached input     Output
# gpt-5      	          $1.25	     $0.125	          $10.00
# gpt-5-mini	          $0.25	     $0.025	           $2.00
# gpt-5-nano	          $0.05	     $0.005	           $0.40
# o3-deep-research	     $10.00	     $2.50	          $40.00
# o4-mini-deep-research	  $2.00	     $0.50	           $8.00
# Web search preview (gpt-5, o-series) [1]	$10.00 / 1k calls
# Web search (all models) [1]	$10.00 / 1k calls

# deepseek-reasoner:     $0.56     $0.07      $1.68   


# QUICK REFERENCE::
# reasoning: { effort: "minimal" | "low" | "medium" | "high" }
# defaults to "medium"
# tools: [{"type": "web_search"}]
# web search does not work with minimal effort
# models: gpt-5, gpt-5-mini, gpt-5-nano


# Batch API and flex service level are considerably cheaper.
# I would've liked to use BatchAPI with web search, but it's
# not currently supported. Flex seems just as cheap though.
# the default timeout is 10 mins. May need to increase to 15 mins.


#%% ========================================


def _destructure_usage(response: Response) -> dict:
    ncalls = sum([getattr(i, "type", "") == "web_search_call" 
                  for i in (response.output or [])])
    d = {"nwebcalls":   ncalls,
         "ntokens_in":  response.usage.input_tokens,
         "ntokens_out": response.usage.output_tokens}
    return d


def gpt5_web(input_text: str) -> str:
    response = client.responses.create(
        model="gpt-5",
        tools=[{"type": "web_search"}],
        reasoning={"effort": "medium"},
        input=input_text
    )
    # tabulate usage cost
    calls      = sum([getattr(i, "type", "") == "web_search_call" 
                      for i in (response.output or [])])
    tokens_in  = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    cost_calls = calls * 10.00 / 1000
    cost_in    = tokens_in / 1_000_000 * 1.25
    cost_out   = tokens_out / 1_000_000 * 10.00
    cost_total = cost_calls + cost_in + cost_out
    print(f"price: ${cost_total:.4f}, calls: ${cost_calls:.4f}, input: ${cost_in:.4f}, output: ${cost_out:.4f}")
    return response.output_text


def gpt5_web_flex(input_text: str) -> str:
    response = client.responses.create(
        model="gpt-5",
        tools=[{"type": "web_search"}],
        reasoning={"effort": "medium"},
        input=input_text,
        service_tier="flex",
    )
    # tabulate usage cost
    calls      = sum([getattr(i, "type", "") == "web_search_call" 
                      for i in (response.output or [])])
    tokens_in  = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    cost_calls = calls * 10.00 / 1000
    cost_in    = tokens_in / 1_000_000 * 0.625
    cost_out   = tokens_out / 1_000_000 * 5.00
    cost_total = cost_calls + cost_in + cost_out
    print(f"price: ${cost_total:.4f}, calls: ${cost_calls:.4f}, input: ${cost_in:.4f}, output: ${cost_out:.4f}")
    return response.output_text


def gpt5_web_flex_mini(input_text: str) -> str:
    response = client.responses.create(
        model="gpt-5-mini",
        tools=[{"type": "web_search"}],
        reasoning={"effort": "medium"},
        input=input_text,
        service_tier="flex",
    )
    # tabulate usage cost
    calls      = sum([getattr(i, "type", "") == "web_search_call" 
                      for i in (response.output or [])])
    tokens_in  = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    cost_calls = calls * 10.00 / 1000
    cost_in    = tokens_in / 1_000_000 * 0.125
    cost_out   = tokens_out / 1_000_000 * 1.00
    cost_total = cost_calls + cost_in + cost_out
    print(f"price: ${cost_total:.4f}, calls: ${cost_calls:.4f}, input: ${cost_in:.4f}, output: ${cost_out:.4f}")
    return response.output_text


def gpt5(input_text: str) -> str:
    response = client.responses.create(
        model="gpt-5",
        reasoning={"effort": "medium"},
        input=input_text
    )
    # tabulate usage cost
    tokens_in  = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    cost_in    = tokens_in / 1_000_000 * 1.25
    cost_out   = tokens_out / 1_000_000 * 10.00
    cost_total = cost_in + cost_out
    print(f"price: ${cost_total:.4f}, input: ${cost_in:.4f}, output: ${cost_out:.4f}")
    return response.output_text


def o3_background(input_text: str) -> str:
    # background mode example:
    # https://platform.openai.com/docs/guides/background
    resp = client.responses.create(
        model="o3",
        input=input_text,
        background=True,
    )

    t0 = time.time()
    while True:

        dt = time.time() - t0
        if resp.status not in {"queued", "in_progress"}:
            break

        time.sleep(10)
        print(f"polling, elapsed: {dt:.2f}s")
        resp = client.responses.retrieve(resp.id)

    print(f"Done! {resp.status}. elapsed: {dt:.2f}s")
    return resp.output_text


def o3_deep_research(input_text: str) -> str:
    # deep research in background mode
    # https://platform.openai.com/docs/guides/deep-research
    resp = client.responses.create(
        model="o3-deep-research",
        input=input_text,
        background=True,
        tools=[{"type": "web_search"}],
    )

    t0 = time.time()
    while True:

        dt = time.time() - t0
        if resp.status not in {"queued", "in_progress"}:
            break

        time.sleep(60)
        print(f"polling, elapsed: {dt:.2f}s")
        resp = client.responses.retrieve(resp.id)

    print(f"Done! {resp.status}. elapsed: {dt:.2f}s")
    return resp.output_text

# We don't really have a use for the Batch API anymore
# because we can just call service tier flex.
#
# def batchjob(prompts: list[str]) -> str:
#     # construct payload
#     # Sep 2025: error Web search is not supported in the Batch API??
#     payload = []
#     for i, prompt in enumerate(prompts):
#         payload.append({
#             "custom_id": f"req-{i:04d}",
#             "method": "POST",
#             "url": "/v1/responses",
#             "body": {
#                 "model": "gpt-5",
#                 "reasoning": {"effort": "medium"},
#                 # "tools": [{"type": "web_search"}],
#                 "input": prompt,
#             }
#         })
#     # write payload to file
#     t0    = time.time()
#     fname = f"{int(t0)}.jsonl"
#     with open(fname, "w", encoding="utf-8") as f:
#         for obj in payload:
#             f.write(json.dumps(obj, ensure_ascii=False) + "\n")
#     # upload file to OpenAI
#     batchfile = client.files.create(
#         file=open(fname, "rb"),
#         purpose="batch",
#     )
#     # create job
#     batchfile_id = batchfile.id
#     metadata = client.batches.create(
#         input_file_id=batchfile_id,
#         endpoint="/v1/responses",
#         completion_window="24h",
#         metadata={"description": "batch job"}
#     )
#     # write metadata to disk
#     with open(f"{int(t0)}.metadata.json", "w", encoding="utf-8") as f:
#         f.write(metadata.model_dump_json(indent=2))
#     batchid = metadata.id
#     return batchid


# def batchjob_get(batchid: str):
#     status = client.batches.retrieve(batchid)
#     file_response = client.files.content(status.output_file_id)
#     pprint(dir(file_response))
#     with open(f"done.jsonl", "w", encoding="utf-8") as f:
#         f.write(file_response.text)
#     return status, file_response

# def batchjob_listall():
#     resp = client.batches.list(limit=10)
#     pprint(resp.model_dump())


#%% ========================================
