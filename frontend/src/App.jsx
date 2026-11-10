import { useCallback, useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import Dashboard from "./pages/Dashboard";
import LiveMonitoring from "./pages/LiveMonitoring";
import SecurityEvents from "./pages/SecurityEvents";
import YoloDetection from "./pages/YoloDetection";
import RiskAnalysis from "./pages/RiskAnalysis";
import UserManagement from "./pages/UserManagement";
import { loadDashboardData } from "./services/api";
import "./styles/app.css";

const pages = {
  dashboard: { title: "Security Overview", component: Dashboard },
  live: { title: "Live Monitoring", component: LiveMonitoring },
  events: { title: "Security Events", component: SecurityEvents },
  yolo: { title: "YOLO Detection", component: YoloDetection },
  risk: { title: "Risk Analysis", component: RiskAnalysis },
  users: { title: "User Management", component: UserManagement }
};

export default function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      const result = await loadDashboardData();
      setData(result);
      setError("");
    } catch (err) {
      setError(err.message || "Unable to connect to backend");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const CurrentPage = pages[activePage].component;

  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <div className="main-shell">
        <Topbar title={pages[activePage].title} connected={Boolean(data?.health?.success)} />
        {error && (
          <div className="connection-error">
            <ShieldCheck size={17} /> Backend connection unavailable: {error}
            <button onClick={refresh}>Retry</button>
          </div>
        )}
        <main className="page-content">
          {loading && !data ? <div className="loading-panel">Connecting to SecureHomeAI backend…</div> :
            <CurrentPage data={data} onRefresh={refresh} />}
        </main>
        <footer className="app-footer">
          <span>SecureHomeAI · AI-Based Intelligent Home Security System</span>
          <span>Auto refresh · 5 seconds</span>
        </footer>
      </div>
    </div>
  );
}