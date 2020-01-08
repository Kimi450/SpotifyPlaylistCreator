import requests, json, base64, sys, spotipy
from config import CLIENT_ID, CLIENT_SECRET, USER
import spotipy.util as util
from os import listdir
from os.path import isfile, join, splitext

from Levenshtein import distance

from tinytag import TinyTag
from apierror import APIError

def get_files(path, extensions, verbose=False):
    """
    Returns the files of specified "extensions" from the passed in "path".
    The verbose tag prints out more messages.
    """
    if verbose:
        print(f"Retrieving files from path and extensions:\n{path}\n{extensions}...")
    files = []
    for file in listdir(path):
        if isfile(join(path, file)):
            base, ext = split_file(file)
            if ext.lower() in extensions:
                files.append(file)
            else:
                print(f"{file} not considered")
    if verbose:
        print(f"...{len(files)} files found")
    return files

def get_token(client_id, client_secret, user, scope, redirect_uri="http://localhost/"):
    """
    Returns a User Credential Flow token
    using the spotipy library to perform the auth

    May have to include the redirect_uri in the acceptable redirects
    for you app on spotify. This is where you get the client_id
    and client_secret from as well.
    """
    url = "https://accounts.spotify.com/authorize?"
    token = util.prompt_for_user_token(user,scope, client_id = client_id,
                                       client_secret = client_secret,
                                       redirect_uri = redirect_uri)
    return token

def get_spotify_album_data(item):
    """
    Returns a tupe the album name, album release_date and
    a list of album artists from the item object passed in.
    """
    album_artists = []
    for object in item["album"]["artists"]:
        album_artists.append(object["name"])
    album_name = item["album"]["name"]
    album_release_date = item["album"]["release_date"]
    return (album_name, album_release_date, album_artists)

def get_spotify_artist_data(item):
    """
    Returns a list of artists from the item object passed in
    """
    artists = []
    for object in item["artists"]:
        artists.append(object["name"])
    return artists

def create_playlist(user, name, description, token, public = False):
    """
    Creates a playlist for user "user", with name "name", description of
    "description" and decides whether or not it should be public (default
    to private).
    """
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
        raise APIError(f"POST request failed: Couldn't create \
        playlist \"{name}\" for \"{user}\"\n{response.json}")
    return response

def add_to_playlist(playlist_id, uris, token):
    """
    Return true if successfully added the "uris" to the plalist with id
    "playlist_id".
    Raises APIError if response status code is not 201 as expected.
    """
    endpoint_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    request_body = json.dumps({
              "uris" : uris
            })
    response = requests.post(url = endpoint_url, data = request_body,
                            headers={"Content-Type":"application/json",
                                     "Authorization":f"Bearer {token}"})
    if response.status_code != 201:
        raise APIError(f"POST request failed: Couldn't add uris \"{uris}\" \
        to playlist_id \"{playlist_id}\"\n{response.json}")
    return True

def get_best_match_uri(items, file):
    """
    Return the best matched URI for the "file" passed in.
    Uses Levenshtein distance to find the best match by finding
    lowest edit ditance between query (file) and the "items" found on spotify
    """
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

def split_file(file):
    base, ext = splitext(file)
    ext = ext.replace(".", "", 1)
    return (base, ext)

def add_files_to_playlist(path, files, playlist_id, token, type = "track"):
    """
    Search tracks the files in list "files" on Spotify
    and add them to "playlist_id"
    Raises APIError if the search query fails.
    Return the list of unknown files (files not found on spotify)
    """
    unknown_files = []
    endpoint_url = "https://api.spotify.com/v1/search?"
    limit = 10
    for count, file in enumerate(files):
        og_file = file
        file_name, file_ext = split_file(file)

        file_path = join(path,f"{file_name}.{file_ext}")
        file_metadata = TinyTag.get(file_path)

        file_title = file_metadata.title
        file_artist = file_metadata.artist
        # if these are Nones, the strip and join will fail
        file_title = file_title if file_title else ""
        file_artist = file_artist if file_artist else ""

        file_title = file_title.strip('\x00')
        file_artist = file_artist.strip('\x00')

        file_set = {file_title, file_artist} # to remove duplicates

        if file_set == {""}:
            # if its a set of just an empty string, use the file
            # name for the search
            file = file_name
        else:
            # else use the attributes found, by joining them
            # with a space to do the search
            file = " ".join(file_set)

        file = file.replace("#","") # to remove "#" that act as IDs in the URL
        print(f"{count+1:>5} --- File ", end="")
        query = f"{endpoint_url}q={file}&type={type}&limit={limit}"
        response = requests.get(query,
                                headers={"Content-Type":"application/json",
                                         "Authorization":f"Bearer {token}"})

        json_response = response.json()
        if response.status_code != 200: # not a successful query
            raise APIError(f"GET request failed: {json_response}")

        # get the best URI match between the file and the passed in items
        best_match_uri = get_best_match_uri(json_response['tracks']["items"],
                                            file)

        if best_match_uri == None:
            # if not match found, make a note of the file and go to the next one
            print(f"NOT found on Spotify: \"{file}\"")
            unknown_files.append((og_file,file_artist,file_title))
            continue

        # add the best URI to the playlist
        add_to_playlist(playlist_id, [best_match_uri], token)
        print(f"added on spotify    : \"{file}\"")
        # parsed = json.loads(json.dumps(json_response))
        # print(json.dumps(parsed, indent=4, sort_keys=True))

    # return the list of unknown files
    return unknown_files

def main():
    """
    Main method
    """
    if len(sys.argv) == 2:
        path = sys.argv[1]
    else:
        print("usage:\npython main.py PATH")
        sys.exit()

    TOKEN = get_token(CLIENT_ID, CLIENT_SECRET,USER,"playlist-modify-private")

    playlist_id = "0aIyRup0xOjwbY0Ncw8dY2"
    response = create_playlist(USER, "Old",
                               "Music I had before I migrated to Spotify.",
                               TOKEN)
    playlist_id = response.json()['id']
    print(playlist_id)

    files = get_files(path, ["mp3", "m4a", "wav", "flac"])

    unknown_files = add_files_to_playlist(path, files,playlist_id, TOKEN)

    print(f"{len(files)-len(unknown_files)}/{len(files)} were found")
    file_name = "unknown_files.csv"
    print(f"** Unknown files will be written to {file_name} in app home dir **")
    with open(file_name, "w", encoding = "utf-8") as output:
        output.write("actual_file_name,file_artist,file_title,\n")
        for file in unknown_files:
            output.write(f"{file[0]},{file[1]},{file[2]},\n")

if __name__ == "__main__":
    main()
