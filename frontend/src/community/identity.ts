// Auth-free pseudonymous identity: name + zip kept in localStorage (plan: no real auth).
export interface Identity {
  name: string;
  zip: string;
}

const KEY = "vakathon-identity";

export function getIdentity(promptIfMissing = false): Identity | null {
  const raw = localStorage.getItem(KEY);
  if (raw) return JSON.parse(raw) as Identity;
  if (!promptIfMissing) return null;
  const name = window.prompt("Your name (shown to neighbors on reports):")?.trim();
  if (!name) return null;
  const zip = window.prompt("Your ZIP code:")?.trim() ?? "";
  const id = { name, zip };
  localStorage.setItem(KEY, JSON.stringify(id));
  return id;
}
