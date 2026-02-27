import React from 'react';
import { Loader2, Search } from 'lucide-react';

interface SearchFormProps {
    url: string;
    setUrl: (url: string) => void;
    fetchInfo: () => void;
    loadingInfo: boolean;
    loadingDownload: boolean;
}

export function SearchForm({ url, setUrl, fetchInfo, loadingInfo, loadingDownload }: SearchFormProps) {
    return (
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
    );
}
