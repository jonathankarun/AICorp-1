// this opens the actual saved PDF using the token, so the source stays protected
import { useEffect, useState } from 'react';
export function SourcePreview({ token, version, page }: { token: string; version: string; page: string }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);
  async function open() {
    setError('');
    try {
      const response = await fetch(`/api/v1/documents/${version}/pdf`, { headers: { Authorization: 'Bearer ' + token } });
      if (!response.ok) throw new Error('This source is no longer available to you.');
      setUrl(URL.createObjectURL(await response.blob()));
    } catch (e) { setError((e as Error).message); }
  }
  return <div><button type="button" onClick={open}>Open original PDF</button>
    {error && <p role="alert">{error}</p>}
    {url && <><p><a href={url} download="source.pdf">Download original PDF</a></p><button type="button" onClick={() => setUrl('')}>Close PDF</button>
      <iframe title="Original source PDF" src={url + '#page=' + page.replace('page ', '')} style={{ width: '100%', height: 420 }} /></>}
  </div>;
}
