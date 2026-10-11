// POST {wort, typ, daten, foto} -> Mail "NEUES WORT" mit Laut-Aufnahme und Foto.
// daten: Audio als Base64, foto: JPEG als Base64 (im Browser verkleinert).
// Das Wort kommt auf die Taste seines ersten Buchstabens, auch Ä/Ö/Ü.

import { person } from "./_sitzung.js";
import {
  ENDUNG, FAMILIE, MAX_BASE64, gutesBase64, gutesWort, heute, ordner, umwandeln, verschicke,
} from "./_mail.js";

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).end();
  const von = person(req);
  if (!von) return res.status(401).end();

  const { wort, typ, daten, foto } = req.body ?? {};
  const endung = ENDUNG[String(typ).split(";")[0]];
  if (!gutesWort(wort) || !endung || !gutesBase64(daten) || !gutesBase64(foto)
      || daten.length + foto.length > MAX_BASE64) {
    return res.status(400).end();
  }

  const buchstabe = wort[0].toUpperCase();
  const laut = `${ordner(wort)}_laut_${ordner(von)}.${endung}`;
  const bild = `${ordner(wort)}_bild_${ordner(von)}.jpg`;
  const eintrag = JSON.stringify({ name: wort, laut: "" });
  await verschicke({
    subject: `oskalizer: NEUES WORT ${wort} – ${von}`,
    text: `${von} schlägt „${wort}“ für die Taste ${buchstabe} vor.\n\n`
      + `1. In woerter.json bei "${buchstabe}" anhängen (gibt's den Buchstaben `
      + `noch nicht, neu anlegen):\n${eintrag}\n\n`
      + `2. Laut umwandeln und ablegen:\n${umwandeln(laut, wort, "laut", von)}\n\n`
      + `3. Foto ablegen:\nmkdir -p ${FAMILIE}/${ordner(wort)}/bild && cp ${bild} `
      + `${FAMILIE}/${ordner(wort)}/bild/${ordner(von)}_${heute()}.jpg\n`,
    attachments: [
      { filename: laut, content: Buffer.from(daten, "base64") },
      { filename: bild, content: Buffer.from(foto, "base64") },
    ],
  });
  res.status(200).json({ ok: true });
}
