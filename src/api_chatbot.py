#%% ========================================
from openai import OpenAI

from pprint import pprint
import time

from src.secrets_ import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

# USAGE:
# https://platform.openai.com/settings/organization/usage

# PRICING/MODELS:
# https://platform.openai.com/docs/pricing

# RESPONSES API:
# https://platform.openai.com/docs/api-reference/responses/create


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


#%% ========================================


def _destructure_usage(response) -> dict:
    raise NotImplementedError()


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


#%% ========================================
