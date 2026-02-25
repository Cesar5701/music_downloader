import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import acoustid
import musicbrainzngs
import mutagen.id3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, ID3NoHeaderError
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

from typing import Optional

class DownloadRequest(BaseModel):
    url: str
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

@app.get("/info")
def get_info(url: str):
    ydl_opts = {'quiet': True, 'noplaylist': True, 'http_headers': {'User-Agent': 'Mozilla/5.0'}}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
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
        'quiet': False,
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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(req.url, download=True)
            video_id = info.get('id')
            temp_filepath = os.path.join(output_dir, f"{video_id}.mp3")
            
            # Datos predeterminados desde el frontend/youtube por si falla la huella
            final_title = req.title or info.get('title', 'Unknown Title')
            final_artist = req.artist or info.get('uploader', 'Unknown Artist')
            final_album = req.album or ''

            # Búsqueda de metadata mediante Audio Fingerprinting y MusicBrainz
            try:
                if ACOUSTID_API_KEY:
                    results = acoustid.match(ACOUSTID_API_KEY, temp_filepath)
                    for score, recording_id, title, artist in results:
                        # Extraer el recording id oficial y enriquecerlo con MusicBrainz
                        mb_data = musicbrainzngs.get_recording_by_id(recording_id, includes=['releases', 'artists'])
                        recording = mb_data.get('recording', {})
                        
                        final_title = recording.get('title', final_title)
                        
                        if 'artist-credit' in recording and len(recording['artist-credit']) > 0:
                            final_artist = recording['artist-credit'][0].get('artist', {}).get('name', final_artist)
                            
                        if 'release-list' in recording and len(recording['release-list']) > 0:
                            final_album = recording['release-list'][0].get('title', final_album)
                        break 
            except Exception as e:
                print(f"AcoustID/MusicBrainz fallback. Usando fallback básico. Error: {e}")

            # Etiquetado con Mutagen
            try:
                audio = ID3(temp_filepath)
            except ID3NoHeaderError:
                audio = ID3()
                
            audio.add(TIT2(encoding=3, text=final_title))
            audio.add(TPE1(encoding=3, text=final_artist))
            if final_album:
                audio.add(TALB(encoding=3, text=final_album))
            
            # Guardamos explícitamente usando ID3v2.3 para compatibilidad
            audio.save(temp_filepath, v2_version=3)

            # Renombramiento a formato "Artista - Titulo.mp3"
            final_filename = f"{sanitize(final_artist)} - {sanitize(final_title)}.mp3"
            final_filepath = os.path.join(output_dir, final_filename)
            
            if os.path.exists(final_filepath):
                os.remove(final_filepath)
            os.rename(temp_filepath, final_filepath)

            return {"status": "success", "message": "Descarga procesada con Audio Fingerprinting exitosamente."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)