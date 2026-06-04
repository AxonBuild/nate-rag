import { useEffect, useState } from 'react';
import { FileText, GitCompare, Pencil, RotateCcw, Save } from 'lucide-react';
import { api } from '../api/client.js';
import PromptDiffView from '../components/PromptDiffView.jsx';
import { toUserFacingMessage } from '../utils/userFacingError.js';

function syncSettingsFromResponse(setSettings, data) {
  setSettings((s) => ({
    ...s,
    systemPrompt: data.is_custom ? data.effective_prompt : '',
  }));
}

export default function SystemPrompt({ setSettings }) {
  const [draft, setDraft] = useState('');
  const [defaultPrompt, setDefaultPrompt] = useState('');
  const [isCustom, setIsCustom] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [savedAt, setSavedAt] = useState(null);
  const [baseline, setBaseline] = useState('');
  const [viewMode, setViewMode] = useState('edit');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError('');
      try {
        const data = await api.getSystemPrompt();
        if (cancelled) return;
        setDefaultPrompt(data.default_prompt);
        setDraft(data.effective_prompt);
        setBaseline(data.effective_prompt);
        setIsCustom(data.is_custom);
        syncSettingsFromResponse(setSettings, data);
      } catch (e) {
        if (!cancelled) setError(toUserFacingMessage(e, 'settings'));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const dirty = !loading && draft.trim() !== baseline.trim();
  const differsFromDefault = !loading && draft.trim() !== defaultPrompt.trim();

  const save = async () => {
    setSaving(true);
    setError('');
    try {
      const data = await api.saveSystemPrompt({ system_prompt: draft });
      setDraft(data.effective_prompt);
      setDefaultPrompt(data.default_prompt);
      setIsCustom(data.is_custom);
      setBaseline(data.effective_prompt);
      syncSettingsFromResponse(setSettings, data);
      setSavedAt(new Date());
      setViewMode('edit');
    } catch (e) {
      setError(toUserFacingMessage(e, 'settings'));
    } finally {
      setSaving(false);
    }
  };

  const resetToDefault = async () => {
    setSaving(true);
    setError('');
    try {
      const data = await api.saveSystemPrompt({ system_prompt: '' });
      setDraft(data.effective_prompt);
      setDefaultPrompt(data.default_prompt);
      setIsCustom(false);
      setBaseline(data.effective_prompt);
      syncSettingsFromResponse(setSettings, data);
      setSavedAt(new Date());
      setViewMode('edit');
    } catch (e) {
      setError(toUserFacingMessage(e, 'settings'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-scroll scroll">
      <div className="page-inner fade-in">
        <h1 className="page-h">System prompt</h1>
        <p className="page-sub">
          This is the instruction Nate&apos;s AI uses when writing chat answers. Compare your
          edits to the built-in default before saving.
        </p>

        <div className="panel settings-panel">
          <div className="settings-panel-head">
            <FileText size={18} style={{ color: 'var(--accent)' }} />
            <span>Answer generation instructions</span>
            {!loading && (
              <span className={`prompt-badge${isCustom ? ' custom' : ''}`}>
                {isCustom ? 'Custom' : 'Default'}
              </span>
            )}
          </div>

          {loading ? (
            <p className="muted" style={{ padding: '12px 0' }}>Loading prompt from server…</p>
          ) : (
            <>
              <div className="prompt-view-toggle" role="tablist" aria-label="Prompt view">
                <button
                  type="button"
                  role="tab"
                  aria-selected={viewMode === 'edit'}
                  className={`prompt-view-btn${viewMode === 'edit' ? ' active' : ''}`}
                  onClick={() => setViewMode('edit')}
                >
                  <Pencil size={14} />
                  Edit
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={viewMode === 'diff'}
                  className={`prompt-view-btn${viewMode === 'diff' ? ' active' : ''}`}
                  onClick={() => setViewMode('diff')}
                >
                  <GitCompare size={14} />
                  Changes
                  {differsFromDefault && <span className="prompt-view-dot" aria-hidden />}
                </button>
              </div>

              {viewMode === 'edit' ? (
                <textarea
                  className="settings-textarea"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  rows={22}
                  disabled={saving}
                />
              ) : (
                <PromptDiffView
                  oldText={defaultPrompt}
                  newText={draft}
                  oldLabel="Default"
                  newLabel="Your draft"
                />
              )}

              {error && (
                <p style={{ color: '#e05a5a', fontSize: 13, marginTop: 8 }}>{error}</p>
              )}
              <div className="settings-actions">
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    className="btn-primary-sm"
                    onClick={save}
                    disabled={saving || !dirty}
                  >
                    <Save size={15} />
                    {saving ? 'Saving…' : 'Save'}
                  </button>
                  <button
                    type="button"
                    className="icon-btn bordered"
                    onClick={resetToDefault}
                    disabled={saving || (!isCustom && !differsFromDefault)}
                    title="Restore default prompt"
                  >
                    <RotateCcw size={15} />
                    Reset to default
                  </button>
                </div>
                <span className="faint" style={{ fontSize: 12 }}>
                  {draft.trim().length} characters
                  {savedAt && !dirty
                    ? ` · Saved ${savedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
                    : dirty
                      ? ' · Unsaved changes'
                      : ''}
                </span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
