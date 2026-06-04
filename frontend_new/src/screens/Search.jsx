import { useState } from 'react';
import { Search as SearchIcon, Sparkles, Clock } from 'lucide-react';
import Disclosure from '../components/Disclosure.jsx';
import { SourceList } from '../components/SourceCard.jsx';
import Performance from '../components/Performance.jsx';
import { api } from '../api/client.js';
import { filterPayload } from '../utils/filters.js';

export default function Search({ filters }) {
  const [q, setQ] = useState('');
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState(null);
  const [error, setError] = useState('');

  const run = async () => {
    const v = q.trim();
    if (!v || busy) return;
    setBusy(true);
    setRes(null);
    setError('');
    try {
      const data = await api.search({ query: v, ...filterPayload(filters) });
      setRes({
        original: data.query || v,
        refined: data.refined_query,
        keywords: data.keywords || [],
        results: data.results || [],
        timing: data.timing,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const totalMs = res?.timing?.total_chat_ms ?? res?.timing?.total_ms;
  const hasFilters = filters.topic !== 'All' || filters.docType !== 'All';

  return (
    <div className="page-scroll scroll">
      <div className="page-inner fade-in">
        <h1 className="page-h">Search the knowledge base</h1>
        <p className="page-sub">
          Semantic search across guides, scripts, SEO content, and client Q&amp;A. Results respect your sidebar filters.
        </p>

        <div className="search-bar">
          <span className="sico"><SearchIcon size={19} /></span>
          <input
            value={q}
            placeholder='Search documents — e.g. "depreciation recapture" or "Augusta Rule rate"'
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') run(); }}
          />
          <button type="button" className="search-go" onClick={run} disabled={!q.trim() || busy}>
            {busy ? 'Searching…' : (<><SearchIcon size={15} /> Search</>)}
          </button>
        </div>

        {hasFilters && (
          <div style={{ display: 'flex', gap: 7, marginTop: 13, alignItems: 'center' }}>
            <span className="faint" style={{ fontSize: 12 }}>Active filters:</span>
            {filters.topic !== 'All' && <span className="pill">{filters.topic}</span>}
            {filters.docType !== 'All' && <span className="pill doc">{filters.docType}</span>}
          </div>
        )}

        {error && (
          <p style={{ marginTop: 20, color: '#e05a5a', fontSize: 14 }}>{error}</p>
        )}

        {busy && (
          <div style={{ marginTop: 34, display: 'flex', justifyContent: 'center' }}>
            <div className="typing"><span /><span /><span /></div>
          </div>
        )}

        {res && !busy && (
          <div className="fade-in">
            <div className="query-boxes">
              <div className="qbox">
                <div className="qlab"><SearchIcon size={12} /> Original query</div>
                <div className="qval">{res.original}</div>
              </div>
              <div className="qbox refined">
                <div className="qlab"><Sparkles size={12} /> Refined query</div>
                <div className="qval">{res.refined}</div>
              </div>
            </div>
            <div className="kw-row" style={{ marginBottom: 4 }}>
              {res.keywords.map((k, i) => <span key={i} className="kw">{k}</span>)}
            </div>

            <div className="results-head">
              <span className="rh">Results</span>
              <span className="rc">
                {res.results.length} documents
                {totalMs != null ? ` · ${(totalMs / 1000).toFixed(2)}s` : ''}
              </span>
            </div>
            <SourceList results={res.results} />

            {res.timing && (
              <div style={{ marginTop: 16 }}>
                <Disclosure
                  icon={Clock}
                  label="Performance"
                  count={totalMs != null ? `${(totalMs / 1000).toFixed(2)}s` : undefined}
                >
                  <Performance timing={res.timing} />
                </Disclosure>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
