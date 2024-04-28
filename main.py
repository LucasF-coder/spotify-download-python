import os
import re
import threading
import sys
import requests
from yt_dlp import YoutubeDL

# Need to use Spotify API
SPOTIFY_CLIENT_ID = "YOUR_SPOTIFY_CLIENT_ID"
SPOTIFY_CLIENT_SECRET = "YOUR_SPOTIFY_CLIENT_SECRET"
MAX_SONGS = 100

def clear_name(name):
    name = name.replace(' ', '_').replace('"', "'")
    name = re.sub(r'[\/:*?"<>|]', '', name)
    return name

def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }
    response = requests.post(url, headers=headers, data=data, timeout=10)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)

def get_playlist_json(token, playlist_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)

def download_mp3(url, name, path=""):
    print("Downloading: " + name)
    mp3 = requests.get(url, timeout=10)
    path = path.replace(" ", "")
    if mp3.encoding is None:
        return print("Unable to download: " + name)
    name = name[:25]
    if not path.endswith("/"):
        path = path + "/"
    if path == "/":
        path = ""
    if path != "":
        if not os.path.exists(path):
            os.makedirs(path)
    with open(path + "" + name + ".mp3", 'wb') as f:
        f.write(mp3.content)

def start(name, artist, path="/"):
    search = f"ytsearch:{name} - {artist}"
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        "external_downloader_args": ['-loglevel', 'panic'],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(search, download=False)
            video_url = info_dict.get('entries')[0].get('url')
            if video_url:
                return download_mp3(video_url, clear_name(name), path)
        except Exception as e:
            print(f"Error: {e}")
    return False

if __name__ == "__main__":
    search = input("Playlist ID or URL:")
    path = input("PATH:")
    if "spotify.com/playlist/" in search:
        search = search.split("playlist/")[1].split("?")[0]
    else:
        print("Invalid input. Please provide a Spotify playlist ID or URL.")
        sys.exit(1)

    token = get_spotify_token()
    if token:
        playlist = get_playlist_json(token, search)
        if playlist:
            if "tracks" in playlist:
                songs = [(item["track"]["name"], item["track"]["artists"][0]["name"]) for item in playlist.get("items", [])]
                print(f"Downloading {len(songs)} songs")
                if len(songs) > MAX_SONGS:
                    print(f"Warning: {len(songs)} songs found, only downloading the first {MAX_SONGS}.")
                    songs = songs[:MAX_SONGS]
                threads = []
                for song in songs:
                    th = threading.Thread(target=start, args=[song[0], song[1], path])
                    th.start()
                    threads.append(th)
                for th in threads:
                    th.join()
                print("Script finished")
            else:
                print("Playlist not found")
        else:
            print("An error occurred while trying to get the playlist data")
    else:
        print("An error occurred while trying to get the token")
