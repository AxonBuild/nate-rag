function formatSeconds(ms) {
  return `${(ms / 1000).toFixed(2)} s`;
}

export default function Performance({ timing }) {
  const rows = [
    { name: 'Query refinement', ms: timing.query_refinement_ms },
    { name: 'Embedding',        ms: timing.embedding_ms },
    { name: 'Retrieval',        ms: timing.retrieval_ms },
    { name: 'Answer generation',ms: timing.answer_generation_ms },
  ].filter(r => r.ms != null && r.ms > 0);

  const max = Math.max(...rows.map(r => r.ms), 1);

  return (
    <div>
      <div className="perf-grid">
        {rows.map((r, i) => (
          <div className="perf-row" key={i}>
            <span className="perf-name">{r.name}</span>
            <div className="perf-track"><div className="perf-fill" style={{ width: `${(r.ms / max) * 100}%` }} /></div>
            <span className="perf-ms">{formatSeconds(r.ms)}</span>
          </div>
        ))}
      </div>
      {timing.total_chat_ms != null && (
        <div className="perf-total">
          <span className="muted">Total response time</span>
          <span className="v">{formatSeconds(timing.total_chat_ms)}</span>
        </div>
      )}
    </div>
  );
}
