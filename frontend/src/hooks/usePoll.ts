import { useEffect, useState } from "react";

/** Load now and every `intervalMs`; keeps the last good data when a refresh fails. */
export function usePoll<T>(load: () => Promise<T>, intervalMs: number, key = "") {
  const [state, setState] = useState<{ data?: T; error?: string }>({});

  useEffect(() => {
    let alive = true;
    setState({}); // a new key means different data; don't show the old one meanwhile
    const run = () =>
      load().then(
        (data) => alive && setState({ data }),
        (e: Error) => alive && setState((s) => ({ ...s, error: e.message })),
      );
    run();
    const id = setInterval(run, intervalMs);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [intervalMs, key]); // `load` changes identity every render; `key` says when it matters

  return state;
}

/** Follows the system light/dark setting. */
export function useDarkMode() {
  const query = "(prefers-color-scheme: dark)";
  const [dark, setDark] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const onChange = () => setDark(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return dark;
}
