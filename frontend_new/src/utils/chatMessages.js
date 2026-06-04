/** Map API conversation messages to Chat UI message shape. */
export function formatMessageTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export function apiMessagesToUi(messages = []) {
  return messages.map((m) => {
    if (m.role === 'user') {
      return {
        id: m.id,
        role: 'user',
        text: m.content,
        ts: formatMessageTime(m.created_at),
      };
    }
    const meta = m.metadata || {};
    return {
      id: m.id,
      role: 'ai',
      answer: m.content,
      search: meta.search,
      timing: meta.timing,
      verification: meta.verification ?? null,
      ts: formatMessageTime(m.created_at),
    };
  });
}
