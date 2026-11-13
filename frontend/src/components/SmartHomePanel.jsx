import React from "react";
import { Lightbulb, Power, Zap, AlertTriangle } from "lucide-react";

export default function SmartHomePanel({
  lightState = "OFF",
  onTurnOn,
  onTurnOff,
  isSmartHomeActive = false,
  isSignalGood = true,
  isCalibrated = false,
  latestDoubleBlink = null,
}) {
  const isOn = lightState === "ON";

  return (
    <div className="panel-card">
      <div className="panel-title-bar">
        <div className="panel-title">
          <Lightbulb size={18} color="#F59E0B" />
          Smart Home Light Relay
        </div>
        <span
          style={{
            fontSize: "0.75rem",
            fontWeight: 700,
            padding: "0.2rem 0.6rem",
            borderRadius: "12px",
            background: isOn ? "rgba(234, 179, 8, 0.2)" : "rgba(100, 116, 139, 0.2)",
            color: isOn ? "#EAB308" : "#94A3B8",
          }}
        >
          {isOn ? "LIGHT ON" : "LIGHT OFF"}
        </span>
      </div>

      <div className="light-widget">
        <div className={`bulb-indicator ${isOn ? "bulb-on" : "bulb-off"}`}>
          <Lightbulb size={48} strokeWidth={isOn ? 2.5 : 1.5} />
        </div>

        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "1.1rem", fontWeight: 700 }}>
            {isOn ? "Relay Closed (Light ON)" : "Relay Open (Light OFF)"}
          </div>
          <div style={{ fontSize: "0.8rem", color: "#94A3B8", marginTop: "0.25rem" }}>
            {isSmartHomeActive
              ? "Ready: Perform deliberate Double Blink to toggle"
              : "Smart Home inactive. Gestures disabled."}
          </div>
        </div>

        {/* Double blink visual feedback badge */}
        {latestDoubleBlink && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid #10B981",
              padding: "0.4rem 0.8rem",
              borderRadius: "8px",
              color: "#10B981",
              fontSize: "0.8rem",
              fontWeight: 600,
            }}
          >
            <Zap size={14} />
            Double Blink Triggered ({latestDoubleBlink.gap_ms} ms gap)
          </div>
        )}

        {/* Warning if calibration missing or bad signal */}
        {isSmartHomeActive && (!isCalibrated || !isSignalGood) && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
              background: "rgba(244, 63, 94, 0.1)",
              border: "1px solid #F43F5E",
              padding: "0.4rem 0.75rem",
              borderRadius: "8px",
              color: "#F43F5E",
              fontSize: "0.75rem",
            }}
          >
            <AlertTriangle size={14} />
            {!isCalibrated
              ? "Calibration required before gesture control activates."
              : "Poor signal quality: Gestures temporarily locked."}
          </div>
        )}
      </div>

      {/* Manual Controls */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
        <button
          className={`btn ${isOn ? "btn-secondary" : "btn-emerald"}`}
          onClick={onTurnOn}
          disabled={isOn}
        >
          <Power size={14} /> Manual ON
        </button>
        <button
          className={`btn ${!isOn ? "btn-secondary" : "btn-rose"}`}
          onClick={onTurnOff}
          disabled={!isOn}
        >
          <Power size={14} /> Manual OFF
        </button>
      </div>
    </div>
  );
}

