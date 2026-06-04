import { useState } from 'react';
import { useSignUp } from '@clerk/clerk-react';
import { getInviteTicket } from '../utils/clerkInvite.js';

export default function InviteSignUp() {
  const { isLoaded, signUp, setActive } = useSignUp();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isLoaded) return;

    const ticket = getInviteTicket();
    if (!ticket) {
      setError('Invitation link is invalid or expired. Ask your admin for a new invite.');
      return;
    }
    if (!firstName.trim() || !lastName.trim() || !password) {
      setError('Please enter your name and password.');
      return;
    }

    setError('');
    setLoading(true);
    try {
      await signUp.create({
        strategy: 'ticket',
        ticket,
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        password,
      });

      if (signUp.status === 'complete') {
        await setActive({ session: signUp.createdSessionId });
      } else {
        setError('Could not finish sign-up. Please try again or request a new invitation.');
      }
    } catch (err) {
      const msg =
        err?.errors?.[0]?.longMessage ||
        err?.errors?.[0]?.message ||
        err?.message ||
        'Sign-up failed';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="invite-signup-form" onSubmit={handleSubmit}>
      <div className="invite-name-row">
        <div className="login-field">
          <label htmlFor="invite-first">First name</label>
          <input
            id="invite-first"
            type="text"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="Jordan"
            autoComplete="given-name"
            required
          />
        </div>
        <div className="login-field">
          <label htmlFor="invite-last">Last name</label>
          <input
            id="invite-last"
            type="text"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Mercer"
            autoComplete="family-name"
            required
          />
        </div>
      </div>
      <div className="login-field">
        <label htmlFor="invite-password">Password</label>
        <input
          id="invite-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Create a password"
          autoComplete="new-password"
          required
        />
      </div>
      {error && <p className="login-error">{error}</p>}
      <button type="submit" className="login-btn" disabled={loading || !isLoaded}>
        {loading ? 'Creating account…' : 'Create account'}
      </button>
    </form>
  );
}
