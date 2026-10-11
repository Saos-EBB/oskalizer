// Login-Cookie und Passwörter. Dateien mit _ sind bei Vercel keine Endpoints.
// Jeder Endpoint nimmt die Person aus person(req), nie aus dem Formular.

import crypto from "node:crypto";

const COOKIE = "sitzung";
const MAX_AGE = 180 * 24 * 3600;            // ein halbes Jahr eingeloggt

// FAMILY_PASSWORDS="Opa:geheim,Oma:auchgeheim" -> Map Person -> Passwort
export function personen() {
  const liste = new Map();
  for (const paar of (process.env.FAMILY_PASSWORDS || "").split(",")) {
    const i = paar.indexOf(":");
    const name = paar.slice(0, i).trim();
    const passwort = paar.slice(i + 1).trim();
    if (i > 0 && name && passwort) liste.set(name, passwort);
  }
  return liste;
}

// Zeitkonstanter Vergleich; die Hashes machen beide Seiten gleich lang.
export function gleich(a, b) {
  const hash = (s) => crypto.createHash("sha256").update(s).digest();
  return crypto.timingSafeEqual(hash(a), hash(b));
}

function signatur(name) {
  return crypto.createHmac("sha256", process.env.SESSION_SECRET).update(name).digest("base64url");
}

export function setzeSitzung(res, name) {
  const wert = `${Buffer.from(name).toString("base64url")}.${signatur(name)}`;
  res.setHeader("Set-Cookie",
    `${COOKIE}=${wert}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${MAX_AGE}`);
}

// Person aus dem Cookie, oder null. Wer aus FAMILY_PASSWORDS gelöscht ist,
// fliegt auch mit gültigem Cookie raus.
export function person(req) {
  const treffer = (req.headers.cookie || "").match(/(?:^|;\s*)sitzung=([^.;]+)\.([^;]+)/);
  if (!treffer) return null;
  const name = Buffer.from(treffer[1], "base64url").toString();
  return gleich(treffer[2], signatur(name)) && personen().has(name) ? name : null;
}
