import { useState, useRef, useEffect } from 'react';
import { Sparkles, ArrowUp, Copy, Check, RefreshCw, Layers, Clock } from 'lucide-react';
import Markdown from '../components/Markdown.jsx';
import Disclosure from '../components/Disclosure.jsx';
import { SourceList } from '../components/SourceCard.jsx';
import Performance from '../components/Performance.jsx';
import Refinement from '../components/Refinement.jsx';
import { SUGGESTIONS } from '../constants/suggestions.js';
import { api } from '../api/client.js';
import { filterPayload } from '../utils/filters.js';

const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

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

function AiMessage({ msg, onRegenerate, isAdmin }) {
  const [shown, setShown] = useState(msg.streaming ? '' : msg.answer);
  const [done, setDone] = useState(!msg.streaming);

  useEffect(() => {
    if (!msg.streaming) {
      setShown(msg.answer);
      setDone(true);
      return;
    }
    let i = 0;
    const full = msg.answer || '';
    let timer;
    const step = () => {
      i += Math.max(2, Math.round(full.length / 280));
      setShown(full.slice(0, i));
      if (i < full.length) timer = setTimeout(step, 14);
      else { setShown(full); setDone(true); }
    };
    timer = setTimeout(step, 30);
    return () => clearTimeout(timer);
  }, [msg.id, msg.streaming, msg.answer]);

  const search = msg.search || {};
  const results = search.results || [];
  const totalMs = msg.timing?.total_chat_ms;

  return (
    <div className="msg ai msg-enter">
      <div className="mavatar"><Sparkles size={18} /></div>
      <div className="msg-body">
        <div className="msg-meta">
          <span className="who">Nate AI</span>
          <span className="ts">{msg.ts}</span>
        </div>
        {msg.error ? (
          <div className="ai-content" style={{ color: '#e05a5a' }}>{msg.answer}</div>
        ) : done ? (
          <Markdown text={shown} />
        ) : (
          <div className="ai-content" style={{ whiteSpace: 'pre-wrap' }}>
            {shown}
            <span className="cursor-blink" />
          </div>
        )}
        {done && !msg.error && (
          <>
            <div className="msg-actions">
              <CopyBtn text={msg.answer} />
              {onRegenerate && (
                <button type="button" className="icon-btn" title="Regenerate" onClick={onRegenerate}>
                  <RefreshCw size={15} />
                </button>
              )}
            </div>
            {msg.search && (
              <div style={{ marginTop: 14 }}>
                {results.length > 0 && (
                  <Disclosure icon={Layers} label="Sources" count={`${results.length} documents`}>
                    <SourceList results={results} />
                  </Disclosure>
                )}
                {(search.refined_query || (search.keywords || []).length > 0) && (
                  <Disclosure icon={Sparkles} label="Query refinement">
                    <Refinement refined={search.refined_query} keywords={search.keywords} />
                  </Disclosure>
                )}
                {isAdmin && msg.timing && (
                  <Disclosure
                    icon={Clock}
                    label="Performance"
                    count={totalMs != null ? `${(totalMs / 1000).toFixed(2)}s` : undefined}
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

function Typing() {
  return (
    <div className="msg ai msg-enter">
      <div className="mavatar"><Sparkles size={18} /></div>
      <div className="msg-body">
        <div className="msg-meta">
          <span className="who">Nate AI</span>
          <span className="muted" style={{ fontSize: 12 }}>searching the knowledge base…</span>
        </div>
        <div className="typing"><span /><span /><span /></div>
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
          <span className="faint">{busy ? 'Nate is responding…' : 'Answers cite firm sources'}</span>
        </div>
      </div>
    </div>
  );
}

function buildHistory(messages) {
  return messages
    .filter((m) => !m.error)
    .map((m) =>
      m.role === 'user'
        ? { role: 'user', content: m.text }
        : { role: 'assistant', content: m.answer }
    )
    .slice(-10);
}

export default function Chat({ messages, setMessages, busy, setBusy, filters, advanced, user, isAdmin }) {
  const threadRef = useRef(null);
  const lastUserRef = useRef('');

  const initials = user?.name
    ? user.name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  const scrollDown = () => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  };

  useEffect(() => { scrollDown(); }, [messages.length, busy]);

  const send = async (text, { replaceLastAi = false } = {}) => {
    if (busy) return;
    lastUserRef.current = text;

    if (!replaceLastAi) {
      setMessages((m) => [...m, { id: `u${Date.now()}`, role: 'user', text, ts: now() }]);
    }

    setBusy(true);
    try {
      const body = {
        question: text,
        chat_history: buildHistory(replaceLastAi ? messages.slice(0, -1) : messages),
        ...filterPayload(filters),
      };
      const sys = advanced?.sys?.trim();
      if (sys) body.system_prompt = sys;

      const data = await api.chat(body);
      const aMsg = {
        id: `a${Date.now()}`,
        role: 'ai',
        answer: data.answer || '',
        search: data.search,
        timing: data.timing,
        ts: now(),
        streaming: true,
      };

      if (replaceLastAi) {
        setMessages((m) => [...m.slice(0, -1), aMsg]);
      } else {
        setMessages((m) => [...m, aMsg]);
      }
    } catch (err) {
      const errMsg = {
        id: `a${Date.now()}`,
        role: 'ai',
        answer: `Something went wrong: ${err.message}`,
        error: true,
        ts: now(),
        streaming: false,
      };
      if (replaceLastAi) {
        setMessages((m) => [...m.slice(0, -1), errMsg]);
      } else {
        setMessages((m) => [...m, errMsg]);
      }
    } finally {
      setBusy(false);
    }
  };

  const regenerate = () => {
    if (!lastUserRef.current || busy) return;
    setMessages((m) => (m[m.length - 1]?.role === 'ai' ? m.slice(0, -1) : m));
    send(lastUserRef.current, { replaceLastAi: false });
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
                  isAdmin={isAdmin}
                  onRegenerate={idx === messages.length - 1 && !busy ? regenerate : undefined}
                />
              )
            )}
            {busy && <Typing key="typing" />}
          </div>
        )}
      </div>
      <Composer onSend={send} busy={busy} />
    </div>
  );
}
