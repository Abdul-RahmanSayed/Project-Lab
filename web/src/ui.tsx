import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { CircleAlert, LoaderCircle } from 'lucide-react';
import type { Filters } from './types';

export const number = (value: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
export const age = (value: number | null) => value === null ? 'Not available' : `${number(value)} years`;
export const date = (value: string) => new Intl.DateTimeFormat('en-US', {
  timeZone: 'UTC', year: 'numeric', month: 'short', day: 'numeric',
}).format(new Date(value));

export function IconButton({ label, children, className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string; children: ReactNode;
}) {
  return <button type="button" className={`icon-button ${className}`} title={label} aria-label={label} {...props}>{children}</button>;
}

export function Notice({ children, loading = false, alert = false, action }: {
  children: ReactNode; loading?: boolean; alert?: boolean; action?: ReactNode;
}) {
  return <div className={`notice ${alert ? 'notice-alert' : ''}`} role={alert ? 'alert' : 'status'}>
    {loading ? <LoaderCircle className="spin" size={18} aria-hidden /> : <CircleAlert size={18} aria-hidden />}
    <div>{children}</div>{action && <div className="notice-action">{action}</div>}
  </div>;
}

export function SelectionLabel({ filters }: { filters: Filters }) {
  return <span className="selection-label"><span>{filters.startYear}-{filters.endYear}</span>
    <span>{filters.productFilter === null ? 'All suspect products' : <>Raw product contains <code>{filters.productFilter}</code></>}</span>
  </span>;
}
