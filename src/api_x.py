#%% ========================================
from dataclasses import dataclass
import time
import csv
import re
from pprint import pprint
from dataclasses import dataclass, asdict

import requests
from selenium import webdriver

from utils import parse_curl_headers_cookies

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

curl_str = \
"""
"""

headers, cookies = parse_curl_headers_cookies(curl_str)
print(f"xapi: successfully parsed headers and cookies!")


#%% ========================================
# SELENIUM quick and dirty hacks to get
# user_id -> url
# url -> user_id

def get_user_id_selenium(url: str):
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
    return userid


def user_id_to_url_selenium(id: int):
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
