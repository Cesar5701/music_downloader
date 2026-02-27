import React from 'react';
import { Download, Loader2 } from 'lucide-react';
import { DownloadInfo, TrackProgress } from '../types';

interface PlaylistViewProps {
    info: DownloadInfo;
    selectedTracks: string[];
    setSelectedTracks: (tracks: string[]) => void;
    handleDownload: () => void;
    loadingDownload: boolean;
    loadingInfo: boolean;
    progressData: Record<string, TrackProgress>;
    formatSpeed: (speed: number) => string;
}

export function PlaylistView({
    info, selectedTracks, setSelectedTracks, handleDownload,
    loadingDownload, loadingInfo, progressData, formatSpeed
}: PlaylistViewProps) {
    const isAllSelected = info.tracks && selectedTracks.length === info.tracks.length;

    return (
        <div className="p-6">
            <h2 className="text-2xl font-bold mb-2">{info.title}</h2>
            <p className="text-zinc-400 mb-6">{info.artist}</p>

            <div className="flex gap-4 mb-4">
                <button
                    onClick={() => setSelectedTracks(info.tracks?.map(t => t.url) || [])}
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
                {info.tracks?.map((track, i) => (
                    <label key={i} className="flex items-center gap-4 bg-zinc-800/50 hover:bg-zinc-800 p-3 rounded-xl cursor-pointer transition-colors">
                        <input
                            type="checkbox"
                            checked={selectedTracks.includes(track.url)}
                            onChange={(e) => {
                                if (e.target.checked) setSelectedTracks([...selectedTracks, track.url]);
                                else setSelectedTracks(selectedTracks.filter(url => url !== track.url));
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
            {loadingDownload && (
                <div className="mt-4 space-y-3">
                    {info.tracks?.filter(t => selectedTracks.includes(t.url)).map(t => {
                        const prog = progressData[t.id];
                        if (!prog) return null;
                        const isProcessing = prog.status === 'processing';
                        return (
                            <div key={t.id} className="bg-zinc-800 p-3 rounded-xl border border-zinc-700">
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="font-semibold truncate pr-2" title={t.title}>{t.title}</span>
                                    <span className="shrink-0">{isProcessing ? 'Procesando...' : `${prog.percent.toFixed(1)}% - ${formatSpeed(prog.speed)}`}</span>
                                </div>
                                <div className="w-full bg-zinc-900 rounded-full h-2 overflow-hidden">
                                    <div
                                        className={`h-2 rounded-full transition-all duration-300 ${isProcessing ? 'bg-green-500 w-full animate-pulse' : 'bg-red-500'}`}
                                        style={{ width: `${isProcessing ? 100 : prog.percent}%` }}
                                    ></div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
