export default function StatCard({ title, value, subtitle, icon, color }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color || ""}`}>{icon}</div>

      <div className="stat-content">
        <p>{title}</p>
        <h2>{value ?? 0}</h2>
        <span>{subtitle}</span>
      </div>
    </div>
  );
}