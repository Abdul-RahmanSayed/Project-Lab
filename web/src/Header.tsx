import { Activity, Moon, PanelsTopLeft, Sun } from 'lucide-react';
import { useTheme } from './theme';

export function Header({ status = 'View unavailable', statusClass = 'unavailable' }: {
  status?: string; statusClass?: 'ready' | 'starting' | 'unavailable';
}) {
  const { theme, toggleTheme } = useTheme();
  const label = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
  return <header className="app-header"><div className="header-inner">
    <div className="brand"><a className="brand-home" href="https://abdul-rahmansayed.github.io/" aria-label="Project Lab: back to portfolio" title="Back to portfolio"><PanelsTopLeft size={21} aria-hidden /><span>Project Lab</span></a><span className="brand-divider">/</span><span>FDA Explorer</span></div>
    <div className="header-actions"><span className={`api-status ${statusClass}`}><Activity size={14} aria-hidden />{status}</span><button type="button" className="icon-button theme-toggle" aria-label={label} title={label} onClick={toggleTheme}>{theme === 'dark' ? <Sun size={18} aria-hidden /> : <Moon size={18} aria-hidden />}</button></div>
  </div></header>;
}
