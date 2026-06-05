import { useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { setAuthTokenGetter } from '../api/client.js';
import { setStreamAuthTokenGetter } from '../api/chatStream.js';

/** Attaches Clerk session tokens to API requests. */
export default function AuthTokenBridge() {
  const { getToken, isSignedIn } = useAuth();

  useEffect(() => {
    if (!isSignedIn) {
      setAuthTokenGetter(null);
      return;
    }
    const getter = () => getToken();
    setAuthTokenGetter(getter);
    setStreamAuthTokenGetter(getter);
    return () => {
      setAuthTokenGetter(null);
      setStreamAuthTokenGetter(null);
    };
  }, [getToken, isSignedIn]);

  return null;
}
