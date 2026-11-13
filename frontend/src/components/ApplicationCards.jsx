import React from "react";
import { Home, Gamepad2, Navigation, Truck, CheckCircle2, Lock } from "lucide-react";

export default function ApplicationCards({
  currentMode,
  onActivateSmartHome,
  onActivateGame,
  onActivateRover,
  onDeactivate,
  isCalibrated,
  isSignalGood,
}) {
  const isSmartHomeActive = currentMode === "SMART_HOME_ACTIVE";
  const isGameActive = currentMode === "GAME_ACTIVE";
  const isRoverActive = currentMode === "ROVER_ACTIVE";

  return (
    <div className="apps-grid">
      {/* 1. Smart Home Automation (Active or Available) */}
      <div className={`app-card ${isSmartHomeActive ? "active" : ""}`}>
        <span
          className={`app-card-badge ${isSmartHomeActive ? "badge-active" : "badge-ready"
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
          className={`app-card-badge ${isGameActive ? "badge-active" : "badge-ready"
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

      {/* 3. MOVO Delivery Rover (Active or Available) */}
      <div className={`app-card ${isRoverActive ? "active" : ""}`}>
        <span
          className={`app-card-badge ${
            isRoverActive ? "badge-active" : "badge-ready"
          }`}
        >
          {isRoverActive ? "Active" : "Available"}
        </span>

        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <div style={{ padding: "0.6rem", background: "rgba(245, 158, 11, 0.15)", borderRadius: "10px", color: "#F59E0B" }}>
              <Truck size={24} />
            </div>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700 }}>MOVO Delivery Rover</h3>
              <p style={{ fontSize: "0.75rem", color: "#94A3B8" }}>Application 03 • EEG + Dual EMG</p>
            </div>
          </div>
          <p style={{ fontSize: "0.85rem", color: "#CBD5E1", lineHeight: "1.4", marginBottom: "1.25rem" }}>
            Ground delivery navigation: CH1 EEG mental focus triggers Forward, while bilateral forearm EMG (CH2/CH3) directs Left, Right, and Reverse.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.6rem", marginTop: "auto" }}>
          {isRoverActive ? (
            <button
              className="btn btn-rose"
              style={{ width: "100%" }}
              onClick={onDeactivate}
            >
              Deactivate Rover
            </button>
          ) : (
            <button
              className="btn btn-amber"
              style={{
                width: "100%",
                background: "#F59E0B",
                color: "#0F172A",
                fontWeight: 700,
                border: "none",
                borderRadius: "8px",
                padding: "0.6rem",
                cursor: "pointer",
              }}
              onClick={onActivateRover}
            >
              Activate MOVO Rover
            </button>
          )}
        </div>
      </div>

      {/* 4. Wheelchair Control (Strictly Coming Soon & Disabled) */}
      <div className="app-card disabled" title="Reserved for future phase - Disabled">
        <span className="app-card-badge badge-disabled">Coming Soon</span>

        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <div style={{ padding: "0.6rem", background: "rgba(148, 163, 184, 0.1)", borderRadius: "10px", color: "#64748B" }}>
              <Navigation size={24} />
            </div>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#94A3B8" }}>Wheelchair Control</h3>
              <p style={{ fontSize: "0.75rem", color: "#64748B" }}>Application 04 • Inactive</p>
            </div>
          </div>
          <p style={{ fontSize: "0.85rem", color: "#64748B", lineHeight: "1.4", marginBottom: "1.25rem" }}>
            Assistive mobility and motorized wheelchair directional steering using sustained eye gestures and safety interlocks.
          </p>
        </div>

        <button className="btn btn-secondary" style={{ width: "100%" }} disabled>
          <Lock size={14} /> Locked (Phase 4)
        </button>
      </div>
    </div>
  );
}
