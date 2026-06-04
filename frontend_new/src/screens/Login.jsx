import { useMemo } from 'react';
import { SignIn, SignUp } from '@clerk/clerk-react';
import { Sun, Moon, Check } from 'lucide-react';
import LogoMark from '../components/LogoMark.jsx';
import { hasInviteTicket } from '../utils/clerkInvite.js';

const clerkAppearance = {
  variables: {
    colorPrimary: '#C9A84C',
    colorBackground: 'transparent',
    colorText: '#EAF0F7',
    colorTextSecondary: '#A9BBCF',
    colorInputBackground: '#0E1E32',
    colorInputText: '#EAF0F7',
    borderRadius: '10px',
    fontSize: '14px',
  },
  elements: {
    rootBox: { width: '100%' },
    cardBox: { width: '100%', boxShadow: 'none', overflow: 'visible' },
    card: {
      background: 'transparent',
      boxShadow: 'none',
      border: 'none',
      padding: 0,
      gap: '16px',
      overflow: 'visible',
    },
    main: { gap: '16px', overflow: 'visible' },
    header: { display: 'none' },
    headerTitle: { display: 'none' },
    headerSubtitle: { display: 'none' },
    logoBox: { display: 'none' },
    footer: { display: 'none' },
    footerAction: { display: 'none' },
    socialButtonsRoot: { display: 'none' },
    socialButtons: { display: 'none' },
    dividerRow: { display: 'none' },
    formButtonPrimary: {
      minHeight: '44px',
      height: 'auto',
      padding: '12px 16px',
      background: 'var(--accent)',
      color: '#0C1726',
      fontWeight: 700,
      fontFamily: 'var(--font-display)',
      fontSize: '14.5px',
      boxShadow: 'var(--shadow-sm)',
      marginTop: '4px',
    },
    formFieldInput: {
      minHeight: '44px',
      padding: '11px 13px',
      border: '1px solid var(--border-strong)',
      background: 'var(--field)',
    },
    formFieldLabel: { color: 'var(--text-2)', fontSize: '12.5px', fontWeight: 600 },
    identityPreview: { background: 'var(--surface-2)' },
  },
};

export default function Login({ theme, toggleTheme }) {
  const isInvite = useMemo(() => hasInviteTicket(), []);

  return (
    <div className="login-root">
      <svg className="login-aurora" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice">
        <defs>
          <radialGradient id="g1"><stop offset="0%" stopColor="var(--accent)" stopOpacity="0.16"/><stop offset="100%" stopColor="var(--accent)" stopOpacity="0"/></radialGradient>
          <radialGradient id="g2"><stop offset="0%" stopColor="#4C8DD8" stopOpacity="0.12"/><stop offset="100%" stopColor="#4C8DD8" stopOpacity="0"/></radialGradient>
        </defs>
        <circle cx="250" cy="180" r="320" fill="url(#g1)"/>
        <circle cx="980" cy="640" r="360" fill="url(#g2)"/>
      </svg>

      <button
        type="button"
        className="icon-btn bordered"
        style={{ position: 'absolute', top: 20, right: 20, zIndex: 3 }}
        onClick={toggleTheme}
        title="Toggle theme"
      >
        {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
        {theme === 'dark' ? 'Light' : 'Dark'}
      </button>

      <div className="login-card fade-in">
        <div className="login-mark"><LogoMark size={54} /></div>
        <h1>{isInvite ? 'Accept your invitation' : 'Welcome to Nate AI'}</h1>
        <p className="login-tag">
          {isInvite
            ? 'Create your password to join Meeker CPA\u2019s Nate AI workspace.'
            : 'Your AI-powered tax & real estate advisor'}
        </p>

        <div className="clerk-signin-wrap">
          {isInvite ? (
            /* Invites must use SignUp + __clerk_ticket — SignIn causes "non-existing identification" */
            <SignUp appearance={clerkAppearance} />
          ) : (
            <SignIn routing="hash" appearance={clerkAppearance} />
          )}
        </div>

        <div className="login-foot">
          Access is by invitation only. <a href="mailto:support@meekercpa.com">Request access</a>
        </div>
      </div>

      <div className="clerk-note">
        <Check size={13} style={{ color: 'var(--accent)' }} />
        Secured by Clerk · Meeker CPA, PLLC
      </div>
    </div>
  );
}
