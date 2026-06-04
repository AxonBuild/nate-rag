import { useState, useEffect, useCallback } from 'react';
import { Mail, UserPlus, RefreshCw } from 'lucide-react';
import { api } from '../api/client.js';

export default function Invites() {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('client');
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [list, setList] = useState([]);
  const [loadingList, setLoadingList] = useState(true);

  const loadInvites = useCallback(async () => {
    setLoadingList(true);
    try {
      const data = await api.listInvitations();
      setList(data.invitations || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingList(false);
    }
  }, []);

  useEffect(() => { loadInvites(); }, [loadInvites]);

  const sendInvite = async (e) => {
    e.preventDefault();
    const trimmed = email.trim();
    if (!trimmed) return;
    setSending(true);
    setError('');
    setMessage('');
    try {
      await api.inviteUser({ email: trimmed, role });
      setMessage(`Invitation sent to ${trimmed}`);
      setEmail('');
      loadInvites();
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="page-scroll scroll">
      <div className="page-inner fade-in">
        <h1 className="page-h">Invite users</h1>
        <p className="page-sub">
          Send email invitations via Clerk. New users sign up with the role you choose below.
        </p>

        <div className="panel invite-form-panel">
          <form onSubmit={sendInvite}>
            <div className="invite-field">
              <label htmlFor="invite-email">Email address</label>
              <input
                id="invite-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="client@example.com"
                required
              />
            </div>
            <div className="invite-field">
              <label htmlFor="invite-role">Role</label>
              <select id="invite-role" className="invite-select" value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="client">Client (normal user)</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            {error && <p className="invite-error">{error}</p>}
            {message && <p className="invite-success">{message}</p>}
            <button type="submit" className="invite-submit" disabled={sending || !email.trim()}>
              <UserPlus size={16} />
              {sending ? 'Sending…' : 'Send invitation'}
            </button>
          </form>
        </div>

        <div className="results-head" style={{ marginTop: 28 }}>
          <span className="rh">Pending invitations</span>
          <button type="button" className="icon-btn bordered" onClick={loadInvites} disabled={loadingList} title="Refresh">
            <RefreshCw size={15} />
          </button>
        </div>

        {loadingList ? (
          <p className="muted" style={{ fontSize: 14 }}>Loading…</p>
        ) : list.length === 0 ? (
          <p className="muted" style={{ fontSize: 14 }}>No pending invitations.</p>
        ) : (
          <ul className="invite-list">
            {list.map((inv) => (
              <li key={inv.id} className="invite-row">
                <Mail size={15} style={{ color: 'var(--text-3)', flexShrink: 0 }} />
                <span className="invite-email">{inv.email_address}</span>
                <span className="pill doc">{inv.role || 'client'}</span>
                <span className="mono faint" style={{ fontSize: 11 }}>{inv.status}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
