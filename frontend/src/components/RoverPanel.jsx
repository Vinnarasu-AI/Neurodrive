import React from "react";
import {
  Truck,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  OctagonAlert,
  Wifi,
  Activity,
  Zap,
  Gauge,
} from "lucide-react";

export default function RoverPanel({
  isRoverActive,
  roverStatus,
  movoSignal,
  onSendCommand,
  onSendStop,
  onSetSpeed,
}) {
  const currentCommand = roverStatus?.current_command || "STOP";
  const commandSource = roverStatus?.command_source || "NONE";
  const isConnected = roverStatus?.connected || false;
  const currentSpeed = roverStatus?.speed || 140;

  // EMG & EEG Real-Time Metrics
  const eegFocus = movoSignal?.eeg?.focus_index || 0.0;
  const isEEGIntent = movoSignal?.eeg?.intent_active || false;
  const emgLeftActive = movoSignal?.emg_left?.active || false;
  const emgLeftEnv = movoSignal?.emg_left?.envelope || 0.0;
  const emgRightActive = movoSignal?.emg_right?.active || false;
  const emgRightEnv = movoSignal?.emg_right?.envelope || 0.0;
  const detectedDecision = movoSignal?.decision || "STOP";

  return (
    <div
      style={{
        background: "rgba(15, 23, 42, 0.8)",
        borderRadius: "16px",
        border: isRoverActive
          ? "1px solid rgba(245, 158, 11, 0.4)"
          : "1px solid rgba(255, 255, 255, 0.08)",
        padding: "1.5rem",
        boxShadow: isRoverActive
          ? "0 0 25px rgba(245, 158, 11, 0.15)"
          : "none",
        backdropFilter: "blur(12px)",
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
      }}
    >
      {/* Header Banner */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          paddingBottom: "0.75rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div
            style={{
              padding: "0.5rem",
              background: "rgba(245, 158, 11, 0.15)",
              color: "#F59E0B",
              borderRadius: "10px",
            }}
          >
            <Truck size={22} />
          </div>
          <div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, margin: 0 }}>
              MOVO Delivery Rover Dashboard
            </h3>
            <p style={{ fontSize: "0.75rem", color: "#94A3B8", margin: 0 }}>
              ESP32 L298N Motor Driver • 10.54.195.37:80 • Watchdog 700ms
            </p>
          </div>
        </div>

        <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
          <span
            style={{
              padding: "0.25rem 0.6rem",
              borderRadius: "20px",
              fontSize: "0.75rem",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: "0.3rem",
              background: isConnected
                ? "rgba(16, 185, 129, 0.15)"
                : "rgba(244, 63, 94, 0.15)",
              color: isConnected ? "#10B981" : "#F43F5E",
              border: isConnected
                ? "1px solid rgba(16, 185, 129, 0.3)"
                : "1px solid rgba(244, 63, 94, 0.3)",
            }}
          >
            <Wifi size={14} /> {isConnected ? "ESP32 LINKED" : "OFFLINE / MOCK"}
          </span>

          <span
            style={{
              padding: "0.25rem 0.6rem",
              borderRadius: "20px",
              fontSize: "0.75rem",
              fontWeight: 700,
              background: isRoverActive
                ? "rgba(245, 158, 11, 0.2)"
                : "rgba(148, 163, 184, 0.1)",
              color: isRoverActive ? "#F59E0B" : "#94A3B8",
            }}
          >
            {isRoverActive ? "CONTROL ACTIVE" : "STANDBY"}
          </span>
        </div>
      </div>

      {/* Multimodal Neural & Muscular Channel Status */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "1rem",
        }}
      >
        {/* CH1: EEG Focus (Forward) */}
        <div
          style={{
            background: "rgba(2, 6, 23, 0.4)",
            borderRadius: "10px",
            padding: "0.85rem",
            border: isEEGIntent
              ? "1px solid #06B6D4"
              : "1px solid rgba(255, 255, 255, 0.05)",
          }}
        >
          <div
            style={{
              fontSize: "0.75rem",
              color: "#94A3B8",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            <Activity size={14} color="#06B6D4" /> CH1: EEG Focus (Forward)
          </div>
          <div
            style={{
              fontSize: "1.2rem",
              fontWeight: 700,
              marginTop: "0.3rem",
              color: isEEGIntent ? "#06B6D4" : "#F8FAFC",
            }}
          >
            {isEEGIntent ? "INTENT ACTIVE" : `Ratio: ${eegFocus.toFixed(2)}`}
          </div>
          <div style={{ fontSize: "0.7rem", color: "#64748B", marginTop: "0.2rem" }}>
            Threshold: 1.50 (Beta / Alpha)
          </div>
        </div>

        {/* CH2: Left Forearm EMG (Turn Left) */}
        <div
          style={{
            background: "rgba(2, 6, 23, 0.4)",
            borderRadius: "10px",
            padding: "0.85rem",
            border: emgLeftActive
              ? "1px solid #10B981"
              : "1px solid rgba(255, 255, 255, 0.05)",
          }}
        >
          <div
            style={{
              fontSize: "0.75rem",
              color: "#94A3B8",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            <Zap size={14} color="#10B981" /> CH2: Left EMG (Left)
          </div>
          <div
            style={{
              fontSize: "1.2rem",
              fontWeight: 700,
              marginTop: "0.3rem",
              color: emgLeftActive ? "#10B981" : "#F8FAFC",
            }}
          >
            {emgLeftActive ? "FIST CONTRACTED" : `${emgLeftEnv.toFixed(1)} uV`}
          </div>
          <div style={{ fontSize: "0.7rem", color: "#64748B", marginTop: "0.2rem" }}>
            State: {emgLeftActive ? "Active" : "Relaxed"}
          </div>
        </div>

        {/* CH3: Right Forearm EMG (Turn Right) */}
        <div
          style={{
            background: "rgba(2, 6, 23, 0.4)",
            borderRadius: "10px",
            padding: "0.85rem",
            border: emgRightActive
              ? "1px solid #8B5CF6"
              : "1px solid rgba(255, 255, 255, 0.05)",
          }}
        >
          <div
            style={{
              fontSize: "0.75rem",
              color: "#94A3B8",
              display: "flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            <Zap size={14} color="#8B5CF6" /> CH3: Right EMG (Right)
          </div>
          <div
            style={{
              fontSize: "1.2rem",
              fontWeight: 700,
              marginTop: "0.3rem",
              color: emgRightActive ? "#8B5CF6" : "#F8FAFC",
            }}
          >
            {emgRightActive ? "FIST CONTRACTED" : `${emgRightEnv.toFixed(1)} uV`}
          </div>
          <div style={{ fontSize: "0.7rem", color: "#64748B", marginTop: "0.2rem" }}>
            State: {emgRightActive ? "Active" : "Relaxed"}
          </div>
        </div>
      </div>

      {/* Direction & Live Actuator Center Console */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.2fr 1fr",
          gap: "1.25rem",
          alignItems: "center",
        }}
      >
        {/* Status & Source Pill */}
        <div
          style={{
            background: "rgba(2, 6, 23, 0.5)",
            padding: "1rem",
            borderRadius: "12px",
            border: "1px solid rgba(255, 255, 255, 0.05)",
          }}
        >
          <div style={{ fontSize: "0.8rem", color: "#94A3B8", marginBottom: "0.3rem" }}>
            Active Rover Motion State:
          </div>
          <div
            style={{
              fontSize: "1.8rem",
              fontWeight: 800,
              color: currentCommand === "STOP" ? "#94A3B8" : "#F59E0B",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            {currentCommand}
            <span
              style={{
                fontSize: "0.75rem",
                padding: "0.2rem 0.5rem",
                borderRadius: "12px",
                background: "rgba(255, 255, 255, 0.1)",
                color: "#E2E8F0",
                fontWeight: 600,
              }}
            >
              Trigger: {commandSource}
            </span>
          </div>

          <div
            style={{
              marginTop: "0.75rem",
              display: "flex",
              alignItems: "center",
              gap: "0.6rem",
              fontSize: "0.8rem",
              color: "#94A3B8",
            }}
          >
            <Gauge size={16} /> Motor PWM: <strong>{currentSpeed} / 220</strong>
            <button
              onClick={() => onSetSpeed(140)}
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "#CBD5E1",
                padding: "0.2rem 0.5rem",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "0.7rem",
              }}
            >
              Low (140)
            </button>
            <button
              onClick={() => onSetSpeed(180)}
              style={{
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.1)",
                color: "#CBD5E1",
                padding: "0.2rem 0.5rem",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "0.7rem",
              }}
            >
              Med (180)
            </button>
          </div>
        </div>

        {/* Manual Direct Operator D-PAD */}
        <div>
          <div
            style={{
              fontSize: "0.75rem",
              fontWeight: 700,
              color: "#94A3B8",
              marginBottom: "0.5rem",
              textAlign: "center",
            }}
          >
            MANUAL DIRECTIONAL OVERRIDE
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "0.4rem",
              maxWidth: "220px",
              margin: "0 auto",
            }}
          >
            <div />
            <button
              className="btn btn-secondary"
              onClick={() => onSendCommand("FORWARD")}
              style={{ padding: "0.6rem" }}
              title="Manual Forward"
            >
              <ArrowUp size={18} />
            </button>
            <div />

            <button
              className="btn btn-secondary"
              onClick={() => onSendCommand("LEFT")}
              style={{ padding: "0.6rem" }}
              title="Manual Left"
            >
              <ArrowLeft size={18} />
            </button>
            <button
              className="btn btn-rose"
              onClick={onSendStop}
              style={{ padding: "0.6rem", fontWeight: 700 }}
              title="Emergency Stop"
            >
              <OctagonAlert size={18} />
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => onSendCommand("RIGHT")}
              style={{ padding: "0.6rem" }}
              title="Manual Right"
            >
              <ArrowRight size={18} />
            </button>

            <div />
            <button
              className="btn btn-secondary"
              onClick={() => onSendCommand("BACKWARD")}
              style={{ padding: "0.6rem" }}
              title="Manual Backward"
            >
              <ArrowDown size={18} />
            </button>
            <div />
          </div>
        </div>
      </div>
    </div>
  );
}

