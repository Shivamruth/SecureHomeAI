import { useEffect, useState } from "react";
import { api } from "../services/api";
import EventTable from "../components/EventTable";
import "../styles/events.css";

export default function YOLOEvents() {
  const [events, setEvents] = useState([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const result = await api.yoloEvents();
        setEvents(result.events || []);
        setTotal(result.total || 0);
        setError("");
      } catch {
        setError("Unable to retrieve YOLO events.");
      }
    }

    load();
    const timer = setInterval(load, 5000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="page-content">
      <h2>YOLOv8 Object Detection</h2>
      <p className="page-description">
        Object detection and ByteTrack tracking event history.
      </p>

      <section className="panel events-panel">
        <div className="panel-heading">
          <h3>Detection Records ({total} total)</h3>
        </div>

        {error ? (
          <div className="error-state">{error}</div>
        ) : (
          <EventTable events={events} type="yolo" />
        )}
      </section>
    </div>
  );
}