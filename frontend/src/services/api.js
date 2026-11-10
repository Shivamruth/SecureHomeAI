const API = "/api";

async function request(path) {
  const response = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json();
}

export async function loadDashboardData() {
  const [health, dashboard, users, events, yoloEvents, risk] = await Promise.all([
    request("/health"),
    request("/dashboard"),
    request("/users"),
    request("/events?limit=100"),
    request("/yolo-events?limit=100"),
    request("/risk")
  ]);
  return { health, dashboard, users, events, yoloEvents, risk };
}