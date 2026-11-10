import { useMemo, useState } from "react";
import "./SecurityEvents.css";

function status(value){const v=String(value||"UNKNOWN").toUpperCase();return v==="GRANTED"?"granted":v==="DENIED"?"denied":"unknown"}
export default function SecurityEvents({ data }) {
  const [filter,setFilter]=useState("ALL");
  const events=data?.events?.events||[];
  const filtered=useMemo(()=>filter==="ALL"?events:events.filter(e=>String(e.access).toUpperCase()===filter),[events,filter]);
  return <div><div className="page-heading"><div><h2>Security Events</h2><p>Authentication history recorded by the AI engine.</p></div>
    <select className="filter-select" value={filter} onChange={e=>setFilter(e.target.value)}><option>ALL</option><option>GRANTED</option><option>DENIED</option></select></div>
    <section className="panel"><h3>Authentication Log</h3><p className="panel-subtitle">{filtered.length} event(s) shown · newest first</p>
      {filtered.length===0?<div className="empty-state">No security events match this filter.</div>:<div className="data-table-wrap"><table className="data-table"><thead><tr><th>Timestamp</th><th>User</th><th>Liveness</th><th>Face</th><th>Access</th><th>Reason</th></tr></thead><tbody>
        {filtered.map((e,i)=><tr key={`${e.timestamp}-${i}`}><td>{formatDate(e.timestamp)}</td><td>{e.user||"Unknown"}</td><td>{e.liveness||"—"}</td><td>{e.face_recognition||"—"}</td><td><span className={`status-pill ${status(e.access)}`}>{e.access||"UNKNOWN"}</span></td><td>{e.reason||"—"}</td></tr>)}
      </tbody></table></div>}
    </section>
  </div>;
}
function formatDate(value){if(!value)return "—";const d=new Date(value);return Number.isNaN(d.getTime())?value:d.toLocaleString();}