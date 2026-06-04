import { useState, useEffect } from 'react';
import { useUser, useAuth, useClerk } from '@clerk/clerk-react';
import { Plus, Trash2 } from 'lucide-react';
import Login from './screens/Login.jsx';
import Chat from './screens/Chat.jsx';
import Search from './screens/Search.jsx';
import Stats from './screens/Stats.jsx';
import Invites from './screens/Invites.jsx';
import Sidebar from './components/Sidebar.jsx';
import ThemeToggle from './components/ThemeToggle.jsx';
import AuthTokenBridge from './components/AuthTokenBridge.jsx';
import { getRoleFromUser, ROLES } from './hooks/useAppRole.js';

const THEME_KEY = 'nate_ai_theme';

const TITLES = {
  chat:   { title: 'New Conversation', crumb: 'Chat' },
  search: { title: 'Search', crumb: 'Knowledge Base' },
  stats:   { title: 'Statistics', crumb: 'System' },
  invites: { title: 'Invite users', crumb: 'Admin' },
};

const DEFAULT_ADV = { l0: '', l1: '', l2: '', sys: '' };

function clerkDisplayUser(user) {
  if (!user) return { name: 'User', email: '' };
  const name =
    user.fullName ||
    [user.firstName, user.lastName].filter(Boolean).join(' ') ||
    user.username ||
    'User';
  const role = getRoleFromUser(user);
  return {
    name,
    email: user.primaryEmailAddress?.emailAddress || '',
    role,
    isAdmin: role === ROLES.ADMIN,
  };
}

function TopBar({ view, theme, toggleTheme, messages, onClear, onNew }) {
  const t = TITLES[view] || TITLES.chat;
  const lastUser = [...messages].reverse().find((m) => m.role === 'user');
  const convoTitle =
    view === 'chat' && messages.length > 0
      ? (lastUser?.text?.slice(0, 48) || t.title) + (lastUser?.text?.length > 48 ? '…' : '')
      : t.title;

  return (
    <header className="topbar">
      <span className="crumb">{t.crumb}</span>
      <span className="crumb">/</span>
      <span className="title">{convoTitle}</span>
      <div className="topbar-actions">
        {view === 'chat' && messages.length > 0 && (
          <button type="button" className="icon-btn bordered" onClick={onClear}>
            <Trash2 size={15} />
            Clear chat
          </button>
        )}
        {view === 'chat' && (
          <button type="button" className="icon-btn bordered" onClick={onNew}>
            <Plus size={15} />
            New
          </button>
        )}
        <ThemeToggle theme={theme} onToggle={toggleTheme} />
      </div>
    </header>
  );
}

function AppShell({ user, onLogout, isAdmin }) {
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) || 'dark');
  const [view, setView] = useState('chat');
  const [collapsed, setCollapsed] = useState(false);
  const [filters, setFilters] = useState({ topic: 'All', docType: 'All' });
  const [advanced, setAdvanced] = useState(DEFAULT_ADV);
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

  const clearChat = () => {
    setMessages([]);
    setBusy(false);
  };

  useEffect(() => {
    if (!isAdmin && (view === 'stats' || view === 'invites')) setView('chat');
  }, [isAdmin, view]);

  let screen;
  if (view === 'chat') {
    screen = (
      <Chat
        messages={messages}
        setMessages={setMessages}
        busy={busy}
        setBusy={setBusy}
        filters={filters}
        advanced={advanced}
        user={user}
        isAdmin={isAdmin}
      />
    );
  } else if (view === 'search') {
    screen = <Search filters={filters} isAdmin={isAdmin} />;
  } else if (view === 'invites' && isAdmin) {
    screen = <Invites />;
  } else if (view === 'stats' && isAdmin) {
    screen = <Stats />;
  } else {
    screen = null;
  }

  return (
    <div className="app-root">
      <AuthTokenBridge />
      <Sidebar
        view={view}
        setView={setView}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        filters={filters}
        setFilters={setFilters}
        advanced={advanced}
        setAdvanced={setAdvanced}
        onLogout={onLogout}
        user={user}
        isAdmin={isAdmin}
      />
      <div className="main">
        <TopBar
          view={view}
          theme={theme}
          toggleTheme={toggleTheme}
          messages={messages}
          onClear={clearChat}
          onNew={clearChat}
        />
        {screen}
      </div>
    </div>
  );
}

export default function App() {
  const { isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();
  const { signOut } = useClerk();
  const [theme, setTheme] = useState(() => localStorage.getItem(THEME_KEY) || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

  const handleLogout = () => signOut();

  if (!isLoaded) {
    return (
      <div className="login-root">
        <p className="muted" style={{ zIndex: 2 }}>Loading…</p>
      </div>
    );
  }

  if (!isSignedIn) {
    return <Login theme={theme} toggleTheme={toggleTheme} />;
  }

  const displayUser = clerkDisplayUser(user);
  return (
    <AppShell
      user={displayUser}
      isAdmin={displayUser.isAdmin}
      onLogout={handleLogout}
    />
  );
}
