// POST {wort, slot, typ, daten} -> Mail mit der Aufnahme als Anhang an MAIL_TO.
// slot: "name" (der ganze Satz "A wie Affe") oder "laut". daten: Base64.
// Die Person kommt aus dem Cookie, nie aus dem Formular.

import { person } from "./_sitzung.js";
import { ENDUNG, gutesBase64, gutesWort, ordner, umwandeln, verschicke } from "./_mail.js";

const SLOTS = { name: ["Name", "den Namen"], laut: ["Laut", "den Laut"] };

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).end();
  const von = person(req);
  if (!von) return res.status(401).end();

  const { wort, slot, typ, daten } = req.body ?? {};
  const endung = ENDUNG[String(typ).split(";")[0]];
  if (!gutesWort(wort) || !Object.hasOwn(SLOTS, slot) || !endung || !gutesBase64(daten)) {
    return res.status(400).end();
  }

  const anhang = `${ordner(wort)}_${slot}_${ordner(von)}.${endung}`;
  await verschicke({
    subject: `oskalizer: ${wort} / ${SLOTS[slot][0]} – ${von}`,
    text: `${von} hat für „${wort}“ ${SLOTS[slot][1]} eingesprochen.\n\n`
      + `Umwandeln und ablegen:\n${umwandeln(anhang, wort, slot, von)}\n`,
    attachments: [{ filename: anhang, content: Buffer.from(daten, "base64") }],
  });
  res.status(200).json({ ok: true });
}
