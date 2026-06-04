import { useUser } from '@clerk/clerk-react';

/** Set in Clerk Dashboard → Users → user → Public metadata: { "role": "admin" } */
export const ROLES = {
  ADMIN: 'admin',
  CLIENT: 'client',
};

export function getRoleFromUser(user) {
  const role = user?.publicMetadata?.role;
  return role === ROLES.ADMIN ? ROLES.ADMIN : ROLES.CLIENT;
}

export function useAppRole() {
  const { user, isLoaded } = useUser();
  const role = getRoleFromUser(user);
  return {
    role,
    isAdmin: role === ROLES.ADMIN,
    isLoaded,
  };
}
