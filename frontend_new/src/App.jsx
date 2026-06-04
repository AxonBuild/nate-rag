import { useState, useEffect } from 'react';
import { useUser, useAuth, useClerk } from '@clerk/clerk-react';
import { Plus, Trash2 } from 'lucide-react';
import Login from './screens/Login.jsx';
import Chat from './screens/Chat.jsx';
import Search from './screens/Search.jsx';
import Stats from './screens/Stats.jsx';
import Invites from './screens/Invites.jsx';
import Retrieval from './screens/Retrieval.jsx';
import SystemPrompt from './screens/SystemPrompt.jsx';
import Sidebar from './components/Sidebar.jsx';
import ConfirmDialog from './components/ConfirmDialog.jsx';
import ThemeToggle from './components/ThemeToggle.jsx';
import AuthTokenBridge from './components/AuthTokenBridge.jsx';
import { api } from './api/client.js';
import { getRoleFromUser, ROLES } from './hooks/useAppRole.js';
import { apiMessagesToUi } from './utils/chatMessages.js';
import { loadSettings, saveSettings } from './utils/settings.js';

const THEME_KEY = 'nate_ai_theme';

const TITLES = {
  chat: { title: 'New Conversation', crumb: 'Chat' },
  search: { title: 'Search', crumb: 'Knowledge Base' },
  retrieval: { title: 'Retrieval', crumb: 'Settings' },
  prompt: { title: 'System prompt', crumb: 'Settings' },
  stats: { title: 'Statistics', crumb: 'System' },
  invites: { title: 'Invite users', crumb: 'Admin' },
};

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

function TopBar({ view, theme, toggleTheme, messages, onClear, onNew, conversationTitle }) {
  const t = TITLES[view] || TITLES.chat;
  const lastUser = [...messages].reverse().find((m) => m.role === 'user');
  const convoTitle =
    view === 'chat' && conversationTitle
      ? conversationTitle
      : view === 'chat' && messages.length > 0
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
  const [settings, setSettingsState] = useState(() => loadSettings());
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [chatsLoading, setChatsLoading] = useState(true);
  const [loadingConversation, setLoadingConversation] = useState(false);
  const [deletingConversationId, setDeletingConversationId] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const setSettings = (updater) => {
    setSettingsState((prev) => {
      const next = typeof updater === 'function' ? updater(prev) : updater;
      saveSettings(next);
      return next;
    });
  };

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggleTheme = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'));

  const refreshConversations = async () => {
    try {
      const list = await api.listConversations();
      setConversations(list);
    } catch (e) {
      console.error('Failed to load conversations', e);
    }
  };

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setChatsLoading(true);
      try {
        const list = await api.listConversations();
        if (!cancelled) setConversations(list);
      } catch (e) {
        console.error('Failed to load conversations', e);
      } finally {
        if (!cancelled) setChatsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const startNewChat = () => {
    setView('chat');
    setActiveConversationId(null);
    setMessages([]);
    setBusy(false);
  };

  const selectConversation = async (id) => {
    if (loadingConversation || busy) return;
    setView('chat');
    setActiveConversationId(id);
    setLoadingConversation(true);
    try {
      const detail = await api.getConversation(id);
      setMessages(apiMessagesToUi(detail.messages));
    } catch (e) {
      console.error('Failed to load conversation', e);
    } finally {
      setLoadingConversation(false);
    }
  };

  const handleConversationId = (id) => {
    if (id) setActiveConversationId(id);
    refreshConversations();
  };

  const activeConversation = conversations.find((c) => c.id === activeConversationId);
  const conversationTitle = activeConversation?.title;

  const requestDeleteConversation = (id) => {
    if (!id || busy || deletingConversationId) return;
    const conv = conversations.find((c) => c.id === id);
    setDeleteConfirm({
      id,
      title: conv?.title || conversationTitle || 'this conversation',
    });
  };

  const deleteConversation = async (id) => {
    if (!id || busy || deletingConversationId) return false;
    setDeletingConversationId(id);
    try {
      await api.deleteConversation(id);
      if (activeConversationId === id) {
        setActiveConversationId(null);
        setMessages([]);
        setBusy(false);
      }
      await refreshConversations();
      return true;
    } catch (e) {
      console.error('Failed to delete conversation', e);
      return false;
    } finally {
      setDeletingConversationId(null);
    }
  };

  const confirmDeleteConversation = async () => {
    if (!deleteConfirm) return;
    const ok = await deleteConversation(deleteConfirm.id);
    if (ok) setDeleteConfirm(null);
  };

  const clearChat = () => {
    if (activeConversationId) {
      requestDeleteConversation(activeConversationId);
      return;
    }
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
        busy={busy || loadingConversation}
        setBusy={setBusy}
        settings={settings}
        user={user}
        conversationId={activeConversationId}
        onConversationId={handleConversationId}
      />
    );
  } else if (view === 'search') {
    screen = <Search settings={settings} />;
  } else if (view === 'retrieval') {
    screen = <Retrieval settings={settings} setSettings={setSettings} />;
  } else if (view === 'prompt') {
    screen = <SystemPrompt settings={settings} setSettings={setSettings} />;
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
        onLogout={onLogout}
        user={user}
        isAdmin={isAdmin}
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={selectConversation}
        onNewChat={startNewChat}
        onDeleteConversation={requestDeleteConversation}
        chatsLoading={chatsLoading}
        deletingConversationId={deletingConversationId}
      />
      <div className="main">
        <TopBar
          view={view}
          theme={theme}
          toggleTheme={toggleTheme}
          messages={messages}
          onClear={clearChat}
          onNew={startNewChat}
          conversationTitle={conversationTitle}
        />
        {screen}
      </div>
      <ConfirmDialog
        open={Boolean(deleteConfirm)}
        title="Delete conversation?"
        message={
          deleteConfirm
            ? `“${deleteConfirm.title}” will be permanently removed. This cannot be undone.`
            : ''
        }
        confirmLabel="Delete"
        busy={Boolean(deleteConfirm && deletingConversationId === deleteConfirm.id)}
        onConfirm={confirmDeleteConversation}
        onCancel={() => {
          if (!deletingConversationId) setDeleteConfirm(null);
        }}
      />
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
