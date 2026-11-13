import React from "react";
import { Home, Gamepad2, Navigation, CheckCircle2 } from "lucide-react";

export default function ApplicationCards({
  currentMode,
  onActivateSmartHome,
  onActivateGame,
  onActivateWheelchair,
  onDeactivate,
  isCalibrated,
  isSignalGood,
}) {
  const isSmartHomeActive = currentMode === "SMART_HOME_ACTIVE";
  const isGameActive = currentMode === "GAME_ACTIVE";
  const isWheelchairActive = currentMode === "WHEELCHAIR_ACTIVE";

  return (
    <div className="apps-grid">
      {/* 1. Smart Home Automation (Active or Available) */}
      <div className={`app-card ${isSmartHomeActive ? "active" : ""}`}>
        <span
          className={`app-card-badge ${
            isSmartHomeActive ? "badge-active" : "badge-ready"
          }`}
        >
          {isSmartHomeActive ? "Active" : "Available"}
        </span>

        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <div style={{ padding: "0.6rem", background: "rgba(6, 182, 212, 0.15)", borderRadius: "10px", color: "#06B6D4" }}>
              <Home size={24} />
            </div>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>Smart Home Automation</h3>
              <p style={{ fontSize: "0.75rem", color: "#94A3B8" }}>Application 01 • Double-Blink Relay Control</p>
            </div>
          </div>
          <p style={{ fontSize: "0.85rem", color: "#CBD5E1", lineHeight: "1.4", marginBottom: "1.25rem" }}>
            Hands-free lighting and appliance actuation via vertical EOG double blinks. Authenticated local HTTP dispatch to physical ESP32 relay.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.6rem", marginTop: "auto" }}>
          {isSmartHomeActive ? (
            <button
              className="btn btn-rose"
              style={{ width: "100%" }}
              onClick={onDeactivate}
            >
              Deactivate Smart Home
            </button>
          ) : (
            <button
              className="btn btn-cyan"
              style={{ width: "100%" }}
              onClick={onActivateSmartHome}
            >
              Activate Smart Home
            </button>
          )}
        </div>
      </div>

      {/* 2. EOG Dino Game Control (Active or Available) */}
      <div className={`app-card ${isGameActive ? "active" : ""}`}>
        <span
          className={`app-card-badge ${
            isGameActive ? "badge-active" : "badge-ready"
          }`}
        >
          {isGameActive ? "Active" : "Available"}
        </span>

        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <div style={{ padding: "0.6rem", background: "rgba(16, 185, 129, 0.15)", borderRadius: "10px", color: "#10B981" }}>
              <Gamepad2 size={24} />
            </div>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>EOG Dino Runner Game</h3>
              <p style={{ fontSize: "0.75rem", color: "#94A3B8" }}>Application 02 • Single-Blink Jump</p>
            </div>
          </div>
          <p style={{ fontSize: "0.85rem", color: "#CBD5E1", lineHeight: "1.4", marginBottom: "1.25rem" }}>
            Fast-reaction endless runner. Perform one deliberate vertical blink to leap over oncoming cactus obstacles. Completely isolated from relay control.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.6rem", marginTop: "auto" }}>
          {isGameActive ? (
            <button
              className="btn btn-rose"
              style={{ width: "100%" }}
              onClick={onDeactivate}
            >
              Deactivate Game
            </button>
          ) : (
            <button
              className="btn btn-emerald"
              style={{ width: "100%" }}
              onClick={onActivateGame}
            >
              Activate Game Control
            </button>
          )}
        </div>
      </div>

      {/* 3. Assistive Wheelchair Control (Active or Available) */}
      <div className={`app-card ${isWheelchairActive ? "active" : ""}`}>
        <span
          className={`app-card-badge ${
            isWheelchairActive ? "badge-active" : "badge-ready"
          }`}
        >
          {isWheelchairActive ? "Active" : "Available"}
        </span>

        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <div style={{ padding: "0.6rem", background: "rgba(59, 130, 246, 0.15)", borderRadius: "10px", color: "#3B82F6" }}>
              <Navigation size={24} />
            </div>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>Assistive Wheelchair</h3>
              <p style={{ fontSize: "0.75rem", color: "#94A3B8" }}>Application 03 • EEG + Dual EMG</p>
            </div>
          </div>
          <p style={{ fontSize: "0.85rem", color: "#CBD5E1", lineHeight: "1.4", marginBottom: "1.25rem" }}>
            Autonomous wheelchair navigation: CH1 EEG mental focus triggers Forward, CH2 Left EMG turns Left, CH3 Right EMG turns Right, and bilateral fists (CH2+CH3) reverses Backward.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.6rem", marginTop: "auto" }}>
          {isWheelchairActive ? (
            <button
              className="btn btn-rose"
              style={{ width: "100%" }}
              onClick={onDeactivate}
            >
              Deactivate Wheelchair
            </button>
          ) : (
            <button
              className="btn btn-blue"
              style={{
                width: "100%",
                background: "#3B82F6",
                color: "#FFFFFF",
                fontWeight: 700,
                border: "none",
                borderRadius: "8px",
                padding: "0.6rem",
                cursor: "pointer",
              }}
              onClick={onActivateWheelchair}
            >
              Activate Wheelchair Control
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
