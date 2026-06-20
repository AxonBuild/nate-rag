import { useState, useEffect, useCallback } from 'react';
import { Mail, UserPlus, RefreshCw, Users, Trash2, Send } from 'lucide-react';
import { api } from '../api/client.js';
import { toUserFacingMessage } from '../utils/userFacingError.js';

function displayRole(role) {
  if (role === 'admin') return 'Admin';
  return 'Member';
}

function formatDate(ts) {
  if (!ts) return '—';
  const d = typeof ts === 'number' ? new Date(ts) : new Date(ts);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function Invites() {
  const [email, setEmail] = useState('');
  const [role, setRole] = useState('client');
  const [sending, setSending] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [list, setList] = useState([]);
  const [loadingList, setLoadingList] = useState(true);
  const [resendingId, setResendingId] = useState(null);

  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const loadInvites = useCallback(async () => {
    setLoadingList(true);
    try {
      const data = await api.listInvitations();
      setList(data.invitations || []);
    } catch (err) {
      setError(toUserFacingMessage(err, 'invites'));
    } finally {
      setLoadingList(false);
    }
  }, []);

  const loadUsers = useCallback(async () => {
    setLoadingUsers(true);
    try {
      const data = await api.listUsers();
      setUsers(data.users || []);
    } catch (err) {
      setError(toUserFacingMessage(err, 'users'));
    } finally {
      setLoadingUsers(false);
    }
  }, []);

  useEffect(() => { loadInvites(); loadUsers(); }, [loadInvites, loadUsers]);

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
      setError(toUserFacingMessage(err, 'invites'));
    } finally {
      setSending(false);
    }
  };

  const resendInvite = async (inv) => {
    setResendingId(inv.id);
    setError('');
    setMessage('');
    try {
      await api.resendInvitation(inv.id, {
        email: inv.email_address,
        role: inv.role || 'client',
      });
      setMessage(`Invitation resent to ${inv.email_address}`);
      await loadInvites();
    } catch (err) {
      setError(toUserFacingMessage(err, 'invites'));
    } finally {
      setResendingId(null);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await api.deleteUser(deleteTarget.id);
      setUsers((prev) => prev.filter((u) => u.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch (err) {
      setError(toUserFacingMessage(err, 'delete user'));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="page-scroll scroll">
      <div className="page-inner fade-in">
        <h1 className="page-h">User Management</h1>
        <p className="page-sub">
          Invite new users, view all accounts, and revoke access.
        </p>

        {/* ---- Invite form ---- */}
        <div className="panel invite-form-panel">
          <form onSubmit={sendInvite}>
            <div className="invite-field">
              <label htmlFor="invite-email">Email address</label>
              <input
                id="invite-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                required
              />
            </div>
            <div className="invite-field">
              <label htmlFor="invite-role">Role</label>
              <select id="invite-role" className="invite-select" value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="client">Member</option>
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

        {/* ---- Pending invitations ---- */}
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
                <span className="pill doc">{displayRole(inv.role || 'client')}</span>
                <span className="mono faint" style={{ fontSize: 11 }}>{inv.status}</span>
                <button
                  type="button"
                  className="icon-btn bordered"
                  title="Resend invitation"
                  onClick={() => resendInvite(inv)}
                  disabled={resendingId === inv.id}
                >
                  <Send size={14} />
                  {resendingId === inv.id ? 'Sending…' : 'Resend'}
                </button>
              </li>
            ))}
          </ul>
        )}

        {/* ---- All users ---- */}
        <div className="results-head" style={{ marginTop: 36 }}>
          <span className="rh" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Users size={16} /> All users
          </span>
          <button type="button" className="icon-btn bordered" onClick={loadUsers} disabled={loadingUsers} title="Refresh">
            <RefreshCw size={15} />
          </button>
        </div>

        {loadingUsers ? (
          <p className="muted" style={{ fontSize: 14 }}>Loading…</p>
        ) : users.length === 0 ? (
          <p className="muted" style={{ fontSize: 14 }}>No users found.</p>
        ) : (
          <ul className="invite-list">
            {users.map((u) => (
              <li key={u.id} className="invite-row">
                <span className="invite-email">
                  {[u.first_name, u.last_name].filter(Boolean).join(' ') || u.email_address}
                </span>
                {u.first_name && (
                  <span className="mono faint" style={{ fontSize: 12 }}>{u.email_address}</span>
                )}
                <span className="pill doc">{displayRole(u.role)}</span>
                <span className="mono faint" style={{ fontSize: 11 }}>
                  Joined {formatDate(u.created_at)}
                </span>
                <button
                  type="button"
                  className="icon-btn"
                  style={{ color: '#b84a4a' }}
                  title="Delete user"
                  onClick={() => setDeleteTarget(u)}
                >
                  <Trash2 size={15} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* ---- Delete confirmation dialog ---- */}
      {deleteTarget && (
        <div className="confirm-overlay" onClick={() => !deleting && setDeleteTarget(null)}>
          <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
            <h2 className="confirm-title">Delete user</h2>
            <p className="confirm-message">
              This will permanently delete{' '}
              <strong>{deleteTarget.first_name || deleteTarget.email_address}</strong>'s
              account and revoke their access. This cannot be undone.
            </p>
            <div className="confirm-actions">
              <button className="confirm-btn cancel" onClick={() => setDeleteTarget(null)} disabled={deleting}>
                Cancel
              </button>
              <button className="confirm-btn danger" onClick={confirmDelete} disabled={deleting}>
                {deleting ? 'Deleting…' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
