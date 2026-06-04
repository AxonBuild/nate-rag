import { useState } from 'react';
import { MessageSquare, Search, BarChart2, UserPlus, ChevronRight, PanelLeft, LogOut } from 'lucide-react';
import LogoMark from './LogoMark.jsx';

const TOPICS = ['All','Firm Guidelines','General Strategy','Real Estate Rules','Maximizing Deductions','STR Loophole','REPS','Cost Segs','1031s','Entity Selection','Paying Children & Augusta Rule','QOZs','S Corps','DSTs','Research'];
const DOC_TYPES = ['All','Guide','Outline','Script','SEO','PDF','Research'];

function NavLink({ id, icon: Icon, label, active, collapsed, onClick }) {
  return (
    <button className={`sb-link${active ? ' active' : ''}`} onClick={onClick} title={collapsed ? label : undefined}>
      <Icon size={18} />
      {!collapsed && <span className="hide-collapsed">{label}</span>}
    </button>
  );
}

function Group({ title, open, onToggle, children }) {
  return (
    <div className="sb-group">
      <button className={`sb-group-head${open ? ' open' : ''}`} onClick={onToggle}>
        <span>{title}</span>
        <span className="chev"><ChevronRight size={13} /></span>
      </button>
      <div className={`sb-group-body${open ? ' open' : ''}`}>
        <div><div className="sb-group-inner">{children}</div></div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <div className="field-label">{label}</div>
      {children}
    </div>
  );
}

const DEFAULT_ADV = { l0: '', l1: '', l2: '', sys: '' };

export default function Sidebar({ view, setView, collapsed, setCollapsed, filters, setFilters, onLogout, user, advanced, setAdvanced, isAdmin }) {
  const [openFilters, setOpenFilters] = useState(true);
  const [openAdv, setOpenAdv] = useState(false);

  const nav = [
    { id: 'chat',   icon: MessageSquare, label: 'Chat' },
    { id: 'search', icon: Search,        label: 'Search' },
    ...(isAdmin ? [
      { id: 'stats', icon: BarChart2, label: 'Statistics' },
      { id: 'invites', icon: UserPlus, label: 'Invites' },
    ] : []),
  ];

  const roleLabel = isAdmin ? 'Admin · Meeker CPA' : 'Client · Meeker CPA';

  const initials = user?.name
    ? user.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  return (
    <aside className={`sidebar scroll${collapsed ? ' collapsed' : ''}`}>
      <div className="sb-top">
        <LogoMark size={34} />
        {!collapsed && (
          <div className="sb-brand-text hide-collapsed">
            <span className="name">Nate AI</span>
            <span className="sub">Tax · Real Estate</span>
          </div>
        )}
        <button className="sb-collapse" onClick={() => setCollapsed(!collapsed)} title={collapsed ? 'Expand' : 'Collapse'}>
          <PanelLeft size={17} />
        </button>
      </div>

      <div className="sb-scroll scroll">
        <nav className="sb-nav">
          {nav.map(n => (
            <NavLink key={n.id} {...n} active={view === n.id} collapsed={collapsed} onClick={() => setView(n.id)} />
          ))}
        </nav>

        {!collapsed && (
          <>
            <Group title="Filters" open={openFilters} onToggle={() => setOpenFilters(!openFilters)}>
              <Field label="Topic">
                <select className="sb-select" value={filters.topic} onChange={e => setFilters({ ...filters, topic: e.target.value })}>
                  {TOPICS.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </Field>
              <Field label="Doc Type">
                <select className="sb-select" value={filters.docType} onChange={e => setFilters({ ...filters, docType: e.target.value })}>
                  {DOC_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </Field>
              {(filters.topic !== 'All' || filters.docType !== 'All') && (
                <button className="linkbtn" onClick={() => setFilters({ topic: 'All', docType: 'All' })}>Clear filters</button>
              )}
            </Group>

            {isAdmin && (
              <Group title="Advanced" open={openAdv} onToggle={() => setOpenAdv(!openAdv)}>
                <div className="sb-help" style={{ marginTop: 0 }}>Power-user retrieval tuning. Defaults work for most queries.</div>
                <div className="adv-row">
                  <Field label="L0 pages">
                    <input className="sb-input" type="number" placeholder="5" value={advanced.l0} onChange={e => setAdvanced({ ...advanced, l0: e.target.value })} />
                  </Field>
                  <Field label="L1 paras">
                    <input className="sb-input" type="number" placeholder="10" value={advanced.l1} onChange={e => setAdvanced({ ...advanced, l1: e.target.value })} />
                  </Field>
                  <Field label="L2 final">
                    <input className="sb-input" type="number" placeholder="5" value={advanced.l2} onChange={e => setAdvanced({ ...advanced, l2: e.target.value })} />
                  </Field>
                </div>
                <button className="linkbtn" onClick={() => setAdvanced(DEFAULT_ADV)}>Reset to defaults</button>
                <Field label="System Prompt Override">
                  <textarea className="sb-textarea" placeholder="Custom instructions…" value={advanced.sys} onChange={e => setAdvanced({ ...advanced, sys: e.target.value })} />
                </Field>
                <button className="linkbtn" onClick={() => setAdvanced({ ...advanced, sys: '' })}>Clear</button>
              </Group>
            )}
          </>
        )}
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
