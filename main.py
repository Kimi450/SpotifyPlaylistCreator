import requests, json, base64, sys, spotipy
from config import CLIENT_ID, CLIENT_SECRET, USER
import spotipy.util as util
from os import listdir
from os.path import isfile, join

from Levenshtein import distance

def get_files(path,extensions, verbose = False, include_extension = True):
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

def get_token(client_id, client_secret, user, scope, redirect_uri = "http://localhost/"):
    # using the spotipy library to perform user level auth
    url = "https://accounts.spotify.com/authorize?"
    token = util.prompt_for_user_token(user,scope, client_id = client_id,
                                       client_secret = client_secret,
                                       redirect_uri = redirect_uri)
    return token

def get_spotify_album_data(item):
    album_artists = []
    for object in item["album"]["artists"]:
        album_artists.append(object["name"])
    album_name = item["album"]["name"]
    album_release_date = item["album"]["release_date"]
    return (album_name, album_release_date, album_artists)

def get_spotify_artist_data(item):
    artists = []
    for object in item["artists"]:
        artists.append(object["name"])
    return artists

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
    if response.status_code != 201:
        raise APIError(f"Couldn't create playlist \"{name}\" for \"{user}\"")
    return response

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

def get_best_match_uri(items, file):

    best_match_cost = sys.maxsize
    best_match_uri = None
    for item_index, item in enumerate(items):
        name = item["name"]
        edit_dist_name = distance(file,name)
        # print(f"{edit_dist_name:>2}: {file} -> {name}")
        if edit_dist_name <= best_match_cost:
            # print(get_spotify_album_data(item))
            # print(get_spotify_artist_data(item))
            best_match_cost = edit_dist_name
            uri = item["uri"]
            best_match_uri = uri

    return best_match_uri

def add_files_to_playlist(files, playlist_id, token, type = "track"):
    unknown_files = []
    endpoint_url = "https://api.spotify.com/v1/search?"
    limit = 10
    for count, file in enumerate(files):
        file = "Cold Water (feat. Justin Bieber"
        # file = "Keep Me In Your Heart For A While"
        # file = "creep postmodern"
        print(f"{count+1:>5} --- File ", end="")
        query = f"{endpoint_url}q={file}&type={type}&limit={limit}"

        response = requests.get(query,
                                headers={"Content-Type":"application/json",
                                         "Authorization":f"Bearer {token}"})
        json_response = response.json()

        if response.status_code != 200:
            raise APIError(f"Failed query: {json_response}")

        best_match_uri = get_best_match_uri(json_response['tracks']["items"], file)

        if best_match_uri == None:
            print(f"NOT found on Spotify: \"{file}\"")
            unknown_files.append(file)
            continue

        add_to_playlist(playlist_id, [best_match_uri], token)
        print(f"Added on spotify    : \"{file}\"")
        # exit()

        # parsed = json.loads(json.dumps(json_response))
        # print(json.dumps(parsed, indent=4, sort_keys=True))

    return unknown_files

def main():
    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        print("usage:\npython main.py PATH")
        sys.exit()

    TOKEN = get_token(CLIENT_ID, CLIENT_SECRET,USER,"playlist-modify-private")

    playlist_id = "1FHMnsDFjDrNdqpRr9l4lx"

    # uncomment the below 3 lines if you want to create a new folder

    # response = create_playlist(USER, "Old",
    #                            "Music I had before I migrated to Spotify.",
    #                            TOKEN)
    # playlist_id = response.json()['id']

    # print(playlist_id)

    files = get_files(path, ["mp3", "m4a", "wav", "flac"],
                      include_extension = False)

    # files.reverse()
    unknown_files = add_files_to_playlist(files,playlist_id, TOKEN)

    print("*** These were not found ***")
    for i in unknown_files: print(i)



if __name__ == "__main__":
    main()
