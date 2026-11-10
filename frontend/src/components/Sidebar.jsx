import {
  LayoutDashboard, Camera, ClipboardList, ScanEye, ShieldAlert, Users, Shield
} from "lucide-react";
import "./Sidebar.css";

const items = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "live", label: "Live Monitoring", icon: Camera },
  { id: "events", label: "Security Events", icon: ClipboardList },
  { id: "yolo", label: "YOLO Detection", icon: ScanEye },
  { id: "risk", label: "Risk Analysis", icon: ShieldAlert },
  { id: "users", label: "User Management", icon: Users }
];

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Shield size={23} /></div>
        <div><strong>SecureHomeAI</strong><small>INTELLIGENT SECURITY</small></div>
      </div>
      <div className="menu-caption">MAIN MENU</div>
      <nav className="side-nav">
        {items.map(({ id, label, icon: Icon }) => (
          <button key={id} className={`nav-item ${activePage === id ? "active" : ""}`}
            onClick={() => onNavigate(id)}>
            <Icon size={17} strokeWidth={1.8} /><span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <span className="sidebar-dot" /> Local security system
      </div>
    </aside>
  );
}