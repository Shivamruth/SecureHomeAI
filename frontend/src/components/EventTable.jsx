import { formatDate } from "../services/api";

export default function EventTable({ events = [], type = "security" }) {
  if (!events.length) {
    return <div className="empty-state">No recorded events found.</div>;
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          {type === "security" ? (
            <tr>
              <th>Time</th>
              <th>User</th>
              <th>Liveness</th>
              <th>Face</th>
              <th>Access</th>
            </tr>
          ) : (
            <tr>
              <th>Time</th>
              <th>Object</th>
              <th>Track ID</th>
              <th>Confidence</th>
              <th>Decision</th>
            </tr>
          )}
        </thead>

        <tbody>
          {events.map((event, index) => (
            <tr key={`${event.timestamp}-${index}`}>
              {type === "security" ? (
                <>
                  <td>{formatDate(event.timestamp)}</td>
                  <td>{event.user || "Unknown"}</td>
                  <td>{event.liveness || "N/A"}</td>
                  <td>{event.face_recognition || "N/A"}</td>
                  <td>
                    <span className={`pill ${
                      event.access === "GRANTED" ? "success" : "danger"
                    }`}>
                      {event.access || "UNKNOWN"}
                    </span>
                  </td>
                </>
              ) : (
                <>
                  <td>{formatDate(event.timestamp)}</td>
                  <td>{event.object || "Unknown"}</td>
                  <td>{event.track_id ?? "N/A"}</td>
                  <td>
                    {typeof event.confidence === "number"
                      ? `${(event.confidence * 100).toFixed(1)}%`
                      : "N/A"}
                  </td>
                  <td>{event.security_decision || "NOT_EVALUATED"}</td>
                </>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}