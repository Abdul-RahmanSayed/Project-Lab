import { useEffect, useRef, useState } from 'react';

export type RequestState<T> = {
  status: 'idle' | 'loading' | 'success' | 'error';
  data?: T;
  dataKey?: string;
  error?: unknown;
};

export function useRequest<T>(key: string | null, load: (signal: AbortSignal) => Promise<T>, revision = 0) {
  const [state, setState] = useState<RequestState<T>>({ status: 'idle' });
  const generation = useRef(0);
  useEffect(() => {
    const current = ++generation.current;
    const controller = new AbortController();
    if (key === null) {
      setState(previous => ({ ...previous, status: 'idle', error: undefined }));
      return () => { controller.abort(); generation.current++; };
    }
    setState(previous => ({ ...previous, status: 'loading', error: undefined }));
    // Abort saves work; the generation check also rejects late, noncooperative loaders.
    load(controller.signal).then(data => {
      if (!controller.signal.aborted && generation.current === current) {
        setState({ status: 'success', data, dataKey: key });
      }
    }).catch(error => {
      if (!controller.signal.aborted && generation.current === current) {
        setState(previous => ({ ...previous, status: 'error', error }));
      }
    });
    return () => { controller.abort(); generation.current++; };
  }, [key, load, revision]);
  return state;
}
