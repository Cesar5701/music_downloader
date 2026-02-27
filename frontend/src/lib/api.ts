export const fetchInfoApi = async (url: string) => {
    const res = await fetch(`http://localhost:8000/info?url=${encodeURIComponent(url)}`);
    const data = await res.json();
    return { res, data };
};

export const downloadApi = async (body: any) => {
    const res = await fetch('http://localhost:8000/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const data = await res.json();
    return { res, data };
};

export const progressApi = async () => {
    const res = await fetch('http://localhost:8000/progress');
    return await res.json();
};
