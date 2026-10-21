import { useEffect, useId, useRef, useState } from 'react';
import { scaleBand, scaleLinear, max } from 'd3';
import { ChartColumn, Table2, ChevronDown, ChevronUp } from 'lucide-react';
import type { MetadataResponse, Overview } from './types';
import { IconButton, age, number } from './ui';

function useWidth() {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(520);
  useEffect(() => {
    if (!ref.current) return;
    const observer = new ResizeObserver(entries => setWidth(Math.max(240, Math.floor(entries[0].contentRect.width))));
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);
  return { ref, width };
}

function DisplayMode({ title, table, setTable }: { title: string; table: boolean; setTable: (value: boolean) => void }) {
  return <div className="segmented" aria-label={`${title} display`}>
    <IconButton label={`Show chart for ${title}`} aria-pressed={!table} onClick={() => setTable(false)}><ChartColumn size={16} /></IconButton>
    <IconButton label={`Show table for ${title}`} aria-pressed={table} onClick={() => setTable(true)}><Table2 size={16} /></IconButton>
  </div>;
}

function CountTable({ title, heading, rows }: { title: string; heading: string; rows: [string, number][] }) {
  return <div className="table-scroll chart-table" tabIndex={0} role="region" aria-label={`${title} values`}>
    <table><caption className="sr-only">{title}: exact report counts for the displayed selection</caption>
      <thead><tr><th scope="col">{heading}</th><th scope="col" className="numeric">Reports</th></tr></thead>
      <tbody>{rows.map(([label, count]) => <tr key={label}><th scope="row">{label}</th><td className="numeric">{number(count)}</td></tr>)}</tbody>
    </table>
  </div>;
}

export function AnnualChart({ overview }: { overview: Overview }) {
  const [table, setTable] = useState(false);
  const { ref, width } = useWidth();
  const id = useId();
  const height = 238, left = 44, bottom = 208;
  const rows = overview.yearCounts as [number, number][];
  const x = scaleBand<number>().domain(rows.map(([year]) => year)).range([left, width - 16]).padding(.22);
  const y = scaleLinear().domain([0, max(rows, row => row[1]) || 1]).nice().range([bottom, 16]);
  const interval = width < 450 ? 6 : 4;
  const labelYears = rows.filter((_, index) => index % interval === 0).map(row => row[0]);
  const finalYear = rows.at(-1)?.[0];
  if (finalYear !== undefined && !labelYears.includes(finalYear)) {
    if (labelYears.length > 1 && finalYear - labelYears.at(-1)! < interval / 2) labelYears.pop();
    labelYears.push(finalYear);
  }
  const partial = rows.some(([year]) => year === 2026);
  return <section className="plot" aria-labelledby={id + '-heading'} data-chart="annual">
    <header className="plot-header"><div><h3 id={id + '-heading'}>Reports by year</h3><p>Actual event year</p></div><DisplayMode title="annual reports" table={table} setTable={setTable} /></header>
    <div ref={ref} className="plot-body">
      {table ? <CountTable title="Annual reports" heading="Event year" rows={rows.map(([year, count]) => [year === 2026 ? '2026 (January 1 only)' : String(year), count])} /> :
        <svg width={width} height={height} role="img" aria-labelledby={`${id}-title ${id}-description`}>
          <title id={id + '-title'}>Reports by actual event year</title><desc id={id + '-description'}>Counts for every year in the displayed selection, including zero-count years. Exact values are in the table view.</desc>
          {y.ticks(4).filter(Number.isInteger).map(tick => <g key={tick}><line className="gridline" x1={left} x2={width - 16} y1={y(tick)} y2={y(tick)} /><text className="tick" x={left - 8} y={y(tick) + 4} textAnchor="end">{tick >= 1000 ? `${number(tick / 1000)}k` : tick}</text></g>)}
          {rows.map(([year, count]) => <rect className="data-mark" key={year} x={x(year)} y={y(count)} width={x.bandwidth()} height={bottom - y(count)} fill={year === 2026 ? 'var(--partial)' : 'var(--teal)'}><title>{year}: {number(count)} reports{year === 2026 ? '; January 1 only' : ''}</title></rect>)}
          {labelYears.map(year => <text className="tick" key={year} x={(x(year) ?? 0) + x.bandwidth() / 2} y={bottom + 22} textAnchor="middle">{year}{year === 2026 ? '*' : ''}</text>)}
        </svg>}
    </div>
    {partial && <p className="plot-note partial-note">* 2026 covers January 1 only, not a full year.</p>}
    {overview.selectedCount === 0 && <p className="empty-note">No reports match this selection.</p>}
  </section>;
}

export function AgeChart({ overview }: { overview: Overview }) {
  const [table, setTable] = useState(false);
  const { ref, width } = useWidth();
  const id = useId();
  const rows = overview.ageHistogram as [number, number][];
  const bottom = 208, height = 238, left = 44;
  const x = scaleLinear().domain([0, 126]).range([left, width - 16]);
  const y = scaleLinear().domain([0, max(rows, row => row[1]) || 1]).nice().range([bottom, 16]);
  return <section className="plot" aria-labelledby={id + '-heading'} data-chart="ages">
    <header className="plot-header"><div><h3 id={id + '-heading'}>Age distribution</h3><p>{number(overview.validAgeCount)} reports with a valid age</p></div><DisplayMode title="age distribution" table={table} setTable={setTable} /></header>
    <div ref={ref} className="plot-body">
      {table ? <CountTable title="Age distribution" heading="Age in years" rows={rows.map(([bin, count]) => [bin === 125 ? 'Exactly 125' : `${bin} to less than ${bin + 1}`, count])} /> :
        <svg width={width} height={height} role="img" aria-labelledby={`${id}-title ${id}-description`}>
          <title id={id + '-title'}>Report ages in one-year bins</title><desc id={id + '-description'}>Fractional ages remain in their original one-year bins. Age 125 has its own bin. Missing or invalid ages are excluded from age calculations, not report totals.</desc>
          {y.ticks(4).filter(Number.isInteger).map(tick => <g key={tick}><line className="gridline" x1={left} x2={width - 16} y1={y(tick)} y2={y(tick)} /><text className="tick" x={left - 8} y={y(tick) + 4} textAnchor="end">{number(tick)}</text></g>)}
          {rows.map(([bin, count]) => <rect className="data-mark" key={bin} x={x(bin)} y={y(count)} width={Math.max(.5, x(1) - x(0) - .35)} height={bottom - y(count)} fill="var(--coral)"><title>{bin === 125 ? 'Exactly 125' : `${bin} to less than ${bin + 1}`} years: {number(count)} reports</title></rect>)}
          {[0, 25, 50, 75, 100, 125].map(tick => <text className="tick" key={tick} x={x(tick)} y={bottom + 22} textAnchor="middle">{tick}</text>)}
        </svg>}
    </div>
    <p className="plot-note">Age in years. {number(overview.missingAgeCount)} reports have missing or invalid ages.</p>
    {overview.validAgeCount === 0 && <p className="empty-note">No valid ages in this selection. Mean age is not available.</p>}
  </section>;
}

function Ranking({ title, field, rows, metadata, maximum }: {
  title: string; field: 'products' | 'outcomes' | 'reactions'; rows: [string, number][]; metadata: MetadataResponse; maximum: number;
}) {
  const [table, setTable] = useState(false);
  const [all, setAll] = useState(false);
  const id = useId();
  const scale = scaleLinear().domain([0, maximum || 1]).range([0, 100]);
  const label = (term: string) => field === 'products' ? metadata.metadata.termDisplayOverrides.find(item => item.canonical === term)?.displayLabel ?? term : term;
  return <section className={`plot ranking ranking-${field}`} aria-labelledby={id} data-chart={field}>
    <header className="plot-header"><div><h3 id={id}>{title}</h3><p>{table || all ? `Top ${rows.length}` : `Top ${Math.min(10, rows.length)}`} by report mentions</p></div><DisplayMode title={title.toLowerCase()} table={table} setTable={setTable} /></header>
    {table ? <CountTable title={title} heading="Canonical term" rows={rows.map(([term, count]) => [label(term), count])} /> :
      <ol className="ranking-list">{(all ? rows : rows.slice(0, 10)).map(([term, count]) => <li key={term}>
        <div className="ranking-label"><span title={term}>{label(term)}</span><strong>{number(count)}</strong></div>
        <svg width="100%" height="7" role="img" aria-label={`${label(term)}: ${number(count)} report mentions`} preserveAspectRatio="none" viewBox="0 0 100 7"><rect className="data-mark" width={scale(count)} height="7" fill={`var(--${field})`} /></svg>
      </li>)}</ol>}
    {rows.length === 0 && <p className="empty-note">No matching terms.</p>}
    {!table && rows.length > 10 && <button className="text-button" onClick={() => setAll(!all)}>{all ? <ChevronUp size={16} /> : <ChevronDown size={16} />}{all ? 'Top 10' : `All ${rows.length}`}</button>}
  </section>;
}

export function OverviewCharts({ overview, metadata }: { overview: Overview; metadata: MetadataResponse }) {
  const rankingMaximum = max(Object.values(overview.rankings).flat(), row => row[1]) ?? 0;
  return <>
    <dl className="metrics" aria-label="Displayed selection totals">
      <div><dt>Selected reports</dt><dd data-testid="selected-count">{number(overview.selectedCount)}</dd></div>
      <div><dt>Valid ages</dt><dd>{number(overview.validAgeCount)}</dd></div>
      <div><dt>Missing / invalid ages</dt><dd>{number(overview.missingAgeCount)}</dd></div>
      <div><dt>Mean age</dt><dd className="mean-age">{overview.ageMeans.total === null ? 'Not available' : <>{number(overview.ageMeans.total)}<small> years</small></>}</dd></div>
    </dl>
    <div className="distribution-grid"><AnnualChart overview={overview} /><AgeChart overview={overview} /></div>
    <section className="gender-context" aria-label="Gender and age coverage"><h3>Reported gender</h3><dl>{overview.genderCounts.map(([gender, count]) => <div key={gender}><dt>{gender}</dt><dd>{number(count)} reports</dd></div>)}</dl>
      <p>Mean age: female {age(overview.ageMeans.female)}; male {age(overview.ageMeans.male)}.</p>
    </section>
    <section className="ranking-section" aria-labelledby="rankings-heading"><header className="section-header"><h2 id="rankings-heading">Report mentions</h2><p>One count per canonical term per report. Terms overlap; counts are not additive or causal pairs.</p>{rankingMaximum > 0 && <p>Shared count scale: 0-{number(rankingMaximum)} reports.</p>}</header>
      <div className="ranking-grid"><Ranking title="Suspect products" field="products" rows={overview.rankings.products as [string, number][]} metadata={metadata} maximum={rankingMaximum} /><Ranking title="Outcomes" field="outcomes" rows={overview.rankings.outcomes as [string, number][]} metadata={metadata} maximum={rankingMaximum} /><Ranking title="Reactions" field="reactions" rows={overview.rankings.reactions as [string, number][]} metadata={metadata} maximum={rankingMaximum} /></div>
    </section>
  </>;
}
