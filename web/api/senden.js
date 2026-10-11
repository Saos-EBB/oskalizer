// POST {wort, slot, typ, daten} -> Mail mit der Aufnahme als Anhang an MAIL_TO.
// slot: "name" (der ganze Satz "A wie Affe") oder "laut". daten: Base64.
// Die Person kommt aus dem Cookie, nie aus dem Formular.

import nodemailer from "nodemailer";
import { person } from "./_sitzung.js";

const ENDUNG = { "audio/webm": "webm", "audio/mp4": "m4a", "audio/ogg": "ogg" };
const SLOTS = { name: ["Name", "den Namen"], laut: ["Laut", "den Laut"] };
const MAX_BASE64 = 4_000_000;               // Vercel nimmt Bodies bis ~4,5 MB

// Wie ordner() in tiere.py: "Bär" -> "baer", damit der Pfad in der Mail passt.
function ordner(name) {
  return name.toLowerCase().replace(/ä/g, "ae").replace(/ö/g, "oe")
    .replace(/ü/g, "ue").replace(/ß/g, "ss");
}

export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).end();
  const von = person(req);
  if (!von) return res.status(401).end();

  const { wort, slot, typ, daten } = req.body ?? {};
  const endung = ENDUNG[String(typ).split(";")[0]];
  if (typeof wort !== "string" || !/^[\p{L} -]{1,40}$/u.test(wort) || !Object.hasOwn(SLOTS, slot)
      || !endung || typeof daten !== "string" || !daten || daten.length > MAX_BASE64) {
    return res.status(400).end();
  }

  const datum = new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Berlin" });
  const ziel = `~/.local/share/oskalizer/familie/${ordner(wort)}/${slot}`;
  const anhang = `${ordner(wort)}_${slot}_${ordner(von)}.${endung}`;
  await nodemailer.createTransport({
    service: "gmail",
    auth: { user: process.env.GMAIL_USER, pass: process.env.GMAIL_APP_PASSWORD },
  }).sendMail({
    from: process.env.GMAIL_USER,
    to: process.env.MAIL_TO,
    subject: `oskalizer: ${wort} / ${SLOTS[slot][0]} – ${von}`,
    text: `${von} hat für „${wort}“ ${SLOTS[slot][1]} eingesprochen.\n\n`
      + `Umwandeln und ablegen:\n`
      + `mkdir -p ${ziel} && ffmpeg -i ${anhang} `
      + `-af "silenceremove=1:0:-50dB,loudnorm" ${ziel}/${ordner(von)}_${datum}.ogg\n`,
    attachments: [{
      filename: anhang,
      content: Buffer.from(daten, "base64"),
    }],
  });
  res.status(200).json({ ok: true });
}
