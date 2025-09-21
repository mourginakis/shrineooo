#%%
from pprint import pprint
import requests
import time
import csv

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
example_curl = \
"""
curl 'https://x.com/i/api/1.1/friends/list.json?include_followed_by=1&user_id=1312083283&count=100&cursor=1815661646446788134' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9' \

  -H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \

  -H 'priority: u=1, i' \
  -H 'referer: https://x.com/zxocw/following' \
  -H 'sec-ch-ua: "Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36' \

  -H 'x-twitter-auth-type: OAuth2Session'
"""


#%%

cookies = {

}

headers = {

}

#%% 
def get_following():
    # clean this up?
    # needs to loop over the paginated data.
    # apparently cursor starts at -1 and ends at 0
    params = {
        'include_followed_by': '1',
        'user_id': '1312083283',
        'count': '100',
        'cursor': '-1',
    }

    # description, folowers_count, id_str,
    # name, screen_name
    following = []

    while True:

        response = requests.get(
            'https://x.com/i/api/1.1/friends/list.json',
            params=params,
            cookies=cookies,
            headers=headers,
        )

        data = response.json()
        next_cursor_str = data["next_cursor_str"]
        users = data["users"]
        params['cursor'] = next_cursor_str
        following.extend(users)

        print(f"+{len(users)} users (total: {len(following)}) => next_cursor: {next_cursor_str}")

        if next_cursor_str == '0':
            break

        time.sleep(2)

    return following


result = get_following()


#%%

def destructure_user(user):
    return {
        'id_str': user['id_str'],
        'screen_name': user['screen_name'],
        'name': user['name'],
        'description': user['description'],
        'followers_count': user['followers_count'],
        'url': f"https://x.com/{user['screen_name']}"
    }

#%%

# write to csv

destructured_result = [destructure_user(user) for user in result]

if destructured_result:
    with open('following.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = destructured_result[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(destructured_result)
    print(f"Successfully wrote {len(destructured_result)} users to following.csv")
else:
    print("No users to write to csv.")


#%%

