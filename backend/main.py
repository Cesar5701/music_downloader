import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import acoustid
import musicbrainzngs
import mutagen.id3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TCON, TDRC, TRCK, ID3NoHeaderError
from dotenv import load_dotenv

load_dotenv()

musicbrainzngs.set_useragent('MusicDownloaderPro', '1.0', 'tu_email@ejemplo.com')
ACOUSTID_API_KEY = os.getenv('ACOUSTID_API_KEY', '')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diccionario global para mantener el progreso actual de cada video
download_progress = {}

from typing import Optional, List

class DownloadRequest(BaseModel):
    url: str
    urls: Optional[List[str]] = []
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None

@app.get("/")
def read_root():
    return {
        "message": "Backend de MusicDownloader Pro activo.",
        "status": "success",
        "documentation": "/docs"
    }

@app.get("/progress")
def get_progress():
    return download_progress

@app.get("/info")
def get_info(url: str):
    ydl_opts = {'quiet': True, 'extract_flat': True, 'http_headers': {'User-Agent': 'Mozilla/5.0'}}
    
    # Asegurar obtener solo música usando búsqueda en YouTube Music
    if not url.startswith("http") and not url.startswith("ytmsearch:") and not url.startswith("ytsearch:"):
        url = f"ytmsearch5:{url}"
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if 'entries' in info:
                return {
                    "is_playlist": True,
                    "title": info.get('title'),
                    "artist": info.get('uploader'),
                    "tracks": [{"id": e.get('id'), "title": e.get('title'), "url": e.get('url')} for e in info.get('entries', []) if e.get('url')]
                }
            return {
                "is_playlist": False,
                "title": info.get('title'),
                "artist": info.get('uploader'),
                "album": info.get('album'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "id": info.get('id')
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/download")
def download_audio(req: DownloadRequest):
    output_dir = "media/downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    import re
    def sanitize(name):
        return re.sub(r'[\\/*?:"<>|]', "", str(name))

    # Descarga bajo archivo temporal usando el ID del video
    temp_filename = "%(id)s"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/{temp_filename}.%(ext)s',
        'writethumbnail': True,
        'writeinfojson': True,
        'quiet': False,
        'progress_hooks': [lambda d: update_progress(d)],
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320', # MP3 320kbps
            },
            {
                'key': 'FFmpegThumbnailsConvertor',
                'format': 'jpg',
            },
            {
                'key': 'EmbedThumbnail',
            },
        ],
        'postprocessor_args': {
            'thumbnailsconvertor': ['-vf', 'crop=min(in_w\,in_h):min(in_w\,in_h)']
        }
    }

    def update_progress(d):
        video_id = d.get('info_dict', {}).get('id')
        if not video_id:
            return
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            percent = (downloaded / total * 100) if total else 0
            download_progress[video_id] = {
                'status': 'downloading',
                'percent': percent,
                'speed': speed
            }
        elif d['status'] == 'finished':
            download_progress[video_id] = {
                'status': 'processing',
                'percent': 100,
                'speed': 0
            }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            if req.urls and len(req.urls) > 0:
                ydl.download(req.urls)
            else:
                ydl.download([req.url])
            
            # Procesar todos los mp3 generados
            import glob
            mp3_files = glob.glob(os.path.join(output_dir, "*.mp3"))
            
            for temp_filepath in mp3_files:
                # Saltar archivos que ya parezcan estar renombrados (tienen ' - ' en el nombre)
                filename = os.path.basename(temp_filepath)
                if "-" in filename and not len(filename) == 15: # heuristic for processed files, or maybe we just check if it's strictly a video ID
                    continue
                
                final_title = req.title or "Unknown Title"
                final_artist = req.artist or "Unknown Artist"
                final_album = req.album or ""
                final_year = ""
                final_genre = ""
                final_track_number = ""
                final_album_artist = ""
                
                video_id = filename.replace(".mp3", "")
                info_json_path = os.path.join(output_dir, f"{video_id}.info.json")
                if os.path.exists(info_json_path):
                    import json
                    try:
                        with open(info_json_path, 'r', encoding='utf-8') as f:
                            track_info = json.load(f)
                            # Tomar metadatos del JSON como fallback más certero que el req general de la playlist
                            final_title = track_info.get('title', final_title)
                            final_artist = track_info.get('artist', track_info.get('uploader', final_artist))
                            final_album = track_info.get('album', final_album)
                            final_year = str(track_info.get('release_date', ''))[:4] or str(track_info.get('release_year', '')) or final_year
                            final_genre = track_info.get('genre', final_genre)
                            final_track_number = str(track_info.get('track_number', '')) or final_track_number
                            final_album_artist = track_info.get('album_artist', final_album_artist)
                    except:
                        pass
                
                # Búsqueda de metadata mediante Audio Fingerprinting y MusicBrainz
                try:
                    if ACOUSTID_API_KEY:
                        results = acoustid.match(ACOUSTID_API_KEY, temp_filepath)
                        for score, recording_id, title, artist in results:
                            mb_data = musicbrainzngs.get_recording_by_id(recording_id, includes=['releases', 'artists', 'tags'])
                            recording = mb_data.get('recording', {})
                            
                            final_title = recording.get('title', final_title)
                            
                            if 'artist-credit' in recording and len(recording['artist-credit']) > 0:
                                final_artist = recording['artist-credit'][0].get('artist', {}).get('name', final_artist)
                                
                            if 'release-list' in recording and len(recording['release-list']) > 0:
                                release = recording['release-list'][0]
                                final_album = release.get('title', final_album)
                                if release.get('date'):
                                    final_year = release.get('date')[:4]
                                    
                            if 'tag-list' in recording and len(recording['tag-list']) > 0:
                                final_genre = recording['tag-list'][0].get('name', final_genre)
                            break 
                    else:
                        # Fallback a MusicBrainz mediante búsqueda de texto si no hay AcoustID API KEY habilitada
                        query = f'recording:"{final_title}"'
                        if final_artist and final_artist != "Unknown Artist":
                            query += f' AND artist:"{final_artist}"'
                        
                        mb_search = musicbrainzngs.search_recordings(query=query, limit=1)
                        if mb_search.get('recording-list'):
                            recording = mb_search['recording-list'][0]
                            final_title = recording.get('title', final_title)
                            
                            if 'artist-credit' in recording and len(recording['artist-credit']) > 0:
                                final_artist = recording['artist-credit'][0].get('artist', {}).get('name', final_artist)
                                
                            if 'release-list' in recording and len(recording['release-list']) > 0:
                                release = recording['release-list'][0]
                                final_album = release.get('title', final_album)
                                if release.get('date'):
                                    final_year = release.get('date')[:4]
                                    
                            if 'tag-list' in recording and len(recording['tag-list']) > 0:
                                final_genre = recording['tag-list'][0].get('name', final_genre)
                except Exception as e:
                    print(f"AcoustID/MusicBrainz fallback para {temp_filepath}. Error: {e}")

                # Etiquetado con Mutagen
                try:
                    audio = ID3(temp_filepath)
                except ID3NoHeaderError:
                    audio = ID3()
                    
                audio.add(TIT2(encoding=3, text=final_title))
                audio.add(TPE1(encoding=3, text=final_artist))
                if final_album:
                    audio.add(TALB(encoding=3, text=final_album))
                if final_year and final_year != 'None':
                    audio.add(TDRC(encoding=3, text=final_year))
                if final_genre and final_genre != 'None':
                    audio.add(TCON(encoding=3, text=final_genre))
                if final_track_number and final_track_number != 'None':
                    audio.add(TRCK(encoding=3, text=final_track_number))
                if final_album_artist and final_album_artist != 'None':
                    audio.add(TPE2(encoding=3, text=final_album_artist))
                
                audio.save(temp_filepath, v2_version=3)

                # Renombramiento a formato "Artista - Titulo.mp3"
                final_filename = f"{sanitize(final_artist)} - {sanitize(final_title)}.mp3"
                final_filepath = os.path.join(output_dir, final_filename)
                
                # Evitar chocar si final_filepath es igual a temp_filepath
                if temp_filepath != final_filepath:
                    if os.path.exists(final_filepath):
                        os.remove(final_filepath)
                    os.rename(temp_filepath, final_filepath)
                
                # Opcional: limpiar el info.json para mantener todo ordenado
                if os.path.exists(info_json_path):
                    os.remove(info_json_path)

            return {"status": "success", "message": "Descarga procesada con Audio Fingerprinting exitosamente."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)