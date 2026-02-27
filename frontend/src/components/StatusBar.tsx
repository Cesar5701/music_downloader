import React from 'react';
import { CheckCircle, XCircle, Info as InfoIcon } from 'lucide-react';
import { Status } from '../types';

export function StatusBar({ status }: { status: Status | null }) {
    if (!status) return null;
    return (
        <div className={`mt-6 p-4 rounded-xl flex items-center gap-2 border ${status.type === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-500' :
            status.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-500' :
                'bg-blue-500/10 border-blue-500/20 text-blue-500'
            }`}>
            {status.type === 'error' && <XCircle size={20} />}
            {status.type === 'success' && <CheckCircle size={20} />}
            {status.type === 'info' && <InfoIcon size={20} />}
            {status.text}
        </div>
    );
}
