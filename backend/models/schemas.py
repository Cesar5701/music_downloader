from pydantic import BaseModel
from typing import Optional, List

class DownloadRequest(BaseModel):
    url: str
    urls: Optional[List[str]] = []
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
