#%% ========================================
import time
import csv
import re
from pprint import pprint
from dataclasses import dataclass, asdict

import requests
from selenium import webdriver

from src.secrets_ import XAPI_CURL

# Notes:
# So even though Elon completely locked down the API and limits it to like seeing only 70 following,
# There seems to be ways to still get all following using undocumented/old endpoints.
# This extension (https://github.dev/dimdenGD/OldTwitter/) seems to be accessing an old API
# under the hood. It seems to use two different possible endpoints, getFollowing and getFollowingV2
# getFollowing is older, getFollowingV2 seems to be using graphql.
# They both use a cursor and paginate the data. I could not get getFollowingV2 to work.
# getFollowing URL:
# https://x.com/i/api/1.1/friends/list.json?include_followed_by=1&user_id=1312083283&count=100&cursor=1815661646446788134
# getFollowingV2:
# https://x.com/i/api/graphql/t-BPOrMIduGUJWO_LxcvNQ/Following?
# Latest GraphQL endpoint (from my research):
# https://x.com/i/api/graphql/RtAIEonfojl3X_l8q56-1w/Following?
# it seems like you can still pass a 'cursor' param into the features json in getFollowingV2,
# but I tried it and it didn't work. This could be my error. But the old API is easier to use
# anyways.
# how to get the cookies/curl (for the chrome extension version):
# click following -> inspect element -> network -> filter 'friends/list' -> copy curl


# Since we're plugged into the unofficial API, we need to parse
# the credentials from the browser's cookies and headers.
# Inspect element lets us get all the relevant info in a
# copy/pastable cURL command, so the idea is to copy this
# into a string here, and then write a little function to parse
# that cURL command into the necessary cookies and headers.
# To get this cURL command:
# 1. Login using dimden's old twitter extension (https://github.dev/dimdenGD/OldTwitter/)
# 2. Click on a user -> following
# 3. Inspect element -> network -> filter 'list.json' -> right click -> copy cURL
# 4. Paste into curl_str
# (it looks like this lasts >1 week at least)

# EXAMPLE: this cURL is incomplete and will fail!
curl_str = \
"""
curl 'https://x.com/i/api/1.1/friends/list.json?include_followed_by=1&user_id=1312083283&count=100&cursor=1815661646446788134' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9' \
  -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'priority: u=1, i' \
  -H 'sec-ch-ua: "Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36' \
  -H 'x-twitter-auth-type: OAuth2Session'
"""

import re
import shlex
from http.cookies import SimpleCookie

def parse_curl_headers_cookies(curl_text: str) -> tuple[dict, dict]:
    """This function takes a raw copy and pasted cURL command and
    parses it into a dictionary of headers and cookies (to be used
    for requests)"""
    # ChatGPT wrote this thank you chatgpt <3
    # Join lines with trailing backslashes and strip the leading 'curl'
    # quick explanation: this is a blackbox function that takes a raw cURL command
    # and parses it into dictionaries of headers and cookies.

    def parse_cookie_string(cookie_str: str) -> dict:
        jar = SimpleCookie()
        jar.load(cookie_str)
        return {k: v.value for k, v in jar.items()}

    s = re.sub(r"\\\s*\r?\n", " ", curl_text).strip()
    if s.lower().startswith("curl "):
        s = s[5:]

    tokens = shlex.split(s, posix=True)

    headers: dict[str, str] = {}
    cookies: dict[str, str] = {}

    def add_header(raw: str):
        if ":" not in raw:
            return
        name, value = raw.split(":", 1)
        name, value = name.strip(), value.strip()
        if name.lower() == "cookie":
            cookies.update(parse_cookie_string(value))
        else:
            headers[name] = value

    def add_cookie(raw: str):
        # If it's a cookie string (not a file path), parse it
        if "=" in raw:
            cookies.update(parse_cookie_string(raw))
        # else: could be a cookie jar file path; out of scope here

    i = 0
    while i < len(tokens):
        t = tokens[i]

        # --header value or --header=value
        if t in ("-H", "--header") and i + 1 < len(tokens):
            add_header(tokens[i + 1]); i += 2; continue
        if t.startswith("--header="):
            add_header(t.split("=", 1)[1]); i += 1; continue

        # --cookie value or --cookie=value
        if t in ("-b", "--cookie") and i + 1 < len(tokens):
            add_cookie(tokens[i + 1]); i += 2; continue
        if t.startswith("--cookie="):
            add_cookie(t.split("=", 1)[1]); i += 1; continue

        i += 1

    return headers, cookies

# TODO: load curl_str from dotenv instead?
headers, cookies = parse_curl_headers_cookies(XAPI_CURL)
print(f"xapi: successfully parsed headers and cookies!")


#%% ========================================
# SELENIUM quick and dirty hacks to get
# user_id -> url
# url -> user_id

def get_user_id_selenium(url: str) -> int:
    """renders js page with selenium quick and dirty.
    example: https://x.com/zxocw
    errors if regex is not found."""
    # load selenium and get the webpage (we need js)
    # wait for js to load (2s)
    # https://gist.github.com/kentbrew/8942accb5c584f11a775af02d097dd40
    opts = webdriver.ChromeOptions()
    opts.add_argument('--headless')
    driver = webdriver.Chrome(options=opts)
    driver.get(url)
    time.sleep(1)
    src = driver.page_source
    driver.quit()
    PAT = re.compile(r'https?://pbs\.twimg\.com/profile_banners/(\d+)(?:/|$)')
    m = PAT.search(src)
    userid = m.group(1)
    userid = int(userid)
    return userid


def user_id_to_url_selenium(id: int) -> str:
    """quick and dirty selenium hack to get the url of a user.
    twitter seems to not redirect unless you have user-agent."""
    id = str(id)
    opts = webdriver.ChromeOptions()
    opts.add_argument('--headless')
    opts.add_argument("--window-size=1280,800")
    opts.add_argument(
        "user-agent="
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124 Safari/537.36"
    )
    driver = webdriver.Chrome(options=opts)
    starturl   = f"https://x.com/i/user/{id}"
    currenturl = starturl
    driver.get(starturl)
    t0 = time.time()
    while True:
        dt = time.time() - t0
        currenturl = driver.current_url
        if currenturl != starturl:
            break
        if dt > 5:
            break
        time.sleep(1)
    driver.quit()
    if currenturl != starturl:
        return currenturl
    raise ValueError(f"Could not resolve profile URL for {id}")



#%% ========================================


@dataclass
class Profile:
    id:              int
    screen_name:     str
    name:            str
    description:     str
    followers_count: int
    urlpinned:       str
    urlprofile:      str


# TODO: get more data into the dataclass?
# TODO: get expanded urls? rn its t.co/ links.

def get_targets(id: int) -> list[Profile]:
    """given an id, get the people that user follows."""
    # clean this up? needs to loop over paginated data.
    # apparently cursor starts at -1 and ends at 0
    params = {
        'include_followed_by': '1',
        'user_id': str(id),
        'count': '100',
        'cursor': '-1',
    }
    # not sure if we need this...
    headers['referer'] = ""
    # targets is a list of Profile objects
    targets: list[Profile] = []
    # start infinite loop
    while True:
        # get the data
        response = requests.get(
            'https://x.com/i/api/1.1/friends/list.json',
            params=params,
            cookies=cookies,
            headers=headers,
        )
        # destructure data
        data = response.json()
        next_cursor_str = data["next_cursor_str"]
        users = data["users"]
        for user in users:
            profile = Profile(
                id             =int(user['id_str']),
                screen_name    =user['screen_name'],
                name           =user['name'],
                description    =user['description'],
                followers_count=user['followers_count'],
                urlpinned      =user['url'],
                urlprofile     =f"https://x.com/{user['screen_name']}",
            )
            targets.append(profile)
        # update params
        params['cursor'] = next_cursor_str
        print(f"+{len(users)} users (total: {len(targets)}) => next_cursor: {next_cursor_str}")
        # break if we've reached the end
        if next_cursor_str == '0':
            break
        # wait to avoid suspicion
        time.sleep(2)
    return targets

#%% ========================================
# tests:

# uid = get_user_id_selenium("https://x.com/realGeorgeHotz/")
# print(uid)
# print(type(uid))

# url = user_id_to_url_selenium(uid)
# print(url)
# print(type(url))

# result = get_targets(uid)
# import json
# with open('targets.json', 'w') as f:
#     dicts = [asdict(p) for p in result]
#     json.dump(dicts, f)

