import React, { useState } from 'react';
import { Download, Music, Search, Disc, User, Loader2, CheckCircle, XCircle, Info } from 'lucide-react';

type Status = {
    text: string;
    type: 'success' | 'error' | 'info';
};

export default function App() {
    const [url, setUrl] = useState('');
    const [loadingInfo, setLoadingInfo] = useState(false);
    const [loadingDownload, setLoadingDownload] = useState(false);
    const [info, setInfo] = useState<any>(null);
    const [status, setStatus] = useState<Status | null>(null);
    const [selectedTracks, setSelectedTracks] = useState<string[]>([]);

    const fetchInfo = async () => {
        if (!url) return;
        setLoadingInfo(true);
        setStatus(null);
        setInfo(null);
        try {
            const res = await fetch(`http://localhost:8000/info?url=${encodeURIComponent(url)}`);
            const data = await res.json();
            if (!res.ok) {
                setStatus({ text: data.detail || "Error al obtener información", type: 'error' });
            } else {
                setInfo(data);
                if (data.is_playlist) {
                    setSelectedTracks(data.tracks.map((t: any) => t.url));
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
        if (info.is_playlist && selectedTracks.length === 0) {
            alert('Por favor, selecciona al menos una pista a descargar.');
            return;
        }

        setLoadingDownload(true);
        setStatus({ text: 'Procesando descarga y metadatos...', type: 'info' });
        try {
            const res = await fetch('http://localhost:8000/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url,
                    urls: info.is_playlist ? selectedTracks : [],
                    title: info.title,
                    artist: info.artist,
                    album: info.album
                })
            });
            const data = await res.json();
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
                <header className="flex items-center gap-3 mb-12">
                    <div className="bg-red-600 p-2 rounded-lg">
                        <Music size={32} className="text-white" />
                    </div>
                    <h1 className="text-3xl font-bold tracking-tight">MusicDownloader <span className="text-red-500">Pro</span></h1>
                </header>

                <div className="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 shadow-xl mb-8">
                    <label className="block text-sm font-medium text-zinc-400 mb-2">Pega la URL de YouTube</label>
                    <div className="flex gap-3">
                        <input
                            className="flex-1 bg-zinc-800 border-none rounded-xl px-4 py-3 focus:ring-2 focus:ring-red-500 transition-all outline-none"
                            placeholder="https://www.youtube.com/watch?v=..."
                            value={url}
                            onChange={(e) => setUrl(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && fetchInfo()}
                        />
                        <button
                            onClick={fetchInfo}
                            disabled={loadingInfo || loadingDownload}
                            className="bg-zinc-100 text-zinc-900 px-6 py-3 rounded-xl font-bold hover:bg-white flex items-center gap-2 disabled:opacity-50"
                        >
                            {loadingInfo ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
                            Analizar
                        </button>
                    </div>
                </div>

                {info && (
                    <div className="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {info.is_playlist ? (
                            <div className="p-6">
                                <h2 className="text-2xl font-bold mb-2">{info.title}</h2>
                                <p className="text-zinc-400 mb-6">{info.artist}</p>

                                <div className="flex gap-4 mb-4">
                                    <button
                                        onClick={() => setSelectedTracks(info.tracks.map((t: any) => t.url))}
                                        className="text-sm bg-zinc-800 hover:bg-zinc-700 px-4 py-2 rounded-lg font-medium transition-colors"
                                    >
                                        Seleccionar todas
                                    </button>
                                    <button
                                        onClick={() => setSelectedTracks([])}
                                        className="text-sm bg-zinc-800 hover:bg-zinc-700 px-4 py-2 rounded-lg font-medium transition-colors"
                                    >
                                        Deseleccionar todas
                                    </button>
                                </div>
                                <div className="max-h-96 overflow-y-auto pr-2 space-y-2 mb-8 scrollbar-thin scrollbar-thumb-zinc-700">
                                    {info.tracks.map((track: any, i: number) => (
                                        <label key={i} className="flex items-center gap-4 bg-zinc-800/50 hover:bg-zinc-800 p-3 rounded-xl cursor-pointer transition-colors">
                                            <input
                                                type="checkbox"
                                                checked={selectedTracks.includes(track.url)}
                                                onChange={(e) => {
                                                    if (e.target.checked) {
                                                        setSelectedTracks([...selectedTracks, track.url]);
                                                    } else {
                                                        setSelectedTracks(selectedTracks.filter(url => url !== track.url));
                                                    }
                                                }}
                                                className="w-5 h-5 rounded border-zinc-600 text-red-600 focus:ring-red-500 bg-zinc-900"
                                            />
                                            <span className="flex-1 truncate text-sm font-medium">{track.title}</span>
                                        </label>
                                    ))}
                                </div>

                                <div className="flex items-center justify-end">
                                    <button
                                        onClick={handleDownload}
                                        disabled={loadingDownload || loadingInfo || selectedTracks.length === 0}
                                        className="bg-red-600 hover:bg-red-500 text-white px-8 py-3 rounded-xl font-bold flex items-center gap-2 transition-colors disabled:opacity-50"
                                    >
                                        {loadingDownload ? <Loader2 className="animate-spin" size={20} /> : <Download size={20} />}
                                        Descargar ({selectedTracks.length})
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="md:flex">
                                <div className="md:w-1/3">
                                    {info.thumbnail ? (
                                        <img src={info.thumbnail} alt="Cover" className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full bg-zinc-800 flex items-center justify-center">
                                            <Music size={48} className="text-zinc-600" />
                                        </div>
                                    )}
                                </div>
                                <div className="p-6 md:w-2/3">
                                    <h2 className="text-xl font-bold mb-4">Metadatos de la Pista</h2>

                                    <div className="space-y-4">
                                        <div className="flex items-center gap-3 bg-zinc-800/50 p-3 rounded-lg">
                                            <Disc className="text-zinc-500" size={18} />
                                            <input
                                                className="bg-transparent border-none w-full focus:ring-0 text-sm"
                                                value={info.title || ''}
                                                onChange={(e) => setInfo({ ...info, title: e.target.value })}
                                                placeholder="Título de la canción"
                                            />
                                        </div>
                                        <div className="flex items-center gap-3 bg-zinc-800/50 p-3 rounded-lg">
                                            <User className="text-zinc-500" size={18} />
                                            <input
                                                className="bg-transparent border-none w-full focus:ring-0 text-sm"
                                                value={info.artist || ''}
                                                onChange={(e) => setInfo({ ...info, artist: e.target.value })}
                                                placeholder="Artista"
                                            />
                                        </div>
                                        <div className="flex items-center gap-3 bg-zinc-800/50 p-3 rounded-lg">
                                            <Disc className="text-zinc-500" size={18} />
                                            <input
                                                className="bg-transparent border-none w-full focus:ring-0 text-sm"
                                                value={info.album || ''}
                                                onChange={(e) => setInfo({ ...info, album: e.target.value })}
                                                placeholder="Álbum"
                                            />
                                        </div>
                                    </div>

                                    <div className="mt-8 flex items-center justify-between">
                                        <div className="text-xs text-zinc-500 uppercase tracking-widest font-bold">
                                            Formato: MP3 320kbps
                                        </div>
                                        <button
                                            onClick={handleDownload}
                                            disabled={loadingDownload || loadingInfo}
                                            className="bg-red-600 hover:bg-red-500 text-white px-8 py-3 rounded-xl font-bold flex items-center gap-2 transition-colors disabled:opacity-50"
                                        >
                                            {loadingDownload ? <Loader2 className="animate-spin" size={20} /> : <Download size={20} />}
                                            Descargar ahora
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {status && (
                    <div className={`mt-6 p-4 rounded-xl flex items-center gap-2 border ${status.type === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-500' :
                        status.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-500' :
                            'bg-blue-500/10 border-blue-500/20 text-blue-500'
                        }`}>
                        {status.type === 'error' && <XCircle size={20} />}
                        {status.type === 'success' && <CheckCircle size={20} />}
                        {status.type === 'info' && <Info size={20} />}
                        {status.text}
                    </div>
                )}
            </div>
        </div>
    );
}