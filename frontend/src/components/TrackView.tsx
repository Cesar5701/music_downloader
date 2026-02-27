import React from 'react';
import { Download, Loader2, Music, Disc, User } from 'lucide-react';
import { DownloadInfo, TrackProgress } from '../types';

interface TrackViewProps {
    info: DownloadInfo;
    setInfo: (info: DownloadInfo) => void;
    handleDownload: () => void;
    loadingDownload: boolean;
    loadingInfo: boolean;
    progressData: Record<string, TrackProgress>;
    formatSpeed: (speed: number) => string;
}

export function TrackView({ info, setInfo, handleDownload, loadingDownload, loadingInfo, progressData, formatSpeed }: TrackViewProps) {
    const prog = info.id ? progressData[info.id] : null;

    return (
        <div className="md:flex">
            <div className="md:w-1/3">
                {info.thumbnail ? (
                    <img src={info.thumbnail} alt="Cover" className="w-full h-full object-cover" />
                ) : (
                    <div className="w-full h-full bg-zinc-800 flex items-center justify-center min-h-[250px]">
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

                <div className="mt-8 flex flex-col gap-4">
                    <div className="flex items-center justify-between w-full">
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
                    {loadingDownload && prog && (
                        <div className="bg-zinc-800 p-3 rounded-xl border border-zinc-700 mt-2">
                            <div className="flex justify-between text-xs mb-1">
                                <span className="font-semibold truncate pr-2" title={info.title}>{info.title}</span>
                                <span className="shrink-0">{prog.status === 'processing' ? 'Procesando...' : `${prog.percent.toFixed(1)}% - ${formatSpeed(prog.speed)}`}</span>
                            </div>
                            <div className="w-full bg-zinc-900 rounded-full h-2 overflow-hidden">
                                <div
                                    className={`h-2 rounded-full transition-all duration-300 ${prog.status === 'processing' ? 'bg-green-500 w-full animate-pulse' : 'bg-red-500'}`}
                                    style={{ width: `${prog.status === 'processing' ? 100 : prog.percent}%` }}
                                ></div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
