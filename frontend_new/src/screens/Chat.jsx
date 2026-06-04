import { useState, useRef, useEffect } from 'react';
import { Sparkles, ArrowUp, Copy, Check, RefreshCw, Layers, Clock, ShieldCheck } from 'lucide-react';
import Markdown from '../components/Markdown.jsx';
import Disclosure from '../components/Disclosure.jsx';
import { SourceList } from '../components/SourceCard.jsx';
import Performance from '../components/Performance.jsx';
import Refinement from '../components/Refinement.jsx';
import { SUGGESTIONS } from '../constants/suggestions.js';
import { chatStream } from '../api/chatStream.js';
import ChatStatusPipeline from '../components/ChatStatusPipeline.jsx';
import { useAnswerReveal } from '../hooks/useAnswerReveal.js';
import { requestSettingsPayload } from '../utils/settings.js';

const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

function formatStreamError(err) {
  const raw = err?.message || 'Unknown error';
  if (/timeout|timed out/i.test(raw)) {
    return 'This request timed out. Complex questions can take a while — tap Retry to try again.';
  }
  return `Something went wrong: ${raw}`;
}

function verificationLabel(verification) {
  if (!verification) return null;
  return verification.is_correct && !verification.was_corrected ? 'Succeeded' : 'Denied';
}

function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="icon-btn"
      title="Copy"
      onClick={() => {
        navigator.clipboard.writeText(text).catch(() => {});
        setCopied(true);
        setTimeout(() => setCopied(false), 1400);
      }}
    >
      {copied ? <Check size={15} /> : <Copy size={15} />}
      {copied ? 'Copied' : null}
    </button>
  );
}

function AiMessage({ msg, onRegenerate, onRetry }) {
  const streaming = Boolean(msg.streaming);
  const showPipeline = streaming && !msg.answer && !msg.error && (msg.status || msg.retryHint);

  return (
    <div className="msg ai msg-enter">
      <div className="mavatar"><Sparkles size={18} /></div>
      <div className="msg-body">
        <div className="msg-meta">
          <div className="msg-meta-head">
            <span className="who">Nate&apos;s AI</span>
            <span className="ts">{msg.ts}</span>
          </div>
          {showPipeline && (
            <ChatStatusPipeline currentPhase={msg.status} retryHint={msg.retryHint} />
          )}
        </div>
        {msg.error ? (
          <>
            <div className="ai-content" style={{ color: '#e05a5a' }}>{msg.answer}</div>
            {onRetry && (
              <div className="msg-actions">
                <button type="button" className="icon-btn" title="Retry" onClick={onRetry}>
                  <RefreshCw size={15} />
                  Retry
                </button>
              </div>
            )}
          </>
        ) : showPipeline ? null : streaming ? (
          <div className="ai-content">
            <Markdown text={msg.answer || ''} />
            <span className="cursor-blink" />
          </div>
        ) : (
          <Markdown text={msg.answer} />
        )}
        {!streaming && !msg.error && (
          <>
            <div className="msg-actions">
              <CopyBtn text={msg.answer} />
              {onRegenerate && (
                <button type="button" className="icon-btn" title="Regenerate" onClick={onRegenerate}>
                  <RefreshCw size={15} />
                </button>
              )}
            </div>
            {(msg.search || msg.timing || msg.verification) && (
              <div style={{ marginTop: 14 }}>
                {msg.verification && (
                  <Disclosure
                    icon={ShieldCheck}
                    label="Verification"
                    count={verificationLabel(msg.verification)}
                  >
                    <p className={`verify-status ${msg.verification.is_correct && !msg.verification.was_corrected ? 'ok' : 'denied'}`}>
                      {verificationLabel(msg.verification)}
                    </p>
                    <p style={{ fontSize: 13.5, lineHeight: 1.55, margin: '8px 0 0' }}>
                      {msg.verification.reasoning}
                    </p>
                  </Disclosure>
                )}
                {msg.search && (msg.search.results || []).length > 0 && (
                  <Disclosure icon={Layers} label="Sources" count={`${msg.search.results.length} documents`}>
                    <SourceList results={msg.search.results} />
                  </Disclosure>
                )}
                {msg.search && (msg.search.refined_query || (msg.search.keywords || []).length > 0) && (
                  <Disclosure icon={Sparkles} label="Query refinement">
                    <Refinement refined={msg.search.refined_query} keywords={msg.search.keywords} />
                  </Disclosure>
                )}
                {msg.timing && (
                  <Disclosure
                    icon={Clock}
                    label="Performance"
                    count={
                      msg.timing.total_chat_ms != null
                        ? `${(msg.timing.total_chat_ms / 1000).toFixed(2)}s`
                        : undefined
                    }
                  >
                    <Performance timing={msg.timing} />
                  </Disclosure>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function UserMessage({ msg, initials }) {
  return (
    <div className="msg user msg-enter">
      <div className="avatar sm">{initials}</div>
      <div className="msg-body">
        <div className="msg-meta" style={{ justifyContent: 'flex-end' }}>
          <span className="ts">{msg.ts}</span>
          <span className="who">You</span>
        </div>
        <div className="user-bubble">{msg.text}</div>
      </div>
    </div>
  );
}

function Empty({ userName, onPick }) {
  const first = userName?.split(' ')[0] || 'there';
  return (
    <div className="empty fade-in">
      <div className="glyph"><Sparkles size={28} style={{ color: 'var(--accent)' }} /></div>
      <h2>How can I help, {first}?</h2>
      <p>
        Ask anything about tax strategy, real-estate rules, or deductions. I&apos;ll answer from
        Meeker CPA&apos;s proprietary playbooks, scripts, and client transcripts — with sources.
      </p>
      <div className="suggest-grid">
        {SUGGESTIONS.map((s, i) => {
          const Icon = s.icon;
          return (
            <button type="button" className="suggest" key={i} onClick={() => onPick(s.q)}>
              <div className="st">
                <span className="ic"><Icon size={16} /></span>
                {s.title}
              </div>
              <div className="sd">{s.desc}</div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Composer({ onSend, busy }) {
  const [val, setVal] = useState('');
  const ref = useRef(null);

  const resize = () => {
    const t = ref.current;
    if (!t) return;
    t.style.height = 'auto';
    t.style.height = `${Math.min(t.scrollHeight, 132)}px`;
  };

  useEffect(resize, [val]);

  const submit = () => {
    const v = val.trim();
    if (!v || busy) return;
    onSend(v);
    setVal('');
    if (ref.current) ref.current.style.height = 'auto';
  };

  return (
    <div className="composer-wrap">
      <div className="composer-inner">
        <div className="composer">
          <textarea
            ref={ref}
            rows={1}
            value={val}
            placeholder="Ask about tax strategy, real estate, deductions…"
            onChange={(e) => setVal(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
            }}
          />
          <button type="button" className="send-btn" disabled={!val.trim() || busy} onClick={submit} title="Send">
            <ArrowUp size={19} />
          </button>
        </div>
        <div className="composer-hint">
          <span>
            <span className="kbd">Enter</span> to send · <span className="kbd">Shift+Enter</span> new line
          </span>
          <span className="faint">
            {busy ? 'Nate\'s AI is working on your answer…' : 'Answers cite firm sources'}
          </span>
        </div>
      </div>
    </div>
  );
}

function buildHistory(messages) {
  return messages
    .filter((m) => !m.error && !m.streaming)
    .map((m) =>
      m.role === 'user'
        ? { role: 'user', content: m.text }
        : { role: 'assistant', content: m.answer }
    )
    .slice(-10);
}

export default function Chat({
  messages,
  setMessages,
  busy,
  setBusy,
  settings,
  user,
  conversationId,
  onConversationId,
}) {
  const threadRef = useRef(null);
  const lastUserRef = useRef('');

  const initials = user?.name
    ? user.name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  const scrollDown = () => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  };

  useEffect(() => { scrollDown(); }, [messages, busy]);

  const patchAi = (aiId, patch) => {
    setMessages((m) => m.map((msg) => (msg.id === aiId ? { ...msg, ...patch } : msg)));
  };

  const { revealAnswer, clearReveal } = useAnswerReveal(patchAi);
  const isRevealing = messages.some((m) => m.role === 'ai' && m.streaming);

  useEffect(() => {
    if (messages.length === 0) clearReveal();
  }, [messages.length, clearReveal]);

  const send = async (text, { retryAiId } = {}) => {
    if (busy || isRevealing) return;
    clearReveal();
    lastUserRef.current = text;

    const aiId = retryAiId || `a${Date.now()}`;
    if (retryAiId) {
      patchAi(retryAiId, {
        answer: '',
        error: false,
        streaming: true,
        status: 'refining',
        retryHint: undefined,
        search: undefined,
        timing: undefined,
        ts: now(),
      });
    } else {
      setMessages((m) => [
        ...m,
        { id: `u${Date.now()}`, role: 'user', text, ts: now() },
        {
          id: aiId,
          role: 'ai',
          answer: '',
          status: 'refining',
          retryHint: undefined,
          streaming: true,
          ts: now(),
        },
      ]);
    }

    setBusy(true);

    const historySource = retryAiId
      ? messages.filter((m) => m.id !== retryAiId)
      : messages;
    const body = {
      question: text,
      conversation_id: conversationId || undefined,
      ...(!conversationId ? { chat_history: buildHistory(historySource) } : {}),
      ...requestSettingsPayload(settings),
    };

    try {
      await chatStream(body, {
        onRetry: (attempt, maxRetries) => {
          patchAi(aiId, {
            answer: '',
            error: false,
            streaming: true,
            status: 'refining',
            retryHint: `Retrying (${attempt}/${maxRetries})…`,
            search: undefined,
            timing: undefined,
          });
        },
        onStatus: (phase) => {
          patchAi(aiId, { status: phase, retryHint: undefined, answer: '' });
        },
        onDone: (data) => {
          if (data.conversation_id) onConversationId?.(data.conversation_id);
          revealAnswer(aiId, data);
        },
      });
    } catch (err) {
      patchAi(aiId, {
        answer: formatStreamError(err),
        error: true,
        streaming: false,
        status: null,
        retryHint: undefined,
      });
    } finally {
      setBusy(false);
    }
  };

  const retryFailed = (aiId) => {
    if (!lastUserRef.current || busy) return;
    send(lastUserRef.current, { retryAiId: aiId });
  };

  const regenerate = () => {
    if (!lastUserRef.current || busy || isRevealing) return;
    clearReveal();
    setMessages((m) => (m[m.length - 1]?.role === 'ai' ? m.slice(0, -1) : m));
    send(lastUserRef.current);
  };

  return (
    <div className="chat-wrap">
      <div className="thread scroll" ref={threadRef}>
        {messages.length === 0 && !busy ? (
          <Empty userName={user?.name} onPick={send} />
        ) : (
          <div className="thread-inner">
            {messages.map((m, idx) =>
              m.role === 'user' ? (
                <UserMessage key={m.id} msg={m} initials={initials} />
              ) : (
                <AiMessage
                  key={m.id}
                  msg={m}
                  onRegenerate={
                    idx === messages.length - 1 && !busy && !m.error ? regenerate : undefined
                  }
                  onRetry={
                    m.error && idx === messages.length - 1 && !busy
                      ? () => retryFailed(m.id)
                      : undefined
                  }
                />
              )
            )}
          </div>
        )}
      </div>
      <Composer onSend={send} busy={busy || isRevealing} />
    </div>
  );
}
