import { Users, ClipboardList, CheckCircle2, Ban, ScanEye, Music2, RefreshCw } from "lucide-react";
import "./Dashboard.css";

function StatCard({ title, value, note, icon: Icon, tone }) {
  return <div className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={21}/></div>
    <div className="stat-copy"><span>{title}</span><strong>{value ?? "—"}</strong><small>{note}</small></div></div>;
}

export default function Dashboard({ data, onRefresh }) {
  const stats = data?.dashboard?.stats || {};
  const risks = data?.dashboard?.riskCounts || {};
  const objects = data?.dashboard?.objectCounts || {};
  const maxObject = Math.max(1, ...Object.values(objects));
  const riskRows = [
    ["LOW", risks.LOW || 0, "green"], ["MEDIUM", risks.MEDIUM || 0, "yellow"],
    ["HIGH", risks.HIGH || 0, "red"], ["UNKNOWN", risks.UNKNOWN || 0, "muted"]
  ];
  return <div>
    <div className="page-heading"><div><h2>System Overview</h2><p>Live statistics from the SecureHomeAI database.</p></div>
      <button className="refresh-button" onClick={onRefresh}><RefreshCw size={14}/> Refresh</button></div>
    <div className="stats-grid">
      <StatCard title="Registered Users" value={stats.registeredUsers} note="Enrolled users" icon={Users} tone="blue"/>
      <StatCard title="Security Events" value={stats.securityEvents} note="Recorded authentication events" icon={ClipboardList} tone="purple"/>
      <StatCard title="Access Granted" value={stats.accessGranted} note="Successful authentication" icon={CheckCircle2} tone="green"/>
      <StatCard title="Access Denied" value={stats.accessDenied} note="Rejected authentication" icon={Ban} tone="red"/>
      <StatCard title="YOLO Events" value={stats.yoloEvents} note="Recorded detection events" icon={ScanEye} tone="orange"/>
      <StatCard title="Voice Profiles" value={stats.voiceProfiles} note="Enrolled voice profiles" icon={Music2} tone="blue"/>
    </div>
    <div className="dashboard-lower">
      <section className="panel"><h3>Risk Distribution</h3><p className="panel-subtitle">Recorded risk classifications</p>
        <div className="risk-bars">{riskRows.map(([label,value,tone])=><div className="risk-row" key={label}>
          <div><span>{label}</span><b>{value}</b></div><div className="bar-track"><i className={tone} style={{width:`${(value/Math.max(1,Object.values(risks).reduce((a,b)=>a+b,0)))*100}%`}}/></div>
        </div>)}</div>
        <p className="chart-note">Most older events do not contain a saved risk label, so they appear as UNKNOWN.</p>
      </section>
      <section className="panel"><h3>Detected Objects</h3><p className="panel-subtitle">YOLOv8 object event counts</p>
        <div className="object-bars">{Object.entries(objects).sort((a,b)=>b[1]-a[1]).map(([name,value])=><div className="object-row" key={name}>
          <span>{name}</span><div className="bar-track"><i style={{width:`${value/maxObject*100}%`}}/></div><b>{value}</b>
        </div>)}</div>
      </section>
    </div>
  </div>;
}