import {
  MessageSquare,
  Search,
  UserPlus,
  PanelLeft,
  LogOut,
  SlidersHorizontal,
  FileText,
  Plus,
  Trash2,
  Upload,
} from 'lucide-react';
import LogoMark from './LogoMark.jsx';

function NavLink({ id, icon: Icon, label, active, collapsed, onClick }) {
  return (
    <button
      className={`sb-link${active ? ' active' : ''}`}
      onClick={onClick}
      title={collapsed ? label : undefined}
    >
      <Icon size={18} />
      {!collapsed && <span className="hide-collapsed">{label}</span>}
    </button>
  );
}

export default function Sidebar({
  view,
  setView,
  collapsed,
  setCollapsed,
  onLogout,
  user,
  isAdmin,
  conversations = [],
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  chatsLoading,
  deletingConversationId,
}) {
  const nav = [
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'search', icon: Search, label: 'Search' },
    { id: 'ingest', icon: Upload, label: 'Ingest' },
    { id: 'retrieval', icon: SlidersHorizontal, label: 'Retrieval' },
    { id: 'prompt', icon: FileText, label: 'System prompt' },
    ...(isAdmin ? [{ id: 'invites', icon: UserPlus, label: 'Invitations' }] : []),
  ];

  const roleLabel = isAdmin ? 'Admin' : null;

  const initials = user?.name
    ? user.name
        .split(' ')
        .map((w) => w[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'U';

  return (
    <aside className={`sidebar scroll${collapsed ? ' collapsed' : ''}`}>
      <div className="sb-top">
        <LogoMark size={34} />
        {!collapsed && (
          <div className="sb-brand-text hide-collapsed">
            <span className="name">Nate&apos;s AI</span>
            <span className="sub">Tax · Real Estate</span>
          </div>
        )}
        <button
          className="sb-collapse"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          <PanelLeft size={17} />
        </button>
      </div>

      <div className="sb-scroll scroll">
        <nav className="sb-nav">
          {nav.map((n) => (
            <NavLink
              key={n.id}
              {...n}
              active={view === n.id}
              collapsed={collapsed}
              onClick={() => setView(n.id)}
            />
          ))}
        </nav>

        {!collapsed && (
          <div className="sb-chats hide-collapsed">
            <div className="sb-chats-head">
              <span>Chats</span>
              <button
                type="button"
                className="sb-new-chat"
                title="New chat"
                onClick={onNewChat}
              >
                <Plus size={15} />
              </button>
            </div>
            <div className="sb-chats-list">
              {chatsLoading && conversations.length === 0 ? (
                <p className="sb-chats-empty">Loading…</p>
              ) : conversations.length === 0 ? (
                <p className="sb-chats-empty">No conversations yet</p>
              ) : (
                conversations.map((c) => (
                  <div
                    key={c.id}
                    className={`sb-chat-row${
                      c.id === activeConversationId ? ' active' : ''
                    }`}
                  >
                    <button
                      type="button"
                      className="sb-chat-item"
                      title={c.title}
                      onClick={() => onSelectConversation(c.id)}
                      disabled={deletingConversationId === c.id}
                    >
                      <MessageSquare size={14} />
                      <span className="sb-chat-title">{c.title}</span>
                    </button>
                    <button
                      type="button"
                      className="sb-chat-delete"
                      title="Delete chat"
                      aria-label={`Delete ${c.title}`}
                      disabled={deletingConversationId === c.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation?.(c.id);
                      }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      <div className="sb-foot">
        <div className="avatar sm">{initials}</div>
        {!collapsed && (
          <>
            <div className="sb-user-meta hide-collapsed">
              <div className="nm">{user?.name || user?.email || 'Account'}</div>
              {roleLabel ? <div className="rl">{roleLabel}</div> : null}
            </div>
            <button className="sb-logout hide-collapsed" title="Log out" onClick={onLogout}>
              <LogOut size={17} />
            </button>
          </>
        )}
      </div>
    </aside>
  );
}
