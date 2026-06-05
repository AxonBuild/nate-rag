/** True when the URL contains a Clerk invitation ticket (custom redirect flow). */
export function hasInviteTicket() {
  return Boolean(getInviteTicket());
}

export function getInviteTicket() {
  const fromSearch = new URLSearchParams(window.location.search).get('__clerk_ticket');
  if (fromSearch) return fromSearch;

  const hash = window.location.hash || '';
  const qIndex = hash.indexOf('?');
  if (qIndex >= 0) {
    const fromHash = new URLSearchParams(hash.slice(qIndex + 1)).get('__clerk_ticket');
    if (fromHash) return fromHash;
  }

  return null;
}
