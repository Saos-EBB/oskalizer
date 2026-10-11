// GET -> {person}, wenn das Cookie gilt. Die Seite fragt beim Laden, ob sie das
// Passwortfeld überspringen kann.

import { person } from "./_sitzung.js";

export default function handler(req, res) {
  const name = person(req);
  if (!name) return res.status(401).end();
  res.status(200).json({ person: name });
}
