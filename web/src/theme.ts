import { useSyncExternalStore } from 'react';

type Theme = 'dark' | 'light';
const storageKey = 'theme';
const changeEvent = 'portfolio-theme-change';

function currentTheme(): Theme {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
}

function savedTheme(): Theme {
  try { return localStorage.getItem(storageKey) === 'light' ? 'light' : 'dark'; }
  catch { return currentTheme(); }
}

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark');
  document.documentElement.style.colorScheme = theme;
}

export function initializeTheme() { applyTheme(savedTheme()); }

function subscribe(notify: () => void) {
  const synchronize = () => { initializeTheme(); notify(); };
  const storageChanged = (event: StorageEvent) => {
    if (event.key === storageKey || event.key === null) synchronize();
  };
  window.addEventListener(changeEvent, notify);
  window.addEventListener('storage', storageChanged);
  window.addEventListener('pageshow', synchronize);
  return () => {
    window.removeEventListener(changeEvent, notify);
    window.removeEventListener('storage', storageChanged);
    window.removeEventListener('pageshow', synchronize);
  };
}

function toggleTheme() {
  const next = currentTheme() === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  try { localStorage.setItem(storageKey, next); } catch { /* Keep the control usable when storage is unavailable. */ }
  window.dispatchEvent(new Event(changeEvent));
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, currentTheme, () => 'dark' as const);
  return { theme, toggleTheme };
}
