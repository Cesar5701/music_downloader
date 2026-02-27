import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { SearchForm } from './components/SearchForm';
import { PlaylistView } from './components/PlaylistView';
import { TrackView } from './components/TrackView';
import { StatusBar } from './components/StatusBar';
import { Status, TrackProgress, DownloadInfo } from './types';
import { fetchInfoApi, downloadApi, progressApi } from './lib/api';

export default function App() {
    const [url, setUrl] = useState('');
    const [loadingInfo, setLoadingInfo] = useState(false);
    const [loadingDownload, setLoadingDownload] = useState(false);
    const [info, setInfo] = useState<DownloadInfo | null>(null);
    const [status, setStatus] = useState<Status | null>(null);
    const [selectedTracks, setSelectedTracks] = useState<string[]>([]);
    const [progressData, setProgressData] = useState<Record<string, TrackProgress>>({});

    useEffect(() => {
        let interval: any;
        if (loadingDownload) {
            interval = setInterval(async () => {
                try {
                    const data = await progressApi();
                    setProgressData(data);
                } catch (e) { }
            }, 1000);
        } else {
            setProgressData({});
        }
        return () => clearInterval(interval);
    }, [loadingDownload]);

    const formatSpeed = (bytesPerSec: number) => {
        if (!bytesPerSec) return '0 B/s';
        const mb = bytesPerSec / 1024 / 1024;
        if (mb >= 1) return `${mb.toFixed(2)} MB/s`;
        return `${(bytesPerSec / 1024).toFixed(2)} KB/s`;
    };

    const fetchInfo = async () => {
        if (!url) return;
        setLoadingInfo(true);
        setStatus(null);
        setInfo(null);
        try {
            const { res, data } = await fetchInfoApi(url);
            if (!res.ok) {
                setStatus({ text: data.detail || "Error al obtener información", type: 'error' });
            } else {
                setInfo(data);
                if (data.is_playlist) {
                    setSelectedTracks(data.tracks?.map((t: any) => t.url) || []);
                } else {
                    setSelectedTracks([]);
                }
            }
        } catch (err) {
            setStatus({ text: "Error de conexión al obtener información", type: 'error' });
        } finally {
            setLoadingInfo(false);
        }
    };

    const handleDownload = async () => {
        if (info?.is_playlist && selectedTracks.length === 0) {
            alert('Por favor, selecciona al menos una pista a descargar.');
            return;
        }

        setLoadingDownload(true);
        setStatus({ text: 'Procesando descarga y metadatos...', type: 'info' });
        try {
            const body = {
                url,
                urls: info?.is_playlist ? selectedTracks : [],
                title: info?.title,
                artist: info?.artist,
                album: info?.album
            };
            const { res, data } = await downloadApi(body);
            if (res.ok && data.status === 'success') {
                setStatus({ text: '¡Descarga finalizada con éxito!', type: 'success' });
            } else {
                setStatus({ text: data.detail || 'Error en la descarga.', type: 'error' });
            }
        } catch (err) {
            setStatus({ text: 'Error de red en la descarga.', type: 'error' });
        } finally {
            setLoadingDownload(false);
        }
    };

    return (
        <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8 font-sans">
            <div className="max-w-3xl mx-auto">
                <Header />
                <SearchForm
                    url={url}
                    setUrl={setUrl}
                    fetchInfo={fetchInfo}
                    loadingInfo={loadingInfo}
                    loadingDownload={loadingDownload}
                />

                {info && (
                    <div className="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {info.is_playlist ? (
                            <PlaylistView
                                info={info}
                                selectedTracks={selectedTracks}
                                setSelectedTracks={setSelectedTracks}
                                handleDownload={handleDownload}
                                loadingDownload={loadingDownload}
                                loadingInfo={loadingInfo}
                                progressData={progressData}
                                formatSpeed={formatSpeed}
                            />
                        ) : (
                            <TrackView
                                info={info}
                                setInfo={setInfo}
                                handleDownload={handleDownload}
                                loadingDownload={loadingDownload}
                                loadingInfo={loadingInfo}
                                progressData={progressData}
                                formatSpeed={formatSpeed}
                            />
                        )}
                    </div>
                )}

                <StatusBar status={status} />
            </div>
        </div>
    );
}