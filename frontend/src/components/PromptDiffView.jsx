import { useMemo } from 'react';
import { diffLines } from 'diff';

function lineCount(text) {
  if (!text) return 0;
  const lines = text.split('\n');
  if (lines.length > 0 && lines[lines.length - 1] === '') lines.pop();
  return lines.length;
}

function countChanges(parts) {
  let added = 0;
  let removed = 0;
  for (const p of parts) {
    const n = lineCount(p.value);
    if (p.added) added += n;
    else if (p.removed) removed += n;
  }
  return { added, removed };
}

function DiffLines({ part, partIndex }) {
  const lines = part.value.split('\n');
  const isLastEmpty = lines.length > 0 && lines[lines.length - 1] === '';
  const rows = isLastEmpty ? lines.slice(0, -1) : lines;
  const prefix = part.added ? '+' : part.removed ? '−' : ' ';

  return rows.map((line, j) => (
    <div
      key={`${partIndex}-${j}`}
      className={
        part.added ? 'diff-line added' : part.removed ? 'diff-line removed' : 'diff-line ctx'
      }
    >
      <span className="diff-gutter">{prefix}</span>
      <span className="diff-text">{line || ' '}</span>
    </div>
  ));
}

export default function PromptDiffView({
  oldText,
  newText,
  oldLabel = 'Default',
  newLabel = 'Your draft',
}) {
  const parts = useMemo(() => diffLines(oldText || '', newText || ''), [oldText, newText]);
  const { added, removed } = useMemo(() => countChanges(parts), [parts]);
  const unchanged = added === 0 && removed === 0;

  if (unchanged) {
    return (
      <div className="prompt-diff prompt-diff-empty">
        <p>No differences from {oldLabel.toLowerCase()}.</p>
      </div>
    );
  }

  return (
    <div className="prompt-diff">
      <div className="prompt-diff-summary">
        <span className="diff-stat removed">−{removed} line{removed === 1 ? '' : 's'}</span>
        <span className="diff-stat added">+{added} line{added === 1 ? '' : 's'}</span>
        <span className="faint">
          {oldLabel} → {newLabel}
        </span>
      </div>
      <pre className="prompt-diff-body scroll" aria-label="Prompt diff">
        {parts.map((part, i) => (
          <DiffLines key={i} part={part} partIndex={i} />
        ))}
      </pre>
    </div>
  );
}
