import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp

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
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "id": info.get('id')
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/download")
def download_audio(req: DownloadRequest):
    # Carpeta de descargas
    output_dir = "../media/downloads"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'format': 'bestaudio/best',
        # Extrae primero metadatos de YT Music oficiales para evitar títulos basura
        'parse_metadata': 'title:%(artist)s - %(title)s',
        # Nombre de archivo limpio: Artista - Título.mp3
        'outtmpl': f'{output_dir}/%(artist,uploader)s - %(track,title)s.%(ext)s',
        'writethumbnail': True,
        'quiet': False,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320', # Aumentado a 320kbps para mejor calidad
            },
            {
                # CRÍTICO: Convierte la miniatura webp de YouTube a jpg
                'key': 'FFmpegThumbnailsConvertor',
                'format': 'jpg',
            },
            {
                'key': 'EmbedThumbnail',
            },
            {
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            },
        ],
    }

    # Si el frontend envía metadatos manuales, los inyectamos en FFmpeg
    ffmpeg_args = []
    if req.title:
        ffmpeg_args.extend(['-metadata', f'title={req.title}'])
    if req.artist:
        ffmpeg_args.extend(['-metadata', f'artist={req.artist}'])
    if req.album:
        ffmpeg_args.extend(['-metadata', f'album={req.album}'])
        
    if ffmpeg_args:
        ydl_opts['postprocessor_args'] = ffmpeg_args

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([req.url])
            return {"status": "success", "message": "Descarga completada con metadatos y portada correctos."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)