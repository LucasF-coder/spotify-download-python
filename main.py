from yt_dlp import YoutubeDL
import requests
from threading import Thread
import os
import re

#Need to use Spotify API
SPOTIFY_CLIENT_ID = "YOUR SPOTIFY CLIENT ID"
SPOTIFY_CLIENT_SECRET = "YOUR SPOTIFY CLIENT SECRET"


def clearName(name):
    name = name.replace(' ', '_').replace('"',"'")
    name = re.sub(r'[\/:*?"<>|]', '', name)
    return name


def getSpotifyToken():
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"Erro: {response.status_code} - {response.text}")
        return None

def getPlaylistJson(token, playlist_id):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro: {response.status_code} - {response.text}")
        return None

def downloadMp3(url,name,path=""):
    print("Downloading: "+name)
    mp3 = requests.get(url)
    path = path.replace(" ","")
    if mp3.encoding != None:
        return print("Unable to download: "+name)
    name = name[:25]
    if not path.endswith("/"):
        path = path + "/"
    if path == "/":
        path = ""
    if path != "":
        if not os.path.exists(path):
            os.makedirs(path)
    with open(path+""+name+".mp3", 'wb') as f:
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
        info_dict = ydl.extract_info(search, download=False)
        video_url = info_dict.get('entries')[0].get('url')
        if video_url:
            return downloadMp3(video_url, clearName(name), path)
    return False


if __name__ == "__main__":
    search = input("Playlist ID or URL:")
    path = input("PATH:")
    if "spotify.com/playlist/" in search:
        search = search.split("playlist/")[1].split("?")[0]
    token = getSpotifyToken()
    if token:
        playlist = getPlaylistJson(token, search)
        if playlist:
            songs = [(item["track"]["name"], item["track"]["artists"][0]["name"]) for item in playlist.get("items", [])]
            print(f"Downloading {len(songs)} songs")
            threads = []
            for song in songs:
                th = Thread(target=start, args=[song[0], song[1], path])
                th.start()
                threads.append(th)
            for th in threads:
                th.join()
            print("Script finished")
        else:
            print("Playlist not found")
    else:
        print("An error occurred while trying to get the token")