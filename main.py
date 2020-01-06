import requests
import requests
import json
import base64
from config import CLIENT_ID, CLIENT_SECRET, USER


def create_playlist(user_id, name, description, token, public = False):

    endpoint_url = f"https://api.spotify.com/v1/users/{user_id}/playlists"

    request_body = json.dumps({
              "name": name,
              "description": description,
              "public": public
            })
    response = requests.post(url = endpoint_url,
                            data = request_body,
                            headers={"Content-Type":"application/json",
                                     "Authorization":f"Bearer {token}"})
    print(response.json())
    url = response.json()['external_urls']['spotify']
    return response.status_code, url

def get_token_old(client_id, client_secret):
    # get token using the Client Credentials Flow
    # https://developer.spotify.com/documentation/general/guides/authorization-guide/

    # "client_ID:client_sec" encoded in base64 as per requirements
    basic = bytes(client_id+':'+client_secret,"utf-8")
    basic = base64.b64encode(basic).decode("utf-8")

    response = requests.post(url = "https://accounts.spotify.com/api/token",
                            data = {"grant_type" : "client_credentials"},
                            headers={"Content-Type":"application/x-www-form-urlencoded",
                                     "Authorization":f"Basic {basic}"})
    return response.json()["access_token"]

def get_token(client_id, client_secret, scope):
    url = "https://accounts.spotify.com/authorize?"

    query = f"{url}client_id={client_id}&response_type=code&redirect_uri=https%3A%2F%2Fwww.google.com%2F&state=lol&scope={scope}"
    # print(query)
    response = requests.get(query)
    response_url = response.url

TOKEN = get_token(CLIENT_ID, CLIENT_SECRET,"playlist-modify-public")

create_playlist(USER_ID, "Old", "Music I had before I migrated to Spotify.", TOKEN)

endpoint_url = "https://api.spotify.com/v1/search?"

type = "track"

artist = "michael jackson"
track = "bad"
q = artist + " " + track

# PERFORM THE QUERY
query = f"{endpoint_url}q={q}&type={type}"

response = requests.get(query,
                        headers={"Content-Type":"application/json",
                        "Authorization":f"Bearer {token}"})
json_response = response.json()
# print(json_response)
uris = []
for i,j in enumerate(json_response['tracks']["items"]):
    uri = j["uri"]
    uris.append(uri)
    print(i, uri, j["name"])

"""

# FILL THE NEW PLAYLIST WITH THE RECOMMENDATIONS

playlist_id = response.json()['id']

endpoint_url = base + f"/playlists/{playlist_id}/tracks"

request_body = json.dumps({
          "uris" : uris
        })
response = requests.post(url = endpoint_url, data = request_body, headers={"Content-Type":"application/json",
                        "Authorization":f"Bearer {token}"})

print(response.status_code)
201
print(f'Your playlist is ready at {url}')
"""
