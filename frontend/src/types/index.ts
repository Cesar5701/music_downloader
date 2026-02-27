export interface Status {
    text: string;
    type: 'success' | 'error' | 'info';
}

export interface TrackProgress {
    status: 'downloading' | 'processing' | 'finished';
    percent: number;
    speed: number;
}

export interface TrackInfo {
    id: string;
    title: string;
    url: string;
}

export interface DownloadInfo {
    is_playlist: boolean;
    title?: string;
    artist?: string;
    album?: string;
    thumbnail?: string;
    duration?: number;
    id?: string;
    tracks?: TrackInfo[];
}
