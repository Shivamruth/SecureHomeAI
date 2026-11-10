import { Wifi, WifiOff } from "lucide-react";
import "./Topbar.css";

export default function Topbar({ title, connected }) {
  return (
    <header className="topbar">
      <div><h1>{title}</h1><p>AI-Based Intelligent Home Security System</p></div>
      <div className={`backend-state ${connected ? "online" : "offline"}`}>
        {connected ? <Wifi size={14} /> : <WifiOff size={14} />}
        {connected ? "Backend Connected" : "Backend Disconnected"}
      </div>
    </header>
  );
}