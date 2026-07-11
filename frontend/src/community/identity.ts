// Auth-free pseudonymous identity: name + zip kept in localStorage (plan: no real auth).
export interface Identity {
  name: string;
  zip: string;
}

const KEY = "vakathon-identity";

export function getIdentity(): Identity | null {
  const raw = localStorage.getItem(KEY);
  return raw ? (JSON.parse(raw) as Identity) : null;
}

export function setIdentity(id: Identity): void {
  localStorage.setItem(KEY, JSON.stringify(id));
}
