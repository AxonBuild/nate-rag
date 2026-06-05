import { useEffect, useMemo, useState } from 'react';
import {
  FileJson,
  FileSpreadsheet,
  FileText,
  FileType,
  Mic,
  Upload,
} from 'lucide-react';
import { api } from '../api/client.js';
import { toUserFacingMessage } from '../utils/userFacingError.js';

const TABS = [
  { id: 'transcript', label: 'Transcripts', icon: Mic },
  { id: 'qa', label: 'QA pairs', icon: FileSpreadsheet },
  { id: 'document', label: 'Documents', icon: FileType },
];

const METADATA_RE = /^meeting-metadata-([A-Za-z0-9]+)\.(txt|json)$/i;

function meetingIdFromFilename(name) {
  if (!name) return null;
  const base = name.split(/[/\\]/).pop();
  const m = base.match(METADATA_RE);
  return m ? m[1] : null;
}

function guessColumn(columns, patterns) {
  if (!columns.length) return '';
  for (const pattern of patterns) {
    const hit = columns.find((c) => pattern.test(c));
    if (hit) return hit;
  }
  return '';
}

function FileField({ id, label, hint, accept, required, icon: Icon, file, onChange }) {
  return (
    <div className="login-field ingest-file-field">
      <label htmlFor={id}>
        {label}
        {required ? <span className="ingest-required">Required</span> : null}
      </label>
      {hint ? <p className="ingest-file-hint">{hint}</p> : null}
      <div className="ingest-file-row">
        <Icon size={18} className="ingest-file-ico" aria-hidden />
        <input
          id={id}
          type="file"
          accept={accept}
          onChange={(e) => onChange(e.target.files?.[0] || null)}
        />
        <span className="ingest-file-name muted">
          {file ? file.name : 'No file chosen'}
        </span>
      </div>
    </div>
  );
}

function ColumnSelect({ id, label, value, columns, onChange, required }) {
  return (
    <div className="login-field">
      <label htmlFor={id}>
        {label}
        {required ? <span className="ingest-required">Required</span> : null}
      </label>
      <select
        id={id}
        className="settings-input ingest-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={!columns.length}
      >
        {!required ? <option value="">— None —</option> : null}
        {columns.map((col) => (
          <option key={col} value={col}>
            {col}
          </option>
        ))}
      </select>
    </div>
  );
}

function IngestError({ message }) {
  if (!message) return null;
  return <p className="ingest-error">{message}</p>;
}

function TranscriptTab({ busy, setBusy, setError }) {
  const [transcriptFile, setTranscriptFile] = useState(null);
  const [metadataFile, setMetadataFile] = useState(null);
  const [result, setResult] = useState(null);

  const meetingId = useMemo(
    () => meetingIdFromFilename(metadataFile?.name),
    [metadataFile],
  );

  const canSubmit = Boolean(transcriptFile && metadataFile && !busy);

  const submit = async () => {
    if (!transcriptFile) {
      setError('Transcript JSON is required.');
      return;
    }
    if (!metadataFile) {
      setError('Meeting metadata file is required.');
      return;
    }
    setBusy(true);
    setError('');
    setResult(null);
    try {
      const form = new FormData();
      form.append('transcript', transcriptFile);
      form.append('metadata', metadataFile);
      setResult(await api.ingestTranscript(form));
    } catch (e) {
      setError(toUserFacingMessage(e, 'generic'));
    } finally {
      setBusy(false);
    }
  };

  const processed = result?.processed;

  return (
    <>
      <FileField
        id="ingest-transcript"
        label="Transcript JSON"
        hint="Fireflies export: transcript.json"
        accept=".json,application/json"
        required
        icon={FileJson}
        file={transcriptFile}
        onChange={setTranscriptFile}
      />
      <FileField
        id="ingest-metadata"
        label="Meeting metadata"
        hint="Fireflies export: meeting-metadata-{id}.txt"
        accept=".txt,.json,text/plain,application/json"
        required
        icon={FileText}
        file={metadataFile}
        onChange={setMetadataFile}
      />
      {meetingId ? (
        <p className="ingest-meta-id">
          Meeting ID: <code>{meetingId}</code>
        </p>
      ) : null}
      <button
        type="button"
        className="btn-primary-sm"
        disabled={!canSubmit}
        onClick={submit}
      >
        {busy ? 'Processing…' : 'Run extraction'}
      </button>
      {processed ? (
        <div className="ingest-result">
          <h2 className="panel-h">Result</h2>
          <ul className="ingest-result-list">
            <li><strong>Meeting:</strong> {processed.meeting_title || '—'}</li>
            <li><strong>Date:</strong> {processed.meeting_date || '—'}</li>
            <li><strong>Client:</strong> {processed.client}</li>
            <li><strong>QA groups:</strong> {processed.qa_groups?.length ?? 0}</li>
            <li><strong>Indexed points:</strong> {result.ingested_points ?? 0}</li>
            <li><strong>LLM cost:</strong> ${Number(result.cost_usd || 0).toFixed(4)}</li>
          </ul>
        </div>
      ) : null}
    </>
  );
}

function QaTab({ busy, setBusy, setError }) {
  const [file, setFile] = useState(null);
  const [columns, setColumns] = useState([]);
  const [loadingColumns, setLoadingColumns] = useState(false);
  const [questionCol, setQuestionCol] = useState('');
  const [answerCol, setAnswerCol] = useState('');
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!file) {
      setColumns([]);
      setQuestionCol('');
      setAnswerCol('');
      return undefined;
    }

    let cancelled = false;
    (async () => {
      setLoadingColumns(true);
      setError('');
      try {
        const form = new FormData();
        form.append('file', file);
        const data = await api.previewQaColumns(form);
        if (cancelled) return;
        const cols = data.columns || [];
        setColumns(cols);
        setQuestionCol(
          guessColumn(cols, [/question/i, /^q$/i, /query/i]) || cols[0] || '',
        );
        setAnswerCol(
          guessColumn(cols, [/answer/i, /^a$/i, /response/i]) || cols[1] || cols[0] || '',
        );
      } catch (e) {
        if (!cancelled) {
          setColumns([]);
          setError(toUserFacingMessage(e, 'generic'));
        }
      } finally {
        if (!cancelled) setLoadingColumns(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [file, setError]);

  const canSubmit = Boolean(
    file && questionCol && answerCol && !busy && !loadingColumns,
  );

  const submit = async () => {
    if (!file || !questionCol || !answerCol) return;
    setBusy(true);
    setError('');
    setResult(null);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('question_column', questionCol);
      form.append('answer_column', answerCol);
      setResult(await api.ingestQa(form));
    } catch (e) {
      setError(toUserFacingMessage(e, 'generic'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <FileField
        id="ingest-qa-file"
        label="Spreadsheet"
        hint="CSV or XLSX with question and answer columns"
        accept=".csv,.xlsx,.xlsm,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        required
        icon={FileSpreadsheet}
        file={file}
        onChange={(f) => {
          setResult(null);
          setFile(f);
        }}
      />

      {loadingColumns ? (
        <p className="ingest-file-hint">Reading columns…</p>
      ) : null}

      {columns.length > 0 ? (
        <div className="ingest-columns">
          <ColumnSelect
            id="qa-question-col"
            label="Question column"
            value={questionCol}
            columns={columns}
            onChange={setQuestionCol}
            required
          />
          <ColumnSelect
            id="qa-answer-col"
            label="Answer column"
            value={answerCol}
            columns={columns}
            onChange={setAnswerCol}
            required
          />
        </div>
      ) : null}

      <button
        type="button"
        className="btn-primary-sm"
        disabled={!canSubmit}
        onClick={submit}
      >
        {busy ? 'Ingesting…' : 'Ingest QA pairs'}
      </button>

      {result ? (
        <div className="ingest-result">
          <h2 className="panel-h">Result</h2>
          <ul className="ingest-result-list">
            <li><strong>Total rows:</strong> {result.total_rows}</li>
            <li><strong>Valid rows:</strong> {result.valid_rows}</li>
            <li><strong>Skipped (empty):</strong> {result.skipped_empty}</li>
            <li><strong>Indexed points:</strong> {result.ingested_points}</li>
          </ul>
        </div>
      ) : null}
    </>
  );
}

function DocumentTab({ busy, setBusy, setError }) {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);

  const canSubmit = Boolean(file && !busy);

  const submit = async () => {
    if (!file) return;
    setBusy(true);
    setError('');
    setResult(null);
    try {
      const form = new FormData();
      form.append('file', file);
      setResult(await api.ingestDocument(form));
    } catch (e) {
      setError(toUserFacingMessage(e, 'generic'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <FileField
        id="ingest-doc-file"
        label="Document"
        hint="PDF or DOCX — indexed using the filename as the document name"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        required
        icon={FileType}
        file={file}
        onChange={(f) => {
          setResult(null);
          setFile(f);
        }}
      />
      <button
        type="button"
        className="btn-primary-sm"
        disabled={!canSubmit}
        onClick={submit}
      >
        {busy ? 'Processing…' : 'Ingest document'}
      </button>

      {result ? (
        <div className="ingest-result">
          <h2 className="panel-h">Result</h2>
          <ul className="ingest-result-list">
            <li><strong>Document:</strong> {result.document_name}</li>
            <li><strong>Characters:</strong> {result.character_count?.toLocaleString()}</li>
            <li><strong>Chunks created:</strong> {result.chunks_created}</li>
            {result.chunks_by_level ? (
              <li>
                <strong>By level:</strong>{' '}
                {Object.entries(result.chunks_by_level)
                  .map(([level, n]) => `L${level}: ${n}`)
                  .join(', ')}
              </li>
            ) : null}
          </ul>
        </div>
      ) : null}
    </>
  );
}

export default function Ingest() {
  const [tab, setTab] = useState('transcript');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const switchTab = (id) => {
    if (busy) return;
    setTab(id);
    setError('');
  };

  const tabCopy = {
    transcript:
      'Extract Q&A from Fireflies meetings. Requires transcript.json and meeting-metadata-*.txt.',
    qa: 'Upload a CSV or XLSX with question and answer columns only.',
    document: 'Upload a PDF or DOCX file. The filename is used as the document name in search.',
  };

  return (
    <div className="page-scroll scroll">
      <div className="page-inner fade-in">
        <h1 className="page-h">Ingest</h1>
        <p className="page-sub">
          Add transcripts, QA spreadsheets, or knowledge-base documents to the search index.
        </p>

        <div className="ingest-tabs prompt-view-toggle" role="tablist">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={tab === id}
              className={`prompt-view-btn${tab === id ? ' active' : ''}`}
              onClick={() => switchTab(id)}
              disabled={busy}
            >
              <Icon size={15} />
              {label}
            </button>
          ))}
        </div>

        <div className="panel settings-panel ingest-panel">
          <div className="settings-panel-head">
            <Upload size={18} style={{ color: 'var(--accent)' }} />
            <span>{TABS.find((t) => t.id === tab)?.label}</span>
          </div>
          <p className="panel-sub">{tabCopy[tab]}</p>

          {tab === 'transcript' ? (
            <TranscriptTab busy={busy} setBusy={setBusy} setError={setError} />
          ) : null}
          {tab === 'qa' ? (
            <QaTab busy={busy} setBusy={setBusy} setError={setError} />
          ) : null}
          {tab === 'document' ? (
            <DocumentTab busy={busy} setBusy={setBusy} setError={setError} />
          ) : null}

          <IngestError message={error} />
        </div>
      </div>
    </div>
  );
}
