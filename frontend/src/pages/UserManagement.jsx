import { UserRound } from "lucide-react";
import "./UserManagement.css";

export default function UserManagement({ data }) {
  const users=data?.users?.users||[];
  return <div><div className="page-heading"><div><h2>User Management</h2><p>Registered users in the SecureHomeAI authentication database.</p></div></div>
    {users.length===0?<div className="empty-state">No registered users found.</div>:<div className="users-grid">{users.map(user=><article className="user-card" key={user.id}>
      <div className="user-avatar">{String(user.name||"?").charAt(0).toUpperCase()}</div>
      <div className="user-info"><strong>{user.name}</strong><span>Registered User #{user.id}</span><b><i/> ENROLLED</b></div>
    </article>)}</div>}
    <p className="privacy-note"><UserRound size={15}/> Biometric embeddings and voice templates are not exposed by this page.</p>
  </div>;
}