/**
 * Map API/network/LLM failures to short, actionable copy (no errno, DNS, stack traces).
 */

const TECHNICAL =
  /getaddrinfo|errno\s*\d+|\[errno|econnrefused|enotfound|eai_again|etimedout|socket|ssl|certificate|traceback|exception:|failed to fetch|networkerror|load failed|net::/i;

function looksTechnical(msg) {
  if (!msg) return true;
  return TECHNICAL.test(msg) || msg.length > 220;
}

/**
 * @param {unknown} err
 * @param {'chat'|'search'|'settings'|'conversations'|'invites'|'generic'} [context]
 * @returns {string}
 */
export function toUserFacingMessage(err, context = 'generic') {
  const status = err?.status;
  const raw = String(err?.message || err || '').trim();
  const lower = raw.toLowerCase();

  if (status === 401) {
    return 'Your session may have expired. Please sign out and sign in again.';
  }
  if (status === 403) {
    return "You don't have permission to do that.";
  }
  if (status === 404 && context === 'conversations') {
    return 'That conversation could not be found.';
  }
  if (status === 429) {
    return 'Too many requests. Please wait a moment and try again.';
  }
  if (status === 502 || status === 503 || status === 504) {
    return context === 'chat'
      ? 'The server is temporarily unavailable. Tap Retry in a moment.'
      : 'The server is temporarily unavailable. Please try again in a moment.';
  }
  if (status >= 500) {
    return 'Something went wrong on our end. Please try again.';
  }

  if (
    err?.network ||
    /getaddrinfo|enotfound|eai_again|11001|econnrefused|connection refused|network error|failed to fetch|fetch failed|load failed/i.test(
      lower
    ) ||
    (err?.name === 'TypeError' && /fetch/i.test(lower))
  ) {
    return "Couldn't reach the server. Check that the API is running and your connection is working.";
  }

  if (/timeout|timed out/i.test(lower)) {
    return context === 'chat'
      ? 'This request timed out. Complex questions can take a while — tap Retry to try again.'
      : 'This request timed out. Please try again.';
  }

  if (/unauthorized|not authenticated|invalid token|jwt|credentials/i.test(lower)) {
    return 'Your session may have expired. Please sign in again.';
  }

  if (/openai|openrouter|rate limit|insufficient_quota|api key/i.test(lower)) {
    return 'The AI service is temporarily unavailable. Please try again shortly.';
  }

  if (/conversation not found/i.test(lower)) {
    return 'That conversation could not be found.';
  }

  if (raw && !looksTechnical(raw)) {
    return raw;
  }

  const byContext = {
    chat: "We couldn't complete your question. Check your connection and tap Retry.",
    search: "Search couldn't complete. Check your connection and try again.",
    settings: "Couldn't update your settings. Please try again.",
    conversations: "Couldn't load conversations. Refresh the page or try again later.",
    invites: "Couldn't send the invitation. Please try again.",
    generic: 'Something went wrong. Please try again.',
  };

  return byContext[context] || byContext.generic;
}

/** @param {unknown} err */
export function isRetryableError(err) {
  if (!err) return false;
  const lower = String(err.message || err).toLowerCase();
  if (
    /timeout|timed out|network|failed to fetch|fetch failed|getaddrinfo|enotfound|econnrefused|eai_again|11001|connection refused|aborted|502|503|504|429/.test(
      lower
    )
  ) {
    return true;
  }
  if (err.status && [502, 503, 504, 429].includes(err.status)) return true;
  if (err.network) return true;
  return err.name === 'TypeError' && /fetch/i.test(lower);
}

/**
 * Normalize a failed fetch into an Error with optional .network flag.
 * @param {unknown} err
 * @returns {Error}
 */
export function normalizeFetchError(err) {
  const e = new Error(err?.message || 'Network error');
  e.cause = err;
  e.network = true;
  e.name = err?.name || 'NetworkError';
  return e;
}
