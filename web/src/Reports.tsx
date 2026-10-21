import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, ChevronsLeft, Eye, RotateCw, X } from 'lucide-react';
import { getDetail, getReports, errorMessage } from './api';
import { filterKey, firstPage, nextPage, previousPage, sameFilters } from './selection';
import type { Filters, MetadataResponse } from './types';
import { useRequest } from './useRequest';
import { IconButton, Notice, SelectionLabel, age, date, number } from './ui';

function DetailDialog({ reportId, filters, metadata, close }: {
  reportId: string; filters: Filters; metadata: MetadataResponse; close: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [retry, setRetry] = useState(0);
  const load = useCallback((signal: AbortSignal) => getDetail(filters, metadata, reportId, signal), [filters, metadata, reportId]);
  const detail = useRequest(reportId, load, retry);
  useEffect(() => {
    const element = dialog.current!;
    element.showModal();
    return () => element.close();
  }, []);
  const report = detail.data?.detail.report;
  return <dialog ref={dialog} className="report-dialog" onCancel={event => { event.preventDefault(); dialog.current?.close(); }} onClose={() => { if (dialog.current && !dialog.current.open) close(); }} aria-labelledby="detail-title">
    <header className="dialog-header"><div><p className="eyebrow">Retained report details</p><h2 id="detail-title">Report {reportId}</h2></div><IconButton label="Close report details" onClick={() => dialog.current?.close()}><X size={20} /></IconButton></header>
    <SelectionLabel filters={filters} />
    <p className="muted snapshot-line">Saved data snapshot; not a causal or product-safety finding.</p>
    {detail.status === 'loading' && <Notice loading>Loading report details.</Notice>}
    {detail.status === 'error' && <Notice alert action={<IconButton label="Retry report details" onClick={() => setRetry(retry + 1)}><RotateCw size={18} /></IconButton>}>{errorMessage(detail.error)}</Notice>}
    {report && <>
      <dl className="detail-facts"><div><dt>Event date</dt><dd>{date(report.eventDate)}</dd></div><div><dt>Age</dt><dd>{age(report.ageYears)}</dd></div><div><dt>Reported gender</dt><dd>{report.gender}</dd></div></dl>
      <h3>Products in this report</h3>
      <div className="table-scroll" tabIndex={0} role="region" aria-label="Report products"><table><caption className="sr-only">Raw products, roles, canonical terms and current-search matching</caption><thead><tr><th scope="col">Raw product name</th><th scope="col">Role</th><th scope="col">Canonical term</th><th scope="col">Search match</th></tr></thead><tbody>{report.products.map(item => <tr key={item.ordinal}><td>{item.rawName}</td><td>{item.role}</td><td>{item.displayLabel ?? item.canonicalTerm ?? 'Not available'}{item.disclosure && <small className="disclosure">{item.disclosure}</small>}</td><td>{item.matchesProductFilter === null ? 'No product filter' : item.matchesProductFilter ? 'Yes' : 'No'}</td></tr>)}</tbody></table></div>
      {([['Canonical suspect products', report.suspectProductsCanonical], ['Reactions', report.reactionsCanonical], ['Outcomes', report.outcomesCanonical]] as const).map(([title, terms]) => <section key={title} className="detail-terms"><h3>{title}</h3>{terms.length ? <ul>{terms.map(term => <li key={term}>{term}</li>)}</ul> : <p>None retained.</p>}</section>)}
      <section className="provenance"><h3>Source position</h3><p><code>{report.provenance.sourcePage}</code></p><p>Report position {report.provenance.sourceIndex} in that saved page.</p><p className="muted">Original age/unit strings, raw reaction strings and full raw JSON are not retained by this prepared database.</p></section>
    </>}
  </dialog>;
}

export function Reports({ filters, metadata, connected, limit, setLimit }: {
  filters: Filters; metadata: MetadataResponse; connected: boolean; limit: number; setLimit: (limit: number) => void;
}) {
  const [position, setPosition] = useState(firstPage);
  const [retry, setRetry] = useState(0);
  const [reportId, setReportId] = useState<string | null>(null);
  const closeButton = useRef<HTMLButtonElement | null>(null);
  const load = useCallback(async (signal: AbortSignal) => ({
    response: await getReports(filters, metadata, limit, position.cursor, signal), number: position.number,
  }), [filters, metadata, limit, position]);
  const key = JSON.stringify([metadata.releaseId, filterKey(filters), limit, position.cursor]);
  const result = useRequest(connected ? key : null, load, retry);
  const page = result.data?.response.page;
  const current = result.dataKey === key && result.status === 'success';
  const busy = result.status === 'loading';
  const close = useCallback(() => {
    setReportId(null);
    // Wait for the modal to leave the top layer before restoring outside focus.
    requestAnimationFrame(() => closeButton.current?.focus());
  }, []);
  return <section aria-labelledby="reports-heading" className="reports-section">
    <header className="section-header reports-heading"><div><h2 id="reports-heading">Matching reports</h2><p>Report ID ascending; one row per report.</p></div><label className="page-size">Rows per page<select value={limit} onChange={event => setLimit(Number(event.target.value))}><option value={25}>25</option><option value={50}>50</option><option value={100}>100</option></select></label></header>
    <div className="displayed-selection"><span>{page ? 'Displayed selection' : 'Requested selection'}</span><SelectionLabel filters={page?.appliedFilters ?? filters} /></div>
    {!connected && <Notice>Report queries are unavailable until the API is ready. No reports are bundled with the saved overview.</Notice>}
    {busy && <Notice loading>{page ? `Loading page ${position.number}. Page ${result.data!.number} remains displayed.` : 'Loading matching reports.'}</Notice>}
    {result.status === 'error' && <Notice alert action={<IconButton label="Retry report page" onClick={() => setRetry(retry + 1)}><RotateCw size={18} /></IconButton>}>{errorMessage(result.error)}</Notice>}
    {page && <>
      <div className="table-scroll report-table" tabIndex={0} role="region" aria-label="Matching report rows" aria-busy={busy}>
        <table><caption className="sr-only">Matching reports, page {result.data!.number}, saved snapshot</caption><thead><tr><th scope="col" aria-sort="ascending">Report ID</th><th scope="col">Event date</th><th scope="col">Age</th><th scope="col">Gender</th><th scope="col"><span className="sr-only">Details</span></th></tr></thead>
          <tbody>{page.items.map(item => <tr key={item.reportId}><th scope="row"><button className="report-link" disabled={!current} onClick={event => { closeButton.current = event.currentTarget; setReportId(item.reportId); }}>{item.reportId}</button></th><td>{date(item.eventDate)}</td><td>{age(item.ageYears)}</td><td>{item.gender}</td><td><IconButton label={`View report ${item.reportId}`} disabled={!current} onClick={event => { closeButton.current = event.currentTarget; setReportId(item.reportId); }}><Eye size={17} /></IconButton></td></tr>)}</tbody>
        </table>
      </div>
      {page.items.length === 0 && <p className="empty-state">No reports match this selection.</p>}
      <nav className="pagination" aria-label="Report pages"><span>Page {result.data!.number} / {number(page.returnedCount)} rows{!page.hasMore ? ' / last page' : ''}</span><div>
        <IconButton label="First report page" disabled={busy || position.number === 1} onClick={() => setPosition(firstPage())}><ChevronsLeft size={18} /></IconButton>
        <IconButton label="Previous report page" disabled={!current || !position.previous.length} onClick={() => setPosition(previousPage(position))}><ArrowLeft size={18} /></IconButton>
        <IconButton label="Next report page" disabled={!current || !page.hasMore} onClick={() => page.nextCursor && setPosition(nextPage(position, page.nextCursor))}><ArrowRight size={18} /></IconButton>
      </div></nav>
    </>}
    {reportId && current && page && sameFilters(page.appliedFilters, filters) && <DetailDialog reportId={reportId} filters={filters} metadata={metadata} close={close} />}
  </section>;
}
