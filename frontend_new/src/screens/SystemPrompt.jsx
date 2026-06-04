import { FileText } from 'lucide-react';

export default function SystemPrompt({ settings, setSettings }) {
  const sys = settings.systemPrompt ?? '';

  return (
    <div className="page-scroll scroll">
      <div className="page-inner fade-in">
        <h1 className="page-h">System prompt</h1>
        <p className="page-sub">
          Optional instructions for Nate&apos;s AI when generating answers in chat. Leave empty to
          use the default firm advisor prompt on the server.
        </p>

        <div className="panel settings-panel">
          <div className="settings-panel-head">
            <FileText size={18} style={{ color: 'var(--accent)' }} />
            <span>Answer generation instructions</span>
          </div>
          <textarea
            className="sb-textarea settings-textarea"
            placeholder="Custom instructions for how answers should be written…"
            value={sys}
            onChange={(e) => setSettings((s) => ({ ...s, systemPrompt: e.target.value }))}
            rows={14}
          />
          <div className="settings-actions">
            <button
              type="button"
              className="linkbtn"
              onClick={() => setSettings((s) => ({ ...s, systemPrompt: '' }))}
              disabled={!sys.trim()}
            >
              Clear and use default
            </button>
            <span className="faint" style={{ fontSize: 12 }}>
              {sys.trim() ? `${sys.trim().length} characters` : 'Using server default'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
