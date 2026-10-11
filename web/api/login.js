// POST {passwort} -> Cookie mit der Person. Falsches Passwort: 3 s warten, 401,
// sonst nichts - kein Hinweis, ob es fast gepasst hätte.

import { gleich, personen, setzeSitzung } from "./_sitzung.js";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).end();
  const eingabe = String(req.body?.passwort ?? "");
  for (const [name, passwort] of personen()) {
    if (gleich(eingabe, passwort)) {
      setzeSitzung(res, name);
      return res.status(200).json({ person: name });
    }
  }
  await new Promise((fertig) => setTimeout(fertig, 3000));
  res.status(401).end();
}
