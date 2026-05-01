const { default: makeWASocket, DisconnectReason, useMultiFileAuthState } = require("@whiskeysockets/baileys");
const qrcode = require("qrcode-terminal");
const http = require("http");
const fs = require("fs");
const FormData = require("form-data");
const path = require("path");

require("dotenv").config();

const DISCLAIMER = "DISCLAIMER: This is decision support only. Always consult a licensed veterinarian.";

async function sendToAPI(videoPath, animalId, farmerPhone) {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    form.append("video", fs.createReadStream(videoPath));
    form.append("animal_id", animalId);
    form.append("farmer_phone", farmerPhone);
    const options = {
      hostname: "127.0.0.1",
      port: 8000,
      path: "/analyze",
      method: "POST",
      headers: form.getHeaders()
    };
    const req = http.request(options, res => {
      let data = "";
      res.on("data", chunk => data += chunk);
      res.on("end", () => {
        try { resolve(JSON.parse(data)); }
        catch (e) { reject(e); }
      });
    });
    req.on("error", reject);
    form.pipe(req);
  });
}

function formatResponse(result) {
  const { analysis, triage, treatment_context } = result;
  let msg = "";
  msg += "BOURGELAT ASSESSMENT\n";
  msg += "━━━━━━━━━━━━━━━━━━━━\n\n";
  msg += "BCS Score: " + analysis.bcs_score + "/5\n";
  msg += "Conditions: " + analysis.conditions.join(", ") + "\n";
  msg += "Confidence: " + Math.round(analysis.confidence * 100) + "%\n\n";
  msg += "Observations:\n" + analysis.observations + "\n\n";

  if (triage.level === "mild") {
    msg += "SEVERITY: MILD\n";
    msg += "Recommended Action:\n" + treatment_context + "\n";
  } else if (triage.level === "moderate") {
    msg += "SEVERITY: MODERATE\n";
    msg += "Treatment Guidance:\n" + treatment_context + "\n";
  } else {
    msg += "SEVERITY: " + triage.level.toUpperCase() + "\n";
    msg += "Veterinary care required immediately.\n";
    msg += "Your registered vet is being notified.\n";
  }

  msg += "\n" + DISCLAIMER;
  return msg;
}

async function notifyVet(sock, vetPhone, animalId, result, farmerPhone) {
  if (!vetPhone) return;
  const msg = "BOURGELAT VET ALERT\n\n"
    + "Farmer: " + farmerPhone + "\n"
    + "Animal ID: " + animalId + "\n"
    + "Diagnosis: " + result.analysis.conditions.join(", ") + "\n"
    + "BCS: " + result.analysis.bcs_score + "/5\n"
    + "Severity: " + result.triage.level.toUpperCase() + "\n"
    + "Confidence: " + Math.round(result.analysis.confidence * 100) + "%\n\n"
    + "Observations:\n" + result.analysis.observations + "\n\n"
    + "Please contact the farmer for a consultation.";
  await sock.sendMessage(vetPhone + "@s.whatsapp.net", { text: msg });
}

async function startBot() {
  const { state, saveCreds } = await useMultiFileAuthState("auth");
  const sock = makeWASocket({ auth: state, printQRInTerminal: true });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", ({ connection, lastDisconnect, qr }) => {
    if (qr) qrcode.generate(qr, { small: true });
    if (connection === "close") {
      const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
      if (shouldReconnect) startBot();
    } else if (connection === "open") {
      console.log("Bourgelat WhatsApp bot connected.");
    }
  });

  sock.ev.on("messages.upsert", async ({ messages }) => {
    const msg = messages[0];
    if (!msg.message || msg.key.fromMe) return;

    const from = msg.key.remoteJid;
    const farmerPhone = from.replace("@s.whatsapp.net", "");
    const body = msg.message.conversation || msg.message.extendedTextMessage?.text || "";
    const videoMsg = msg.message.videoMessage;

    if (body.toLowerCase() === "hi" || body.toLowerCase() === "hello") {
      await sock.sendMessage(from, {
        text: "Welcome to Bourgelat - AI Veterinary Assistant\n\nTo analyze your cattle:\n1. Send a short video of your animal\n2. Include the animal ID in your message\n\nType help for available commands."
      });
      return;
    }

    if (body.toLowerCase() === "help") {
      await sock.sendMessage(from, {
        text: "BOURGELAT COMMANDS\n\nSend a video - Analyze cattle health\nrecords [animal_id] - View health history\nfeed [animal_id] - Get feed recommendations\nvet - Contact your registered vet"
      });
      return;
    }

    if (videoMsg) {
      await sock.sendMessage(from, { text: "Analyzing your cattle video... Please wait." });
      try {
        const buffer = await sock.downloadMediaMessage(msg);
        const tmpPath = path.join(__dirname, "..", "logs", "tmp_" + Date.now() + ".mp4");
        fs.writeFileSync(tmpPath, buffer);
        const animalId = body.trim() || "unknown";
        const result = await sendToAPI(tmpPath, animalId, farmerPhone);
        fs.unlinkSync(tmpPath);
        const response = formatResponse(result);
        await sock.sendMessage(from, { text: response });
        if (result.triage.level === "severe" || result.triage.level === "inconclusive") {
          const vetPhone = process.env.VET_PHONE;
          await notifyVet(sock, vetPhone, animalId, result, farmerPhone);
        }
      } catch (err) {
        console.error("Analysis error:", err);
        await sock.sendMessage(from, {
          text: "Error analyzing video. Please try again or contact your vet directly."
        });
      }
      return;
    }
  });
}

startBot().catch(console.error);
