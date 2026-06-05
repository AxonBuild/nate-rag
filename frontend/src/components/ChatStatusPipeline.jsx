import { Loader2, Search, ShieldCheck, Sparkles, PenLine } from 'lucide-react';
import { CHAT_PIPELINE } from '../api/chatStream.js';

const STEP_ICONS = {
  refining: Sparkles,
  retrieving: Search,
  generating: PenLine,
  verifying: ShieldCheck,
};

export default function ChatStatusPipeline({ currentPhase, retryHint }) {
  const slotKey = retryHint ? 'retry' : currentPhase;
  if (!slotKey) return null;

  const step = retryHint
    ? { id: 'retry', label: retryHint }
    : CHAT_PIPELINE.find((s) => s.id === currentPhase);

  if (!step) return null;

  const Icon = retryHint ? Loader2 : STEP_ICONS[step.id];

  return (
    <div
      key={slotKey}
      className={`chat-status-slot${retryHint ? ' retry' : ''}`}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <span className="chat-status-icon-wrap">
        <Icon
          size={15}
          className={`chat-status-icon phase-${step.id}${retryHint ? ' spinning' : ' animating'}`}
        />
      </span>
      <span className="chat-status-label">{step.label}</span>
      {!retryHint && (
        <span className="chat-status-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
      )}
    </div>
  );
}
