#%% ========================================
from openai import OpenAI

from pprint import pprint

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

def gpt5_web(input_text: str) -> str:
    response = client.responses.create(
        model="gpt-5",
        tools=[{"type": "web_search"}],
        reasoning={"effort": "medium"},
        input=input_text
    )
    return response.output_text


def gpt5(input_text: str) -> str:
    response = client.responses.create(
        model="gpt-5",
        reasoning={"effort": "medium"},
        input=input_text
    )
    input_tokens  = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    price_input = input_tokens / 1_000_000 * 1.25
    price_output = output_tokens / 1_000_000 * 10.00
    price_total = price_input + price_output
    print(f"Price: ${price_total:.9f}, Input: ${price_input:.9f}, Output: ${price_output:.9f}")
    return response.output_text


story = gpt5("Write a short one-sentence bedtime story.")
print(story)

#%% ========================================
prompt = \
"""
Look up the following info:
visit each web link and give me a summary of each web link. do your best to be accurate. Load javascript if possible.
Also, find other websites that you can actually load to learn more about the project from these other sites.
(do research on the project from other sites of your choosing as well)
{
  "website": [
    "https://equilibria.fi"
  ],
  "technical_doc": [
    "https://docs.equilibria.fi"
  ]
}
"""


result = gpt5_web(prompt)

#%%
print(result)


#%% ========================================



from openai import OpenAI
from time import sleep

def o3_background(input_text: str) -> str:
    # background mode example:
    # https://platform.openai.com/docs/guides/background
    resp = client.responses.create(
        model="o3",
        input=input_text,
        background=True,
    )

    while resp.status in {"queued", "in_progress"}:
        print(f"Current status: {resp.status}")
        sleep(2)
        resp = client.responses.retrieve(resp.id)

    print(f"Final status: {resp.status}\nOutput:\n{resp.output_text}")

    return resp.output_text


prompt = "Write a short text about otters in space."
response = o3_background(prompt)



#%% ========================================

# TODO: deep research:
# https://platform.openai.com/docs/guides/deep-research
