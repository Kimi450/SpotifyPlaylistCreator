import requests, json, base64, sys, spotipy
from config import CLIENT_ID, CLIENT_SECRET, USER
import spotipy.util as util
from os import listdir
from os.path import isfile, join

def get_ext_files(path,extensions, verbose = False):
    if verbose:
        print(f"Retrieving files from path and extensions:\n{path}\n{extensions}...")
    files = []
    for f in listdir(path):
        # print(f)
        if isfile(join(path, f)):
            ext = f.split(".")
            # print(len(ext))
            if len(ext)>1:
                ext = ext[-1]
            else:
                continue
            if ext.lower() in extensions:
                files.append(f)
            else:
                print(f"{f} not considered")
    # for file in files:
        # print(file)
    if verbose:
        print(f"...{len(files)} files found")
    return files

def create_playlist(user, name, description, token, public = False):

    endpoint_url = f"https://api.spotify.com/v1/users/{user}/playlists"

    request_body = json.dumps({
              "name": name,
              "description": description,
              "public": public
            })
    response = requests.post(url = endpoint_url,
                            data = request_body,
                            headers={"Content-Type":"application/json",
                                     "Authorization":f"Bearer {token}"})
    # print(response.json())
    # url = response.json()['external_urls']['spotify']
    return response

def get_token_old(client_id, client_secret):
    # limited usage, hence not using

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

def get_token(client_id, client_secret, user, scope, redirect_uri = "http://localhost/"):
    # using the spotipy library to perform user level auth
    url = "https://accounts.spotify.com/authorize?"
    token = util.prompt_for_user_token(user,scope, client_id = client_id,
                                       client_secret = client_secret,
                                       redirect_uri = redirect_uri)
    return token

def add_to_playlist(playlist_id, uris, token):

    # FILL THE NEW PLAYLIST WITH THE RECOMMENDATIONS
    endpoint_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

    request_body = json.dumps({
              "uris" : uris
            })
    response = requests.post(url = endpoint_url, data = request_body,
                            headers={"Content-Type":"application/json",
                                     "Authorization":f"Bearer {token}"})
    print("Done!")
    return True

def main():
    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        print("usage:\npython main.py PATH")
        sys.exit()
    files = get_ext_files(path,["mp3", "m4a", "wav", "flac"])

    TOKEN = get_token(CLIENT_ID, CLIENT_SECRET,USER,"playlist-modify-private")
    # response = create_playlist(USER, "Old", "Music I had before I migrated to Spotify.", TOKEN)
    # playlist_id = response.json()['id']
    # print(playlist_id)
    playlist_id = "0c19QMpcD16HLXrX1DdmS9"
    endpoint_url = "https://api.spotify.com/v1/search?"
    type = "track"

    artist = "michael jackson"
    track = "bad"
    q = artist + " " + track

    # PERFORM THE QUERY
    query = f"{endpoint_url}q={q}&type={type}&limit=10"

    response = requests.get(query,
                            headers={"Content-Type":"application/json",
                            "Authorization":f"Bearer {TOKEN}"})
    json_response = response.json()
    # print(json_response)
    uris = []
    for i,j in enumerate(json_response['tracks']["items"]):
        uri = j["uri"]
        uris.append(uri)
        print(i, uri, j["name"])


    add_to_playlist(playlist_id, uris, TOKEN)


if __name__ == "__main__":
    main()
