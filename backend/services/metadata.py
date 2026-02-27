import musicbrainzngs
from utils.logger import metadata_logger

def extract_musicbrainz_tags(recording: dict, fallback_title: str, fallback_artist: str) -> dict:
    """Extrae la información de MusicBrainz en un diccionario limpio."""
    tags = {
        'title': recording.get('title', fallback_title),
        'artist': fallback_artist,
        'album': '',
        'album_artist': '',
        'year': '',
        'date': '',
        'genre': '',
        'track_number': '',
        'total_tracks': '',
        'disc_number': '',
        'total_discs': '',
        'media': '',
        'country': '',
        'status': '',
        'type': '',
        'language': 'spa',
        'script': '',
        'publisher': '',
        'isrc': '',
        'mb_artist_id': '',
        'mb_recording_id': recording.get('id', ''),
        'mb_release_artist_id': '',
        'mb_release_group_id': '',
        'mb_release_id': '',
        'mb_track_id': ''
    }

    if 'isrc-list' in recording and recording['isrc-list']:
        isrc_e = recording['isrc-list'][0]
        tags['isrc'] = isrc_e.get('id') if isinstance(isrc_e, dict) else str(isrc_e)
    
    if 'artist-credit' in recording and recording['artist-credit']:
        ac_list = recording['artist-credit']
        artist_names = []
        artist_sort_names = []
        artist_string = ""
        for ac in ac_list:
            if isinstance(ac, dict) and 'artist' in ac:
                a_name = ac['artist'].get('name', '')
                a_sort = ac['artist'].get('sort-name', a_name)
                artist_names.append(a_name)
                artist_sort_names.append(a_sort)
                artist_string += a_name + ac.get('joinphrase', '')
            elif isinstance(ac, str):
                artist_string += ac
        tags['artist'] = artist_string or fallback_artist
        tags['artists'] = artist_names
        tags['artist_sort_order'] = ' '.join(artist_sort_names) if artist_sort_names else ''
        if isinstance(ac_list[0], dict) and 'artist' in ac_list[0]:
            tags['mb_artist_id'] = ac_list[0]['artist'].get('id', '')
        
    if 'release-list' in recording and recording['release-list']:
        release = recording['release-list'][0]
        tags['album'] = release.get('title', '')
        tags['mb_release_id'] = release.get('id', '')
        tags['country'] = release.get('country', '')
        tags['status'] = release.get('status', '')
        tags['barcode'] = release.get('barcode', '')
        if release.get('date'):
            tags['date'] = release.get('date')
            tags['year'] = tags['date'][:4]
        
        if 'release-group' in release:
            tags['mb_release_group_id'] = release['release-group'].get('id', '')
            tags['type'] = release['release-group'].get('primary-type', '')
            
        if 'artist-credit' in release and release['artist-credit']:
            ac_list = release['artist-credit']
            album_artist_names = []
            album_artist_sort_names = []
            album_artist_string = ""
            for ac in ac_list:
                if isinstance(ac, dict) and 'artist' in ac:
                    a_name = ac['artist'].get('name', '')
                    a_sort = ac['artist'].get('sort-name', a_name)
                    album_artist_names.append(a_name)
                    album_artist_sort_names.append(a_sort)
                    album_artist_string += a_name + ac.get('joinphrase', '')
                elif isinstance(ac, str):
                    album_artist_string += ac
            tags['album_artist'] = album_artist_string
            tags['album_artist_sort_order'] = ' '.join(album_artist_sort_names) if album_artist_sort_names else ''
            if isinstance(ac_list[0], dict) and 'artist' in ac_list[0]:
                tags['mb_release_artist_id'] = ac_list[0]['artist'].get('id', '')
            
        try:
            rel_data = musicbrainzngs.get_release_by_id(release['id'], includes=['labels', 'recordings'])
            rel_info = rel_data.get('release', {})
            
            if 'label-info-list' in rel_info and rel_info['label-info-list']:
                tags['publisher'] = rel_info['label-info-list'][0].get('label', {}).get('name', '')
                
            if 'medium-list' in rel_info:
                for medium in rel_info['medium-list']:
                    if 'track-list' in medium:
                        for track in medium['track-list']:
                            if track.get('recording', {}).get('id') == tags['mb_recording_id']:
                                tags['media'] = medium.get('format', '')
                                tags['disc_number'] = medium.get('position', '')
                                tags['total_discs'] = str(rel_info.get('medium-count', ''))
                                tags['total_tracks'] = str(medium.get('track-count', ''))
                                tags['track_number'] = track.get('number', '')
                                tags['mb_track_id'] = track.get('id', '')
                                break
        except Exception as e:
            metadata_logger.warning(f"No se pudo extraer información extendida del release: {e}")

        if 'text-representation' in release:
            tags['language'] = release['text-representation'].get('language', '')
            tags['script'] = release['text-representation'].get('script', '')
            
    if 'tag-list' in recording and recording['tag-list']:
        tags['genre'] = recording['tag-list'][0].get('name', '')
        
    return tags
