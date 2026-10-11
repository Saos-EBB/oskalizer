// Gemeinsames für senden.js und neu.js: Prüfen, Dateinamen, Gmail-Versand.

import nodemailer from "nodemailer";

export const ENDUNG = { "audio/webm": "webm", "audio/mp4": "m4a", "audio/ogg": "ogg" };
export const MAX_BASE64 = 4_000_000;        // Vercel nimmt Bodies bis ~4,5 MB
export const FAMILIE = "~/.local/share/oskalizer/familie";

// Nur Buchstaben, Leerzeichen, Bindestrich - landet in Dateinamen und im Mailtext.
export function gutesWort(wort) {
  return typeof wort === "string" && /^\p{L}[\p{L} -]{0,39}$/u.test(wort);
}

export function gutesBase64(daten) {
  return typeof daten === "string" && daten.length > 0 && daten.length <= MAX_BASE64;
}

// Wie ordner() in tiere.py: "Tante Bär" -> "tante-baer", damit die Pfade in der Mail passen.
export function ordner(name) {
  return name.toLowerCase().replace(/ä/g, "ae").replace(/ö/g, "oe")
    .replace(/ü/g, "ue").replace(/ß/g, "ss").replace(/ /g, "-");
}

export function heute() {
  return new Date().toLocaleDateString("sv-SE", { timeZone: "Europe/Berlin" });
}

// ffmpeg-Befehl: Anhang -> OGG im Familien-Ordner, Stille weg, Lautstärke angeglichen
export function umwandeln(anhang, wort, slot, von) {
  const ziel = `${FAMILIE}/${ordner(wort)}/${slot}`;
  return `mkdir -p ${ziel} && ffmpeg -i ${anhang} `
    + `-af "silenceremove=1:0:-50dB,loudnorm" ${ziel}/${ordner(von)}_${heute()}.ogg`;
}

export function verschicke({ subject, text, attachments }) {
  return nodemailer.createTransport({
    service: "gmail",
    auth: { user: process.env.GMAIL_USER, pass: process.env.GMAIL_APP_PASSWORD },
  }).sendMail({
    from: process.env.GMAIL_USER, to: process.env.MAIL_TO, subject, text, attachments,
  });
}
