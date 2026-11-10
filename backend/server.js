
const http = require("http");
const fs = require("fs");
const path = require("path");
const { URL } = require("url");

const PORT = Number(process.env.PORT) || 5000;

const DATABASE = path.resolve(
  __dirname,
  "..",
  "ai-engine",
  "face-recognition",
  "database"
);

const FILES = {
  security: path.join(DATABASE, "security_logs.json"),
  yolo: path.join(DATABASE, "yolo_events.json"),
  users: path.join(DATABASE, "users.json"),
  voice: path.join(DATABASE, "voice_profiles.json")
};

function readJSON(file, fallback = []) {
  try {
    const content = fs.readFileSync(file, "utf8");
    return JSON.parse(content);
  } catch (error) {
    console.error(`Database read error: ${path.basename(file)}: ${error.message}`);
    return fallback;
  }
}

function readDatabase() {
  return {
    security: readJSON(FILES.security),
    yolo: readJSON(FILES.yolo),
    users: readJSON(FILES.users),
    voice: readJSON(FILES.voice, {})
  };
}

// Never expose biometric templates or other sensitive fields.
function sanitize(value) {
  if (Array.isArray(value)) {
    return value.map(sanitize);
  }

  if (value && typeof value === "object") {
    const result = {};

    for (const [key, item] of Object.entries(value)) {
      if (/embedding|template|voiceprint|descriptor|password|secret|audio|vector/i.test(key)) {
        continue;
      }

      result[key] = sanitize(item);
    }

    return result;
  }

  return value;
}

function getDecision(event) {
  const access = event?.access;

  if (typeof access === "boolean") return access;

  if (typeof access === "string") {
    const value = access.toUpperCase();
    if (value === "GRANTED") return true;
    if (value === "DENIED") return false;
  }

  if (access && typeof access === "object") {
    if (typeof access.granted === "boolean") return access.granted;

    const value = String(
      access.decision || access.status || access.result || ""
    ).toUpperCase();

    if (value === "GRANTED") return true;
    if (value === "DENIED") return false;
  }

  return null;
}

function getRisk(event) {
  const access = event?.access || {};
  const candidates = [
    access?.risk?.risk_level,
    access?.risk?.level,
    access?.risk_level,
    access?.riskLevel,
    event?.risk?.risk_level,
    event?.risk?.level,
    event?.risk_level
  ];

  for (const value of candidates) {
    if (typeof value === "string") {
      const level = value.toUpperCase();
      if (["LOW", "MEDIUM", "HIGH", "UNKNOWN"].includes(level)) {
        return level;
      }
    }
  }

  return "UNKNOWN";
}

function getVoiceProfileCount(voice) {
  const profiles = voice?.profiles;

  if (Array.isArray(profiles)) return profiles.length;

  if (profiles && typeof profiles === "object") {
    return Object.keys(profiles).length;
  }

  return 0;
}

function getUsers(users) {
  if (!Array.isArray(users)) return [];

  return users.map((user, index) => ({
    id: index + 1,
    name: typeof user.name === "string" ? user.name : "Unknown"
  }));
}

function getDashboard(data) {
  const security = Array.isArray(data.security) ? data.security : [];
  const yolo = Array.isArray(data.yolo) ? data.yolo : [];
  const users = getUsers(data.users);

  let granted = 0;
  let denied = 0;

  for (const event of security) {
    const decision = getDecision(event);
    if (decision === true) granted++;
    if (decision === false) denied++;
  }

  const objectCounts = {};

  for (const event of yolo) {
    const object = event.object || "unknown";
    objectCounts[object] = (objectCounts[object] || 0) + 1;
  }

  const riskCounts = {
    LOW: 0,
    MEDIUM: 0,
    HIGH: 0,
    UNKNOWN: 0
  };

  for (const event of security) {
    riskCounts[getRisk(event)]++;
  }

  return {
    success: true,
    stats: {
      registeredUsers: users.length,
      voiceProfiles: getVoiceProfileCount(data.voice),
      securityEvents: security.length,
      yoloEvents: yolo.length,
      accessGranted: granted,
      accessDenied: denied
    },
    riskCounts,
    objectCounts,
    recentSecurityEvents: sanitize(security.slice(-10).reverse()),
    recentYOLOEvents: sanitize(yolo.slice(-10).reverse()),
    generatedAt: new Date().toISOString()
  };
}

function sendJSON(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "http://localhost:5173",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Cache-Control": "no-store"
  });

  response.end(JSON.stringify(payload));
}

function createServer() {
  return http.createServer((request, response) => {
    if (request.method === "OPTIONS") {
      sendJSON(response, 200, { success: true });
      return;
    }

    if (request.method !== "GET") {
      sendJSON(response, 405, {
        success: false,
        message: "Only GET requests are supported."
      });
      return;
    }

    const url = new URL(request.url, `http://localhost:${PORT}`);
    const route = url.pathname;
    const data = readDatabase();

    if (route === "/api/health") {
      sendJSON(response, 200, {
        success: true,
        service: "SecureHomeAI Backend",
        status: "RUNNING",
        database: fs.existsSync(DATABASE) ? "AVAILABLE" : "UNAVAILABLE",
        timestamp: new Date().toISOString()
      });
      return;
    }

    if (route === "/api/dashboard") {
      sendJSON(response, 200, getDashboard(data));
      return;
    }

    if (route === "/api/events") {
      const limit = Math.min(
        200,
        Math.max(1, Number(url.searchParams.get("limit")) || 50)
      );

      const events = Array.isArray(data.security) ? data.security : [];

      sendJSON(response, 200, {
        success: true,
        total: events.length,
        events: sanitize(events.slice(-limit).reverse())
      });
      return;
    }

    if (route === "/api/yolo-events") {
      const limit = Math.min(
        200,
        Math.max(1, Number(url.searchParams.get("limit")) || 50)
      );

      const events = Array.isArray(data.yolo) ? data.yolo : [];

      sendJSON(response, 200, {
        success: true,
        total: events.length,
        events: sanitize(events.slice(-limit).reverse())
      });
      return;
    }

    if (route === "/api/users") {
      sendJSON(response, 200, {
        success: true,
        total: getUsers(data.users).length,
        users: getUsers(data.users)
      });
      return;
    }

    if (route === "/api/risk") {
      const security = Array.isArray(data.security) ? data.security : [];

      const riskCounts = {
        LOW: 0,
        MEDIUM: 0,
        HIGH: 0,
        UNKNOWN: 0
      };

      security.forEach(event => {
        riskCounts[getRisk(event)]++;
      });

      sendJSON(response, 200, {
        success: true,
        riskCounts,
        note: "These are recorded event risk labels, not newly calculated live risk scores."
      });
      return;
    }

    sendJSON(response, 404, {
      success: false,
      message: "API endpoint not found."
    });
  });
}

const server = createServer();

server.listen(PORT, "127.0.0.1", () => {
  console.log("\n===== SECUREHOMEAI BACKEND =====");
  console.log(`Server: http://localhost:${PORT}`);
  console.log(`Database: ${DATABASE}`);
  console.log("Status: RUNNING");
  console.log("\nAvailable API endpoints:");
  console.log("GET /api/health");
  console.log("GET /api/dashboard");
  console.log("GET /api/events");
  console.log("GET /api/yolo-events");
  console.log("GET /api/users");
  console.log("GET /api/risk");
});
