import os
import json
import yt_dlp
import acoustid
import musicbrainzngs
from fastapi import APIRouter, HTTPException
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TCON, TDRC, TRCK, TENC, COMM, TPUB, TCOP, TCOM, TLAN, TSRC, TPOS, TMED, TDOR, TXXX, TSOP, TSO2, ID3NoHeaderError

from models.schemas import DownloadRequest
from utils.helpers import sanitize_filename, clean_track_title
from utils.logger import download_logger, metadata_logger, connection_logger
from services.metadata import extract_musicbrainz_tags

router = APIRouter()

download_progress = {}

@router.get("/")
def read_root():
    return {
        "message": "Backend de MusicDownloader Pro activo.",
        "status": "success",
        "documentation": "/docs"
    }

@router.get("/progress")
def get_progress():
    return download_progress

@router.get("/info")
def get_info(url: str):
    ydl_opts = {'quiet': True, 'extract_flat': True, 'http_headers': {'User-Agent': 'Mozilla/5.0'}}
    
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

@router.post("/download")
def download_audio(req: DownloadRequest):
    output_dir = "media/downloads"
    os.makedirs(output_dir, exist_ok=True)
    ACOUSTID_API_KEY = os.getenv('ACOUSTID_API_KEY', '')

    def update_progress(d):
        video_id = d.get('info_dict', {}).get('id')
        if not video_id: return
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            download_progress[video_id] = {
                'status': 'downloading',
                'percent': (downloaded / total * 100) if total else 0,
                'speed': d.get('speed', 0)
            }
        elif d['status'] == 'finished':
            download_progress[video_id] = {'status': 'processing', 'percent': 100, 'speed': 0}

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
        'writethumbnail': True,
        'writeinfojson': True,
        'quiet': False,
        'progress_hooks': [update_progress],
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'},
            {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'},
            {'key': 'EmbedThumbnail'}
        ],
        'postprocessor_args': {'thumbnailsconvertor': ['-vf', 'crop=min(in_w\,in_h):min(in_w\,in_h)']}
    }

    try:
        urls_to_process = req.urls if req.urls else [req.url]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for current_url in urls_to_process:
                download_logger.info(f"INICIANDO DESCARGA: {current_url}")
                info = ydl.extract_info(current_url, download=True)
                entries = info.get('entries', [info]) if 'entries' in info else [info]
                
                for entry in entries:
                    if not entry: continue
                    video_id = entry.get('id')
                    temp_filepath = os.path.join(output_dir, f"{video_id}.mp3")
                    info_json_path = os.path.join(output_dir, f"{video_id}.info.json")
                    
                    if not os.path.exists(temp_filepath):
                        download_logger.error(f"El archivo {temp_filepath} no se generó.")
                        continue
                    
                    metadata_logger.info(f"PROCESANDO METADATOS: {video_id}")
                    
                    meta = {
                        'title': clean_track_title(req.title or entry.get('title', 'Unknown Title')),
                        'artist': req.artist or entry.get('artist', entry.get('uploader', 'Unknown Artist')),
                        'album': req.album or entry.get('album', ''),
                        'year': str(entry.get('release_date', ''))[:4] or str(entry.get('release_year', '')),
                        'genre': entry.get('genre', ''),
                        'track_number': str(entry.get('track_number', '')),
                        'album_artist': entry.get('album_artist', '')
                    }

                    if os.path.exists(info_json_path):
                        try:
                            with open(info_json_path, 'r', encoding='utf-8') as f:
                                track_info = json.load(f)
                                meta['title'] = clean_track_title(track_info.get('title', meta['title']))
                                meta['artist'] = track_info.get('artist', track_info.get('uploader', meta['artist']))
                                meta['album'] = track_info.get('album', meta['album'])
                        except Exception as e:
                            metadata_logger.warning(f"No se pudo leer info.json: {e}")

                    matched = False
                    if ACOUSTID_API_KEY:
                        try:
                            connection_logger.info("Consultando AcoustID...")
                            results = acoustid.match(ACOUSTID_API_KEY, temp_filepath)
                            for score, recording_id, mb_title, mb_artist in results:
                                metadata_logger.info(f"AcoustID Match! Score: {score}, RecID: {recording_id}")
                                matched = True
                                mb_data = musicbrainzngs.get_recording_by_id(recording_id, includes=['releases', 'artists', 'tags', 'isrcs'])
                                mb_tags = extract_musicbrainz_tags(mb_data.get('recording', {}), meta['title'], meta['artist'])
                                mb_tags['acoustid_id'] = recording_id
                                meta.update(mb_tags)
                                break 
                        except acoustid.NoBackendError:
                            connection_logger.error("Chromaprint no está instalado en el sistema.")
                        except Exception as e:
                            connection_logger.error(f"Error en AcoustID: {e}")

                    if not matched:
                        try:
                            connection_logger.info("Fallback a Búsqueda de Texto en MusicBrainz...")
                            query = f'recording:({meta["title"]})'
                            if meta["artist"] and meta["artist"] != "Unknown Artist":
                                query += f' artist:({meta["artist"]})'
                            
                            mb_search = musicbrainzngs.search_recordings(query=query, limit=1)
                            if mb_search.get('recording-list'):
                                metadata_logger.info("MusicBrainz Texto Match!")
                                rec_info = mb_search['recording-list'][0]
                                try:
                                    mb_rec = musicbrainzngs.get_recording_by_id(rec_info['id'], includes=['releases', 'artists', 'tags', 'isrcs'])
                                    recording_data = mb_rec.get('recording', rec_info)
                                except:
                                    recording_data = rec_info
                                    
                                mb_tags = extract_musicbrainz_tags(recording_data, meta['title'], meta['artist'])
                                meta.update(mb_tags)
                        except Exception as e:
                            connection_logger.error(f"Error en búsqueda de texto MB: {e}")

                    try:
                        audio = ID3(temp_filepath)
                    except ID3NoHeaderError:
                        audio = ID3()
                        
                    audio.add(TIT2(encoding=3, text=meta.get('title', '')))
                    audio.add(TPE1(encoding=3, text=meta.get('artist', '')))
                    
                    if meta.get('album'): audio.add(TALB(encoding=3, text=meta['album']))
                    if meta.get('genre'): audio.add(TCON(encoding=3, text=meta['genre']))
                    
                    date_val = meta.get('date') or meta.get('year')
                    if date_val:
                        audio.add(TDRC(encoding=3, text=date_val))
                        audio.add(TDOR(encoding=3, text=date_val))

                    track_str = meta.get('track_number', '')
                    if track_str and meta.get('total_tracks'):
                        track_str = f"{track_str}/{meta['total_tracks']}"
                    if track_str: audio.add(TRCK(encoding=3, text=track_str))

                    disc_str = meta.get('disc_number', '')
                    if disc_str and meta.get('total_discs'):
                        disc_str = f"{disc_str}/{meta['total_discs']}"
                    if disc_str: audio.add(TPOS(encoding=3, text=disc_str))

                    if meta.get('media'): audio.add(TMED(encoding=3, text=meta['media']))
                    if meta.get('album_artist'): audio.add(TPE2(encoding=3, text=meta['album_artist']))
                    if meta.get('isrc'): audio.add(TSRC(encoding=3, text=meta['isrc']))
                    if meta.get('language'): audio.add(TLAN(encoding=3, text=meta['language']))

                    if meta.get('publisher'):
                        audio.add(TPUB(encoding=3, text=meta['publisher']))
                        copy_text = f"{meta.get('year', '')} {meta['publisher']}".strip()
                        audio.add(TCOP(encoding=3, text=copy_text))

                    if meta.get('artist_sort_order'): audio.add(TSOP(encoding=3, text=meta['artist_sort_order']))
                    if meta.get('album_artist_sort_order'): audio.add(TSO2(encoding=3, text=meta['album_artist_sort_order']))

                    def add_txxx(desc, key):
                        val = meta.get(key)
                        if val: audio.add(TXXX(encoding=3, desc=desc, text=str(val)))
                            
                    def add_txxx_list(desc, key):
                        val = meta.get(key)
                        if val and isinstance(val, list):
                            audio.add(TXXX(encoding=3, desc=desc, text=val))
                            
                    add_txxx_list('ARTISTS', 'artists')
                    add_txxx('BARCODE', 'barcode')
                    add_txxx('Acoustid Id', 'acoustid_id')
                    add_txxx('MusicBrainz Artist Id', 'mb_artist_id')
                    add_txxx('MusicBrainz Recording Id', 'mb_recording_id')
                    add_txxx('MusicBrainz Release Artist Id', 'mb_release_artist_id')
                    add_txxx('MusicBrainz Release Group Id', 'mb_release_group_id')
                    add_txxx('MusicBrainz Release Id', 'mb_release_id')
                    add_txxx('MusicBrainz Release Track Id', 'mb_track_id')
                    add_txxx('MusicBrainz Album Release Country', 'country')
                    add_txxx('MusicBrainz Album Status', 'status')
                    add_txxx('MusicBrainz Album Type', 'type')
                    add_txxx('Script', 'script')
                    
                    audio.save(temp_filepath, v2_version=3)

                    final_filename = f"{sanitize_filename(meta.get('artist', 'Unknown'))} - {sanitize_filename(meta.get('title', 'Unknown'))}.mp3"
                    final_filepath = os.path.join(output_dir, final_filename)
                    
                    if temp_filepath != final_filepath:
                        if os.path.exists(final_filepath):
                            os.remove(final_filepath)
                        os.rename(temp_filepath, final_filepath)
                    
                    if os.path.exists(info_json_path):
                        os.remove(info_json_path)
                    
                    download_progress[video_id] = {'status': 'completed', 'percent': 100, 'speed': 0}

        return {"status": "success", "message": "Descargas procesadas exitosamente."}
    except Exception as e:
        download_logger.error(f"Error crítico en el endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
