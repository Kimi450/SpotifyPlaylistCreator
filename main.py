import requests, json, base64, sys, spotipy
from config import CLIENT_ID, CLIENT_SECRET, USER
import spotipy.util as util
from os import listdir
from os.path import isfile, join

def get_ext_files(path,extensions, verbose = False, include_extension = True):
    if verbose:
        print(f"Retrieving files from path and extensions:\n{path}\n{extensions}...")
    files = []
    for file in listdir(path):
        # print(file)
        if isfile(join(path, file)):

            file_split = file.rsplit(".",1)
            # print(len(file_split))
            if len(file_split)>1:
                ext = file_split[-1]
            else:
                continue
            if ext.lower() in extensions:
                if include_extension:
                    files.append(file)
                else:
                    files.append(file_split[0])
            else:
                print(f"{file} not considered")
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
    print(response.status_code)
    if response.status_code != 201:
        raise APIError(f"Couldn't create playlist \"{name}\" for \"{user}\"")
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

class APIError(Exception):
    pass

def add_to_playlist(playlist_id, uris, token):

    # FILL THE NEW PLAYLIST WITH THE RECOMMENDATIONS
    endpoint_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    request_body = json.dumps({
              "uris" : uris
            })
    response = requests.post(url = endpoint_url, data = request_body,
                            headers={"Content-Type":"application/json",
                                     "Authorization":f"Bearer {token}"})
    if response.status_code != 201:
        raise APIError(f"Couldn't add uris \"{uris}\" to playlist_id \"{playlist_id}\"")
    return True

def main():
    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        print("usage:\npython main.py PATH")
        sys.exit()

    TOKEN = get_token(CLIENT_ID, CLIENT_SECRET,USER,"playlist-modify-private")

    playlist_id = "5z4DQFUNLKmiN7au7dK781"

    # uncomment the below 3 lines if you want to create a new folder

    # response = create_playlist(USER, "Old", "Music I had before I migrated to Spotify.", TOKEN)
    # playlist_id = response.json()['id']
    # print(playlist_id)

    endpoint_url = "https://api.spotify.com/v1/search?"
    type = "track"
    limit = 10
    files = get_ext_files(path,["mp3", "m4a", "wav", "flac"],
                          include_extension=False)
    unknown_files = []
    for count, file in enumerate(files):
        # file = "Cold Water (feat. Justin Bieber"

        print(f"{count+1:>5} --- FILE ---> {file}")
        query = f"{endpoint_url}q={file}&type={type}&limit={limit}"

        response = requests.get(query,
                                headers={"Content-Type":"application/json",
                                "Authorization":f"Bearer {TOKEN}"})
        json_response = response.json()
        # print(f"{file}\n{query}\n\n{json_response}\n\n")
        uris = []
        for item_index, item in enumerate(json_response['tracks']["items"]):
            uri = item["uri"]
            uris.append(uri)
            # print(item    _index, uri, item["name"])

        if len(uris) == 0:
            print(f"*** Not found on Spotify: \"{file}\"")
            unknown_files.append(file)
            continue

        add_to_playlist(playlist_id, [uris[0]], TOKEN)

    print("These were not found:")
    for i in unknown_files: print("\t",i)

    return unknown_files
if __name__ == "__main__":
    main()
