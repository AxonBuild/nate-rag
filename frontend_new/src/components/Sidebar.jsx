import { MessageSquare, Search, BarChart2, UserPlus, PanelLeft, LogOut, SlidersHorizontal, FileText } from 'lucide-react';
import LogoMark from './LogoMark.jsx';

function NavLink({ id, icon: Icon, label, active, collapsed, onClick }) {
  return (
    <button className={`sb-link${active ? ' active' : ''}`} onClick={onClick} title={collapsed ? label : undefined}>
      <Icon size={18} />
      {!collapsed && <span className="hide-collapsed">{label}</span>}
    </button>
  );
}

export default function Sidebar({ view, setView, collapsed, setCollapsed, onLogout, user, isAdmin }) {
  const nav = [
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'search', icon: Search, label: 'Search' },
    { id: 'retrieval', icon: SlidersHorizontal, label: 'Retrieval' },
    { id: 'prompt', icon: FileText, label: 'System prompt' },
    ...(isAdmin ? [
      { id: 'stats', icon: BarChart2, label: 'Statistics' },
      { id: 'invites', icon: UserPlus, label: 'Invites' },
    ] : []),
  ];

  const roleLabel = isAdmin ? 'Admin · Meeker CPA' : 'Client · Meeker CPA';

  const initials = user?.name
    ? user.name.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2)
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
        <button className="sb-collapse" onClick={() => setCollapsed(!collapsed)} title={collapsed ? 'Expand' : 'Collapse'}>
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
      </div>

      <div className="sb-foot">
        <div className="avatar sm">{initials}</div>
        {!collapsed && (
          <>
            <div className="sb-user-meta hide-collapsed">
              <div className="nm">{user?.name || 'User'}</div>
              <div className="rl">{roleLabel}</div>
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
