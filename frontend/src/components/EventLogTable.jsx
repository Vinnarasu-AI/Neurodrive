import React from "react";
import { History, Check, X, ShieldAlert } from "lucide-react";

export default function EventLogTable({ logs = [], relayActions = [] }) {
  return (
    <div className="panel-card">
      <div className="panel-title-bar">
        <div className="panel-title">
          <History size={18} color="#06B6D4" />
          Real-Time Audit Trail & Gesture History (SQLite)
        </div>
        <span style={{ fontSize: "0.75rem", color: "#94A3B8" }}>
          Persisted securely in database
        </span>
      </div>

      <div style={{ maxHeight: "220px", overflowY: "auto" }}>
        <table className="event-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Event / Command</th>
              <th>Source / Trigger</th>
              <th>Status</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {relayActions.length === 0 && logs.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", color: "#64748B", padding: "1.5rem" }}>
                  No events recorded yet. Start Smart Home or toggle light to view audit log.
                </td>
              </tr>
            ) : (
              relayActions.map((action) => (
                <tr key={`act-${action.id}`}>
                  <td>{new Date(action.timestamp * 1000).toLocaleTimeString()}</td>
                  <td style={{ fontWeight: 600, color: action.state === "ON" ? "#EAB308" : "#94A3B8" }}>
                    RELAY: {action.command}
                  </td>
                  <td>
                    <span
                      style={{
                        padding: "0.15rem 0.4rem",
                        borderRadius: "4px",
                        fontSize: "0.7rem",
                        background: action.trigger.includes("GESTURE")
                          ? "rgba(6, 182, 212, 0.2)"
                          : "rgba(100, 116, 139, 0.2)",
                        color: action.trigger.includes("GESTURE") ? "#06B6D4" : "#CBD5E1",
                      }}
                    >
                      {action.trigger}
                    </span>
                  </td>
                  <td>
                    {action.success ? (
                      <span style={{ color: "#10B981", display: "flex", alignItems: "center", gap: "0.2rem" }}>
                        <Check size={14} /> OK ({Math.round(action.latency_ms)}ms)
                      </span>
                    ) : (
                      <span style={{ color: "#F43F5E", display: "flex", alignItems: "center", gap: "0.2rem" }}>
                        <X size={14} /> Failed
                      </span>
                    )}
                  </td>
                  <td style={{ color: "#94A3B8", fontSize: "0.75rem" }}>
                    {action.error_message || `State -> ${action.state}`}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

