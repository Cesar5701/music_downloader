import React from 'react';
import { Music } from 'lucide-react';

export function Header() {
    return (
        <header className="flex items-center gap-3 mb-12">
            <div className="bg-red-600 p-2 rounded-lg">
                <Music size={32} className="text-white" />
            </div>
            <h1 className="text-3xl font-bold tracking-tight">MusicDownloader <span className="text-red-500">Pro</span></h1>
        </header>
    );
}
