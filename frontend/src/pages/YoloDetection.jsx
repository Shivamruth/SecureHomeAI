import { ScanEye } from "lucide-react";
import "./YoloDetection.css";

export default function YoloDetection({ data }) {
  const events=data?.yoloEvents?.events||[];
  const objects=data?.dashboard?.objectCounts||{};
  return <div><div className="page-heading"><div><h2>YOLO Detection</h2><p>Object detection and ByteTrack event history.</p></div></div>
    <div className="yolo-summary">{Object.entries(objects).sort((a,b)=>b[1]-a[1]).map(([name,count])=><div className="yolo-chip" key={name}><ScanEye size={16}/><span>{name}</span><b>{count}</b></div>)}</div>
    <section className="panel"><h3>Recent Detection Events</h3><p className="panel-subtitle">{data?.yoloEvents?.total??0} total recorded detections · latest first</p>
      {events.length===0?<div className="empty-state">No YOLO events recorded yet.</div>:<div className="data-table-wrap"><table className="data-table"><thead><tr><th>Timestamp</th><th>Object</th><th>Event</th><th>Track ID</th><th>Confidence</th><th>Decision</th></tr></thead><tbody>
        {events.map((e,i)=><tr key={`${e.timestamp}-${e.track_id}-${i}`}><td>{formatDate(e.timestamp)}</td><td>{e.object||"—"}</td><td>{e.event_type||"—"}</td><td>{e.track_id??"—"}</td><td>{typeof e.confidence==="number"?`${(e.confidence*100).toFixed(1)}%`:"—"}</td><td><span className="status-pill neutral">{e.security_decision||"NOT EVALUATED"}</span></td></tr>)}
      </tbody></table></div>}
    </section>
    <p className="yolo-footnote">YOLO detections are object-monitoring events. They are not identity verification results and do not independently grant or deny access.</p>
  </div>;
}
function formatDate(value){if(!value)return "—";const d=new Date(value);return Number.isNaN(d.getTime())?value:d.toLocaleString();}