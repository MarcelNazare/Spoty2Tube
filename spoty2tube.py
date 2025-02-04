import os
import json
import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
import youtube_dl
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import re
from tqdm import tqdm

# Configuration
SPOTIFY_CLIENT_ID = 'your_spotify_client_id'
SPOTIFY_CLIENT_SECRET = 'your_spotify_client_secret'
REDIRECT_URI = 'http://localhost:8080'
DOWNLOAD_BASE_PATH = './spotify_downloads/'

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='user-library-read,user-read-recently-played,playlist-read-private'
))

def sanitize_filename(name):
    """Remove invalid characters from filenames"""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def format_size(size_bytes):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"

def get_playlist_tracks(playlist_id):
    """Get all tracks from a playlist"""
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    tracks.extend(results['items'])
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

def download_track(track, output_dir):
    """Download a track from YouTube and convert to MP3"""
    query = f"{track['name']} {track['artists'][0]['name']}"
    safe_query = sanitize_filename(query)
    output_template = f"{output_dir}/{safe_query}.%(ext)s"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)['entries'][0]
            return info
        except Exception as e:
            print(f"\nError downloading {query}: {str(e)}")
            return None

def set_metadata(file_path, track_info):
    """Set MP3 file metadata using Mutagen"""
    try:
        audio = MP3(file_path, ID3=EasyID3)
        audio['title'] = track_info['name']
        audio['artist'] = track_info['artists'][0]['name']
        audio['album'] = track_info['album']['name']
        audio.save()
    except Exception as e:
        print(f"\nError setting metadata for {file_path}: {str(e)}")

def process_tracks(tracks, output_dir, description="Downloading"):
    """Process and download tracks with progress tracking"""
    os.makedirs(output_dir, exist_ok=True)
    total_size = 0
    downloaded_files = []

    with tqdm(total=len(tracks), desc=description, unit='song') as pbar:
        for item in tracks:
            track = item.get('track', item)
            if not track:
                continue

            track_name = sanitize_filename(track['name'])
            artist_name = sanitize_filename(track['artists'][0]['name'])
            filename = f"{track_name} - {artist_name}.mp3"
            file_path = os.path.join(output_dir, filename)

            if os.path.exists(file_path):
                pbar.set_postfix_str(f"Skipped: {filename[:15]}...")
                pbar.update(1)
                continue

            pbar.set_postfix_str(f"Downloading: {filename[:15]}...")
            download_result = download_track(track, output_dir)
            
            if download_result:
                temp_path = f"{output_dir}/{sanitize_filename(download_result['title'])}.mp3"
                os.rename(temp_path, file_path)
                set_metadata(file_path, track)
                
                # Get file size
                file_size = os.path.getsize(file_path)
                total_size += file_size
                pbar.set_postfix_str(f"Downloaded: {format_size(file_size)}")
                
                downloaded_files.append({
                    'path': file_path,
                    'size': file_size
                })

            pbar.update(1)
    
    return total_size, downloaded_files

def main():
    start_time = time.time()
    total_downloaded_size = 0
    all_downloaded_files = []

    # Create base directory
    os.makedirs(DOWNLOAD_BASE_PATH, exist_ok=True)

    # Download recently played tracks
    print("\nFetching recently played tracks...")
    recently_played = sp.current_user_recently_played(limit=50)
    size, files = process_tracks(
        [item['track'] for item in recently_played['items']],
        os.path.join(DOWNLOAD_BASE_PATH, 'Recently Played'),
        "Recent Tracks"
    )
    total_downloaded_size += size
    all_downloaded_files.extend(files)

    # Download saved tracks
    print("\nFetching saved tracks...")
    saved_tracks = sp.current_user_saved_tracks()
    size, files = process_tracks(
        saved_tracks['items'],
        os.path.join(DOWNLOAD_BASE_PATH, 'Liked Songs'),
        "Liked Songs"
    )
    total_downloaded_size += size
    all_downloaded_files.extend(files)

    # Download playlists
    print("\nFetching playlists...")
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if playlist['owner']['id'] == sp.current_user()['id']:
            print(f"\nProcessing playlist: {playlist['name']}")
            tracks = get_playlist_tracks(playlist['id'])
            size, files = process_tracks(
                tracks,
                os.path.join(DOWNLOAD_BASE_PATH, sanitize_filename(playlist['name'])),
                f"Playlist: {playlist['name'][:15]}..."
            )
            total_downloaded_size += size
            all_downloaded_files.extend(files)

    # Calculate total statistics
    total_time = time.time() - start_time
    total_files = len(all_downloaded_files)

    # Print summary
    print("\n" + "="*50)
    print("Download Summary:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Total files downloaded: {total_files}")
    print(f"Total size downloaded: {format_size(total_downloaded_size)}")
    print("="*50)

if __name__ == "__main__":
    main()