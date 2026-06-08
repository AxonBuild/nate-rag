import { normalizeFetchError } from '../utils/userFacingError.js';

const BASE = import.meta.env.VITE_API_URL || '';

let getAuthToken = null;

/** Register Clerk getToken so API calls can send Bearer auth (for when backend enforces it). */
export function setAuthTokenGetter(fn) {
  getAuthToken = fn;
}

async function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (getAuthToken) {
    const token = await getAuthToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function request(path, options = {}) {
  const headers = await authHeaders(options.headers || {});

  let res;
  try {
    res = await fetch(BASE + path, { ...options, headers });
  } catch (err) {
    throw normalizeFetchError(err);
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const d = err.detail;
    const msg = Array.isArray(d)
      ? d.map((x) => x.msg || x.message || String(x)).join(', ')
      : (typeof d === 'string' ? d : d?.message) || res.statusText;
    const e = new Error(msg || `HTTP ${res.status}`);
    e.status = res.status;
    throw e;
  }
  return res.json();
}

async function upload(path, formData) {
  const headers = await authHeaders();
  let res;
  try {
    res = await fetch(BASE + path, { method: 'POST', headers, body: formData });
  } catch (err) {
    throw normalizeFetchError(err);
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const d = err.detail;
    const msg = Array.isArray(d)
      ? d.map((x) => x.msg || x.message || String(x)).join(', ')
      : (typeof d === 'string' ? d : d?.message) || res.statusText;
    const e = new Error(msg || `HTTP ${res.status}`);
    e.status = res.status;
    throw e;
  }
  return res.json();
}

const json = (body) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

export const api = {
  chat:   (body) => request('/chat/',   json(body)),
  search: (body) => request('/search/', json(body)),
  config: ()     => request('/system/config/'),
  inviteUser: (body) => request('/admin/invitations', json(body)),
  listInvitations: () => request('/admin/invitations'),
  listConversations: () => request('/conversations'),
  createConversation: (body = {}) =>
    request('/conversations', { method: 'POST', ...json(body) }),
  getConversation: (id) => request(`/conversations/${id}`),
  deleteConversation: (id) =>
    request(`/conversations/${id}`, { method: 'DELETE' }),
  getSystemPrompt: () => request('/settings/system-prompt'),
  saveSystemPrompt: (body) =>
    request('/settings/system-prompt', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  ingestTranscript: (formData) => upload('/ingest/transcript', formData),
  previewQaColumns: (formData) => upload('/ingest/qa/preview', formData),
  ingestQa: (formData) => upload('/ingest/qa', formData),
  ingestDocument: (formData) => upload('/ingest/document', formData),
};
