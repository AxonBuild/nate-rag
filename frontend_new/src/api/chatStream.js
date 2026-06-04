const BASE = import.meta.env.VITE_API_URL || '';

const DEFAULT_MAX_RETRIES = 2;
const RETRY_DELAY_MS = 1500;

let getAuthToken = null;

export function setStreamAuthTokenGetter(fn) {
  getAuthToken = fn;
}

const STATUS_LABELS = {
  refining: 'Refining your question…',
  retrieving: 'Searching the knowledge base…',
  generating: 'Writing answer…',
  verifying: 'Reviewing answer against sources…',
};

export function statusLabel(phase) {
  return STATUS_LABELS[phase] || 'Working…';
}

/** Errors worth an automatic retry (timeouts, gateway, network). */
export function isRetryableError(err) {
  if (!err) return false;
  const msg = String(err.message || err).toLowerCase();
  if (
    /timeout|timed out|network|failed to fetch|econnreset|connection reset|aborted|502|503|504|429/.test(
      msg
    )
  ) {
    return true;
  }
  if (err.status && [502, 503, 504, 429].includes(err.status)) return true;
  return err.name === 'TypeError';
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function chatStreamOnce(body, { onStatus, onToken, onDone, onError } = {}) {
  const headers = { 'Content-Type': 'application/json', Accept: 'text/event-stream' };
  if (getAuthToken) {
    const token = await getAuthToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${BASE}/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });
  } catch (err) {
    throw new Error(err.message || 'Network error');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const d = err.detail;
    const msg = typeof d === 'string' ? d : res.statusText;
    const e = new Error(msg || `HTTP ${res.status}`);
    e.status = res.status;
    throw e;
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error('Streaming not supported in this browser');

  const decoder = new TextDecoder();
  let buffer = '';
  let streamError = null;

  const dispatch = (block) => {
    const lines = block.split('\n');
    let event = 'message';
    let dataStr = '';
    for (const line of lines) {
      if (line.startsWith('event:')) event = line.slice(6).trim();
      else if (line.startsWith('data:')) {
        dataStr += (dataStr ? '\n' : '') + line.slice(line.indexOf(':') + 1).trim();
      }
    }
    if (!dataStr) return;
    let data;
    try {
      data = JSON.parse(dataStr);
    } catch {
      return;
    }
    if (event === 'status') onStatus?.(data.phase, data);
    else if (event === 'token') onToken?.(data.text ?? '');
    else if (event === 'done') onDone?.(data);
    else if (event === 'error') {
      streamError = new Error(data.message || 'Stream failed');
      onError?.(streamError);
    }
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';
      for (const part of parts) {
        if (part.trim()) dispatch(part);
      }
      if (streamError) throw streamError;
    }
    if (buffer.trim()) dispatch(buffer);
    if (streamError) throw streamError;
  } finally {
    reader.releaseLock?.();
  }
}

/**
 * POST /chat/stream — SSE with status, done, error events.
 * Full answer arrives on `done`; UI reveals it with a local typewriter effect.
 * Retries automatically on timeouts and transient failures.
 */
export async function chatStream(body, handlers = {}, { maxRetries = DEFAULT_MAX_RETRIES } = {}) {
  let lastError;
  const attempts = maxRetries + 1;

  for (let attempt = 0; attempt < attempts; attempt++) {
    try {
      if (attempt > 0) {
        handlers.onRetry?.(attempt, maxRetries);
        await sleep(RETRY_DELAY_MS * attempt);
      }
      await chatStreamOnce(body, handlers);
      return;
    } catch (err) {
      lastError = err;
      const canRetry = attempt < maxRetries && isRetryableError(err);
      if (!canRetry) throw err;
    }
  }

  throw lastError;
}
