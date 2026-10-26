import { StrictMode, Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { Header } from './Header';
import { initializeTheme } from './theme';
import './styles.css';

class Boundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(_error: Error, _info: ErrorInfo) { /* Do not log report data or raw selections. */ }
  render() {
    return this.state.failed ? <><Header /><main><h1>FDA Explorer</h1><p role="alert">The view could not be displayed. No unverified replacement data is shown.</p><button onClick={() => location.reload()}>Reload</button></main></> : this.props.children;
  }
}

initializeTheme();
createRoot(document.getElementById('root')!).render(<StrictMode><Boundary><App /></Boundary></StrictMode>);
