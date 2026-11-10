import { useEffect, useState } from "react";
import { api } from "../services/api";
import "../styles/users.css";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const result = await api.users();
        setUsers(result.users || []);
        setError("");
      } catch {
        setError("Unable to retrieve registered users.");
      }
    }

    load();
    const timer = setInterval(load, 10000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="page-content">
      <h2>User Management</h2>
      <p className="page-description">
        Registered users in the SecureHomeAI authentication database.
      </p>

      {error && <div className="error-state">{error}</div>}

      <div className="users-grid">
        {users.map(user => (
          <div className="user-card" key={user.id}>
            <div className="user-avatar">
              {user.name.charAt(0).toUpperCase()}
            </div>

            <div>
              <h3>{user.name}</h3>
              <p>Registered User #{user.id}</p>
              <span className="user-status">ENROLLED</span>
            </div>
          </div>
        ))}

        {!users.length && !error && (
          <div className="empty-state">No registered users found.</div>
        )}
      </div>

      <p className="privacy-note">
        Biometric embeddings and voice templates are not exposed by this page.
      </p>
    </div>
  );
}