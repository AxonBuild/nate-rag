import { FileText } from 'lucide-react';

const TYPE_META = {
  qa_pair:  { color: 'var(--type-qa)',       label: 'Q&A'      },
  script:   { color: 'var(--type-script)',   label: 'Script'   },
  guide:    { color: 'var(--type-guide)',     label: 'Guide'    },
  outline:  { color: 'var(--type-guide)',     label: 'Outline'  },
  seo:      { color: 'var(--type-seo)',       label: 'SEO'      },
  pdf:      { color: 'var(--type-pdf)',       label: 'PDF'      },
  research: { color: 'var(--type-research)', label: 'Research' },
};

function SourceCard({ data }) {
  const meta = TYPE_META[data.doc_type] || TYPE_META[data.file_type] || { color: 'var(--accent)', label: data.doc_type || 'Doc' };
  const isQA = data.file_type === 'qa_pair';
  const pct = Math.round(Math.min((data.score || 0), 1) * 100);

  return (
    <div className="src-card" style={{ '--tc': meta.color }}>
      <div className="src-top">
        <span className="rank-badge">#{data.rank}</span>
        <span className="pill type">{meta.label}</span>
        {data.topic && <span className="pill topic">{data.topic}</span>}
        <div className="score-bar">
          <div className="score-track"><div className="score-fill" style={{ width: `${pct}%` }} /></div>
          <span className="score-val">{(data.score || 0).toFixed(2)}</span>
        </div>
      </div>
      <div className="src-doc">
        <FileText size={14} style={{ color: 'var(--text-3)', flex: '0 0 auto' }} />
        <span>{data.document_name}</span>
      </div>
      {isQA ? (
        <div className="qa-block">
          <div className="qa-q"><span className="qa-label">Q:</span>{data.text}</div>
          {data.answer && <div className="qa-a"><span className="qa-label">A:</span>{data.answer}</div>}
        </div>
      ) : (
        <div className="src-excerpt">{data.text}</div>
      )}
      {data.tags && data.tags.length > 0 && (
        <div className="tag-row">
          {data.tags.map((t, i) => <span key={i} className="tag">#{t.replace(/\s+/g, '')}</span>)}
        </div>
      )}
    </div>
  );
}

export function SourceList({ results }) {
  return (
    <div className="src-grid">
      {(results || []).map((r, i) => <SourceCard key={i} data={r} />)}
    </div>
  );
}

export default SourceCard;
