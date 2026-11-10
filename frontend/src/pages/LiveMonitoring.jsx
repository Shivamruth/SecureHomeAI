import { Camera, CircleAlert, PlayCircle } from "lucide-react";
import "./LiveMonitoring.css";

export default function LiveMonitoring({ data }) {
  return <div><div className="page-heading"><div><h2>Live Monitoring</h2><p>Camera and AI monitoring status.</p></div></div>
    <div className="monitor-grid">
      <section className="panel camera-panel"><div className="camera-heading"><h3><Camera size={17}/> Camera Feed</h3><span className="status-pill neutral">NOT CONNECTED</span></div>
        <div className="camera-placeholder"><Camera size={42}/><strong>Camera stream is not connected to the dashboard</strong><span>The Python camera monitor runs separately at this stage.</span></div>
      </section>
      <section className="panel"><h3>AI Engine Status</h3><p className="panel-subtitle">Available recorded module activity</p>
        <div className="module-status"><span>Backend API</span><b className="good">CONNECTED</b></div>
        <div className="module-status"><span>Face authentication logs</span><b className="good">AVAILABLE</b></div>
        <div className="module-status"><span>YOLO detection logs</span><b className="good">AVAILABLE</b></div>
        <div className="module-status"><span>Live camera stream</span><b className="waiting">NOT INTEGRATED</b></div>
        <div className="module-status"><span>Voice profile records</span><b className="good">{data?.dashboard?.stats?.voiceProfiles ?? 0} PROFILE(S)</b></div>
        <div className="monitor-note"><CircleAlert size={16}/> This page does not display a simulated camera feed. Only real stream integration will enable video here.</div>
      </section>
    </div>
  </div>;
}