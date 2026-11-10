import { ShieldAlert } from "lucide-react";
import "./RiskAnalysis.css";

const levels=[["LOW","green"],["MEDIUM","yellow"],["HIGH","red"],["UNKNOWN","muted"]];
export default function RiskAnalysis({ data }) {
  const counts=data?.risk?.riskCounts||data?.dashboard?.riskCounts||{};
  const total=levels.reduce((sum,[name])=>sum+(counts[name]||0),0);
  return <div><div className="page-heading"><div><h2>Risk Analysis</h2><p>Recorded risk labels from authentication history.</p></div></div>
    <div className="risk-summary-grid">{levels.map(([name,tone])=><div className="risk-summary-card" key={name}><span>{name} EVENTS</span><strong>{counts[name]||0}</strong><small>{total?`${((counts[name]||0)/total*100).toFixed(1)}% of recorded events`:"No records"}</small></div>)}</div>
    <section className="panel"><h3><ShieldAlert size={16}/> Risk Classification</h3><p className="panel-subtitle">Historical event risk distribution · {total} events</p>
      <div className="risk-detail-list">{levels.map(([name,tone])=><div className="risk-detail" key={name}><div><span>{name}</span><b>{counts[name]||0}</b></div><div className="bar-track"><i className={tone} style={{width:`${total?(counts[name]||0)/total*100:0}%`}}/></div></div>)}</div>
      <div className="risk-warning"><strong>Interpretation:</strong> UNKNOWN means the historical event did not contain a risk label. It does not mean a HIGH-risk event. The backend currently reports stored labels; it does not calculate a new live risk score.</div>
    </section>
  </div>;
}