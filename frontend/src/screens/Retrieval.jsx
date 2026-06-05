import { SlidersHorizontal } from 'lucide-react';
import { RETRIEVAL_MIN, RETRIEVAL_MAX } from '../utils/settings.js';

export default function Retrieval({ settings, setSettings }) {
  const automatic = settings.retrievalLimit == null;
  const value = automatic ? '' : String(settings.retrievalLimit);

  const setAutomatic = () => {
    setSettings((s) => {
      const next = { ...s, retrievalLimit: null };
      return next;
    });
  };

  const setLimit = (raw) => {
    if (raw === '') {
      setAutomatic();
      return;
    }
    const n = parseInt(raw, 10);
    if (Number.isNaN(n)) return;
    setSettings((s) => ({ ...s, retrievalLimit: n }));
  };

  return (
    <div className="page-scroll scroll">
      <div className="page-inner fade-in">
        <h1 className="page-h">Retrieval</h1>
        <p className="page-sub">
          Control how many knowledge-base chunks are merged into each answer or search. Page and
          paragraph limits stay at server defaults; only the final cap is adjustable here.
        </p>

        <div className="panel settings-panel">
          <div className="settings-panel-head">
            <SlidersHorizontal size={18} style={{ color: 'var(--accent)' }} />
            <span>Final retrieval limit</span>
          </div>

          <label className="settings-radio">
            <input
              type="radio"
              name="retrieval-mode"
              checked={automatic}
              onChange={setAutomatic}
            />
            <span>
              <strong>Automatic</strong>
              <span className="muted block-sub">
                Query refinement chooses between {RETRIEVAL_MIN} and {RETRIEVAL_MAX} chunks per
                question.
              </span>
            </span>
          </label>

          <label className="settings-radio">
            <input
              type="radio"
              name="retrieval-mode"
              checked={!automatic}
              onChange={() =>
                setSettings((s) => ({
                  ...s,
                  retrievalLimit: s.retrievalLimit ?? 10,
                }))
              }
            />
            <span>
              <strong>Fixed limit</strong>
              <span className="muted block-sub">Always retrieve this many top chunks after ranking.</span>
            </span>
          </label>

          {!automatic && (
            <div className="settings-field" style={{ marginTop: 12 }}>
              <div className="field-label">Chunks ({RETRIEVAL_MIN}–{RETRIEVAL_MAX})</div>
              <input
                className="settings-input"
                type="number"
                min={RETRIEVAL_MIN}
                max={RETRIEVAL_MAX}
                value={value}
                onChange={(e) => setLimit(e.target.value)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
