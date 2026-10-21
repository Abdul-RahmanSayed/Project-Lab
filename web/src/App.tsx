import { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity, Check, ChevronDown, Copy, Database, Filter, Info, PanelsTopLeft, RotateCcw, RotateCw, Search } from 'lucide-react';
import { connect, errorMessage, getOverview } from './api';
import { bundledMetadata, savedOverview } from './contracts';
import { OverviewCharts } from './charts';
import { Reports } from './Reports';
import { defaultView, draftFilters, encodeView, filterKey, parseView, sameFilters } from './selection';
import type { MetadataResponse, Tab, View } from './types';
import { useRequest } from './useRequest';
import { IconButton, Notice, SelectionLabel, date, number } from './ui';

const tabs: { id: Tab; label: string }[] = [{ id: 'overview', label: 'Overview' }, { id: 'reports', label: 'Reports' }, { id: 'source', label: 'Snapshot & methods' }];
const defaults = bundledMetadata.metadata.defaultFilters;

function Source({ metadata, connected }: { metadata: MetadataResponse; connected: boolean }) {
  const value = metadata.metadata;
  return <section className="source-section" aria-labelledby="source-heading">
    <header className="section-header"><h2 id="source-heading">Snapshot & methods</h2><p>{connected ? 'API-checked metadata' : 'Bundled saved metadata'} / never live FDA data</p></header>
    <dl className="source-facts"><div><dt>Source</dt><dd><a href="https://open.fda.gov/apis/food/event/" target="_blank" rel="noreferrer">openFDA food adverse-event reports</a></dd></div><div><dt>Event-date coverage</dt><dd>{date(value.coverageStart)} - {date(value.coverageEnd)}</dd></div><div><dt>Snapshot acquired</dt><dd>{date(metadata.snapshotAcquiredAt)}</dd></div><div><dt>Reports / saved pages</dt><dd>{number(value.reportCount)} / {number(value.pageCount)}</dd></div></dl>
    <section><h3>Selection and counting</h3><ul className="method-list"><li>Year bounds are inclusive and use actual event dates. January 1, 2026 belongs to 2026, despite its final 2025 download window.</li><li>Product searches match a literal substring of raw SUSPECT product names, using Python Unicode casefolding. Spaces and punctuation are preserved; aliases are not substituted into search text.</li><li>Rankings use the existing canonical terms, counting each term once per selected report. With a product search, only matching suspect products enter the product ranking. All reactions and outcomes of selected reports remain eligible.</li><li>Product, reaction and outcome mentions overlap. Summing ranked counts does not produce a number of people or establish a causal pair.</li></ul></section>
    <section><h3>Ages and retained details</h3><ul className="method-list"><li>Existing unit conversions and valid-age rules are preserved, including fractional ages, zero and exactly 125. Missing or invalid ages remain counted reports, but are excluded from means and the age histogram.</li><li>Histogram bins retain the prepared one-year counts. The final bin is exactly age 125. A missing mean is not zero.</li><li>Report details expose retained raw product names, roles, canonical terms and source positions. Full raw reports, original age/unit strings and raw reaction strings are not retained.</li></ul></section>
    {value.termDisplayOverrides.length > 0 && <section><h3>Product disclosure labels</h3><dl className="disclosure-list">{value.termDisplayOverrides.map(item => <div key={item.canonical}><dt>{item.canonical}</dt><dd>{item.displayLabel}{item.disclosure && item.disclosure !== item.displayLabel && <> / {item.disclosure}</>}</dd></div>)}</dl></section>}
    <details className="technical-details"><summary>Release and policy identities</summary><dl className="source-facts identifiers"><div><dt>Release</dt><dd><code>{metadata.releaseId}</code></dd></div><div><dt>Dataset</dt><dd><code>{value.datasetId}</code></dd></div><div><dt>Policy</dt><dd><code>{value.policyVersion}</code></dd></div><div><dt>Schema</dt><dd>{value.schemaVersion} / <code>{value.schemaHash}</code></dd></div><div><dt>Query hash</dt><dd><code>{value.queryHash}</code></dd></div><div><dt>FDA source revision</dt><dd><code>{value.sourceRevision}</code> ({value.revisionKind})</dd></div></dl></details>
    <p className="source-interpretation">{value.interpretationNotes.join(' ')}</p>
  </section>;
}

export default function App() {
  const [navigation, setNavigation] = useState(() => parseView(location.hash, bundledMetadata));
  const { view } = navigation;
  const selectedKey = filterKey(view.filters);
  const filters = useMemo(() => view.filters, [selectedKey]);
  const [draft, setDraft] = useState({ start: String(filters.startYear), end: String(filters.endYear), product: filters.productFilter ?? '' });
  const [draftError, setDraftError] = useState('');
  const [expanded, setExpanded] = useState(false);
  const [metadataRetry, setMetadataRetry] = useState(0);
  const [queryRetry, setQueryRetry] = useState(0);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
  const connection = useRequest(navigation.error ? null : 'metadata', connect, metadataRetry);
  const connected = connection.status === 'success' && !!connection.data;
  const metadata = connection.data ?? bundledMetadata;
  const load = useCallback((signal: AbortSignal) => getOverview(filters, metadata, signal), [filters, metadata]);
  const overview = useRequest(connected && !navigation.error ? selectedKey : null, load, queryRetry);
  const displayed = overview.data ?? (sameFilters(filters, defaults) ? savedOverview : undefined);
  const stale = displayed && !sameFilters(displayed.overview.appliedFilters, filters);
  const pending = overview.status === 'loading';
  const unapplied = draft.start !== String(filters.startYear) || draft.end !== String(filters.endYear) || draft.product !== (filters.productFilter ?? '');

  useEffect(() => {
    const changed = () => setNavigation(parseView(location.hash, bundledMetadata));
    addEventListener('hashchange', changed);
    addEventListener('popstate', changed);
    if (!location.hash) history.replaceState(null, '', encodeView(defaultView(bundledMetadata), bundledMetadata));
    return () => { removeEventListener('hashchange', changed); removeEventListener('popstate', changed); };
  }, []);
  useEffect(() => {
    setDraft({ start: String(filters.startYear), end: String(filters.endYear), product: filters.productFilter ?? '' });
    setDraftError('');
  }, [filters]);
  useEffect(() => { setCopied(false); setCopyError(false); }, [selectedKey, view.tab, view.limit]);

  function navigate(next: View) {
    const hash = encodeView(next, bundledMetadata);
    if (location.hash !== hash) history.pushState(null, '', hash);
    setNavigation(parseView(hash, bundledMetadata));
  }

  function reset(tab: Tab = view.tab) {
    setDraft({ start: String(defaults.startYear), end: String(defaults.endYear), product: '' });
    setDraftError('');
    setExpanded(false);
    navigate({ ...defaultView(bundledMetadata), tab, limit: view.limit });
  }

  function apply(event: React.FormEvent) {
    event.preventDefault();
    try {
      const selection = draftFilters(draft.start, draft.end, draft.product, defaults);
      setDraftError('');
      navigate({ ...view, filters: selection });
      setExpanded(false);
      if (matchMedia('(max-width: 680px)').matches) {
        (document.activeElement as HTMLElement | null)?.blur();
        document.getElementById('selection-heading')?.focus();
      }
    } catch (error) { setDraftError(error instanceof Error ? error.message : 'The selection is invalid.'); }
  }

  const apiStatus = navigation.error ? 'Saved view' : connected ? overview.status === 'error' ? 'Query unavailable' : 'API ready' : connection.status === 'error' ? 'API unavailable' : 'Connecting';
  const statusClass = apiStatus === 'API ready' ? 'ready' : apiStatus === 'Connecting' ? 'starting' : 'unavailable';
  return <>
    <a className="skip-link" href="#main" onClick={event => { event.preventDefault(); document.getElementById('main')?.focus(); }}>Skip to FDA Explorer</a>
    <header className="app-header"><div className="header-inner"><div className="brand"><PanelsTopLeft size={21} aria-hidden /><span>Project Lab</span><span className="brand-divider">/</span><span>FDA Explorer</span></div><span className={`api-status ${statusClass}`}><Activity size={14} aria-hidden />{apiStatus}</span></div></header>
    <main id="main" tabIndex={-1}>
      <header className="page-heading"><div><h1>FDA Explorer</h1><p className="dataset-line">Food adverse-event reports <span>/</span> {date(metadata.metadata.coverageStart)} - {date(metadata.metadata.coverageEnd)}</p></div><div className="heading-tools"><span className="snapshot-badge"><Database size={14} aria-hidden />Saved snapshot</span><IconButton label="Copy view link" onClick={async () => { try { await navigator.clipboard.writeText(location.href); setCopied(true); } catch { setCopyError(true); } }}>{copied ? <Check size={18} /> : <Copy size={18} />}</IconButton></div></header>
      <p className="interpretation">These are reports, not unique people. They do not establish causation, incidence, relative risk or product safety.</p>
      <div className="sr-only" role="status">{copied ? 'View link copied.' : copyError ? 'The view link could not be copied.' : ''}</div>

      {navigation.error && <Notice alert action={<button className="button" onClick={() => reset('overview')}>Use saved default view</button>}><strong>Invalid shared view.</strong> {navigation.error} No custom query has been sent.</Notice>}
      {!navigation.error && connection.status === 'loading' && <Notice loading>Connecting to the API. {displayed ? 'The labeled saved or previous result remains visible.' : 'No result is displayed for this selection yet.'}</Notice>}
      {connection.status === 'error' && <Notice alert action={<IconButton label="Retry API connection" onClick={() => setMetadataRetry(metadataRetry + 1)}><RotateCw size={18} /></IconButton>}>{errorMessage(connection.error)} Custom queries are unavailable until the API is ready.</Notice>}

      <section className="filters" aria-label="Year and raw product selection">
        <div className="mobile-filter-heading"><button className="filter-toggle" aria-expanded={expanded} aria-controls="filter-body" onClick={() => setExpanded(!expanded)}><Filter size={17} />Filters<ChevronDown size={16} /></button><span>{filters.startYear}-{filters.endYear}{filters.productFilter !== null ? ' / product search' : ' / all products'}</span></div>
        <form id="filter-body" className={`filter-body ${expanded ? 'expanded' : ''}`} onSubmit={apply}>
          <label>Start year<select value={draft.start} onChange={event => setDraft({ ...draft, start: event.target.value })}>{Array.from({ length: defaults.endYear - defaults.startYear + 1 }, (_, index) => defaults.startYear + index).map(year => <option key={year} value={year}>{year}</option>)}</select></label>
          <label>End year<select value={draft.end} onChange={event => setDraft({ ...draft, end: event.target.value })}>{Array.from({ length: defaults.endYear - defaults.startYear + 1 }, (_, index) => defaults.startYear + index).map(year => <option key={year} value={year}>{year}{year === 2026 ? ' (Jan 1 only)' : ''}</option>)}</select></label>
          <label className="product-field">Raw suspect-product name<input value={draft.product} placeholder="e.g. CARROTS" aria-describedby="product-policy" onChange={event => setDraft({ ...draft, product: event.target.value })} autoComplete="off" spellCheck={false} /></label>
          <button className="button primary" type="submit" disabled={!connected || !!navigation.error}><Search size={16} />Apply</button>
          <IconButton label="Reset selection" onClick={() => reset()}><RotateCcw size={18} /></IconButton>
        </form>
        <p id="product-policy" className="filter-policy">Literal text in original SUSPECT product names; case-insensitive. Spaces and punctuation are preserved. {unapplied && <strong>Unapplied changes.</strong>}</p>
        {draftError && <p className="field-error" role="alert">{draftError}</p>}
      </section>

      <nav className="tabs" aria-label="FDA views" role="tablist">{tabs.map((tab, index) => <button role="tab" id={`tab-${tab.id}`} aria-controls={`panel-${tab.id}`} aria-selected={view.tab === tab.id} tabIndex={view.tab === tab.id ? 0 : -1} key={tab.id} onClick={() => navigate({ ...view, tab: tab.id })} onKeyDown={event => {
        const next = event.key === 'ArrowRight' ? (index + 1) % tabs.length : event.key === 'ArrowLeft' ? (index + tabs.length - 1) % tabs.length : event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : null;
        if (next !== null) { event.preventDefault(); navigate({ ...view, tab: tabs[next].id }); document.getElementById(`tab-${tabs[next].id}`)?.focus(); }
      }}>{tab.id === 'source' && <Info size={15} />}{tab.label}</button>)}</nav>

      <div id={`panel-${view.tab}`} role="tabpanel" aria-labelledby={`tab-${view.tab}`}>
        {view.tab === 'overview' && <section aria-labelledby="selection-heading" data-testid="overview-section" data-state={overview.status}>
          <div className="results-heading"><div><h2 id="selection-heading" tabIndex={-1}>{displayed ? 'Displayed selection' : 'Requested selection'}</h2><SelectionLabel filters={displayed?.overview.appliedFilters ?? filters} /></div><span className={`result-origin ${stale ? 'previous' : ''}`}>{stale ? 'Previous result' : displayed?.source === 'sqlite' ? 'API query / saved snapshot' : 'Saved overview / data snapshot'}</span></div>
          {pending && <Notice loading><strong>Querying:</strong> <SelectionLabel filters={filters} /> {stale && 'Previous numbers retain their original selection.'}</Notice>}
          {overview.status === 'error' && <Notice alert action={<IconButton label="Retry overview" onClick={() => setQueryRetry(queryRetry + 1)}><RotateCw size={18} /></IconButton>}>{errorMessage(overview.error)}</Notice>}
          {displayed ? <div className={stale ? 'previous-results' : ''} aria-busy={pending}><OverviewCharts overview={displayed.overview} metadata={metadata} /></div> : <p className="empty-state">No results are displayed for this selection yet.</p>}
        </section>}
        {view.tab === 'reports' && <Reports key={selectedKey + '|' + view.limit} filters={filters} metadata={metadata} connected={connected && !navigation.error} limit={view.limit} setLimit={limit => navigate({ ...view, limit })} />}
        {view.tab === 'source' && <Source metadata={metadata} connected={connected} />}
      </div>
      <footer className="page-footer"><span>Snapshot acquired {date(metadata.snapshotAcquiredAt)} / <code title={metadata.releaseId}>{metadata.releaseId.split(':')[1].slice(0, 12)}</code></span><span>Prepared read-only data / not live FDA data</span></footer>
    </main>
  </>;
}
