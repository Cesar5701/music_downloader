import re

def sanitize_filename(name: str) -> str:
    """Elimina caracteres inválidos para nombres de archivo en Windows/Linux."""
    return re.sub(r'[\\/*?:"<>|]', "", str(name))

def clean_track_title(title: str) -> str:
    """Limpia etiquetas basura de YouTube (Official Video, Audio, etc)."""
    if not title: return title
    cleaned = re.sub(r'(?i)[\(\[]\s*(official\s*(video|audio|music\s*video|lyric\s*video)?|lyric\s*video|audio|video|lyrics?)\s*[\)\]]', '', str(title))
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'\s+[-|]+\s*$', '', cleaned).strip()
    return cleaned
