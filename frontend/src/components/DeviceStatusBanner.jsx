import React, { useState } from "react";
import {
  Cpu,
  Wifi,
  CheckCircle2,
  AlertCircle,
  Play,
  Square,
  Link,
  Unlink,
  Radio,
} from "lucide-react";

export default function DeviceStatusBanner({
  npgStatus = {},
  relayStatus = {},
  quality = {},
  sampleRate = 0,
  onConnectNpg,
  onDisconnectNpg,
  onStartAcq,
  onStopAcq,
  onSetSimulation,
}) {
  const isNpgConnected = npgStatus.connected;
  const isStreaming = npgStatus.is_streaming;
  const isRelayConnected = relayStatus.connected;
  const isGoodQuality = quality.is_good;
  const isMock = npgStatus.is_mock;
  const sourceLabel = isMock ? "SIMULATION" : "REAL HARDWARE";

  const [selectedPort, setSelectedPort] = useState(
    npgStatus.port && npgStatus.port !== "SIMULATED" && npgStatus.port !== "DISCONNECTED"
      ? npgStatus.port
      : "AUTO"
  );
  const [selectedBaud, setSelectedBaud] = useState(npgStatus.baud_rate || 230400);

  const handleConnect = () => {
    if (onConnectNpg) {
      onConnectNpg(selectedPort, Number(selectedBaud));
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Top Banner Row */}
      <div className="status-banner">
        {/* 1. NPG Lite USB Status with Source Tag */}
        <div className="status-card">
          <div
            className="status-icon-wrapper"
            style={{
              background: isNpgConnected
                ? "rgba(16, 185, 129, 0.15)"
                : "rgba(244, 63, 94, 0.15)",
              color: isNpgConnected ? "#10B981" : "#F43F5E",
            }}
          >
            <Cpu size={24} />
          </div>
          <div className="status-info">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span className="status-label">NPG Lite Acquisition Board</span>
              {/* Distinct Badge for Real Hardware vs Simulation */}
              <span
                style={{
                  fontSize: "0.65rem",
                  fontWeight: 800,
                  padding: "0.15rem 0.45rem",
                  borderRadius: "6px",
                  textTransform: "uppercase",
                  background: isMock
                    ? "rgba(245, 158, 11, 0.2)"
                    : "rgba(6, 182, 212, 0.2)",
                  color: isMock ? "#F59E0B" : "#06B6D4",
                  border: `1px solid ${isMock ? "#F59E0B" : "#06B6D4"}`,
                }}
              >
                {sourceLabel}
              </span>
            </div>

            <span className="status-value">
              <span
                className={`pulse-dot ${isNpgConnected ? "pulse-green" : "pulse-red"
                  }`}
              />
              {isNpgConnected ? "Connected" : "Disconnected"}
              <span style={{ fontSize: "0.75rem", color: "#94A3B8", marginLeft: "0.25rem" }}>
                ({npgStatus.port || "N/A"})
              </span>
            </span>
            <span style={{ fontSize: "0.75rem", color: "#64748B" }}>
              Rate: {sampleRate || 0} Hz • Ch1 Vertical EOG • {isStreaming ? "Streaming" : "Idle"}
            </span>
          </div>
        </div>

        {/* 2. ESP32 Relay Wi-Fi Status */}
        <div className="status-card">
          <div
            className="status-icon-wrapper"
            style={{
              background: isRelayConnected
                ? "rgba(59, 130, 246, 0.15)"
                : "rgba(244, 63, 94, 0.15)",
              color: isRelayConnected ? "#3B82F6" : "#F43F5E",
            }}
          >
            <Wifi size={24} />
          </div>
          <div className="status-info">
            <span className="status-label">ESP32 Wi-Fi Relay</span>
            <span className="status-value">
              <span
                className={`pulse-dot ${isRelayConnected ? "pulse-green" : "pulse-red"
                  }`}
              />
              {isRelayConnected ? "Connected" : "Offline"}
              <span style={{ fontSize: "0.75rem", color: "#94A3B8", marginLeft: "0.25rem" }}>
                ({relayStatus.url || "N/A"})
              </span>
            </span>
            <span style={{ fontSize: "0.75rem", color: "#64748B" }}>
              Auth: Bearer Token • Relay: {relayStatus.state || "OFF"}
            </span>
          </div>
        </div>

        {/* 3. Signal Quality & Calibration Status */}
        <div className="status-card">
          <div
            className="status-icon-wrapper"
            style={{
              background: isGoodQuality
                ? "rgba(16, 185, 129, 0.15)"
                : "rgba(245, 158, 11, 0.15)",
              color: isGoodQuality ? "#10B981" : "#F59E0B",
            }}
          >
            {isGoodQuality ? <CheckCircle2 size={24} /> : <AlertCircle size={24} />}
          </div>
          <div className="status-info">
            <span className="status-label">EOG Signal Quality</span>
            <span className="status-value">
              {quality.score || 0}% • {quality.status || "IDLE"}
            </span>
            <span style={{ fontSize: "0.75rem", color: "#64748B" }}>
              SNR: {quality.snr_db || 0} dB • Artifacts: Minimal
            </span>
          </div>
        </div>
      </div>

      {/* Hardware Control Strip */}
      <div
        style={{
          background: "var(--bg-card)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "12px",
          padding: "0.75rem 1.25rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "0.75rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
          <label style={{ fontSize: "0.8rem", color: "#94A3B8", fontWeight: 600 }}>COM Port:</label>
          <select
            value={selectedPort}
            onChange={(e) => setSelectedPort(e.target.value)}
            style={{
              padding: "0.4rem 0.6rem",
              background: "#090D16",
              color: "#F8FAFC",
              border: "1px solid var(--border-subtle)",
              borderRadius: "6px",
              fontSize: "0.8rem",
            }}
          >
            <option value="AUTO">AUTO (Scan for NPG Lite)</option>
            {(npgStatus.available_ports || []).map((p) => (
              <option key={p.device} value={p.device}>
                {p.device} ({p.description})
              </option>
            ))}
          </select>

          <label style={{ fontSize: "0.8rem", color: "#94A3B8", fontWeight: 600, marginLeft: "0.4rem" }}>
            Baud:
          </label>
          <select
            value={selectedBaud}
            onChange={(e) => setSelectedBaud(e.target.value)}
            style={{
              padding: "0.4rem 0.6rem",
              background: "#090D16",
              color: "#F8FAFC",
              border: "1px solid var(--border-subtle)",
              borderRadius: "6px",
              fontSize: "0.8rem",
            }}
          >
            <option value={230400}>230400 (Default NPG Lite)</option>
            <option value={115200}>115200 (Standard)</option>
          </select>

          {isNpgConnected && !isMock ? (
            <button className="btn btn-rose" style={{ padding: "0.4rem 0.8rem" }} onClick={onDisconnectNpg}>
              <Unlink size={14} /> Disconnect
            </button>
          ) : (
            <button className="btn btn-cyan" style={{ padding: "0.4rem 0.8rem" }} onClick={handleConnect}>
              <Link size={14} /> Connect NPG Lite
            </button>
          )}

          {/* Acquisition Start/Stop */}
          <button
            className="btn btn-secondary"
            style={{ padding: "0.4rem 0.8rem" }}
            onClick={isStreaming ? onStopAcq : onStartAcq}
          >
            {isStreaming ? (
              <>
                <Square size={14} color="#F43F5E" /> Stop Acquisition
              </>
            ) : (
              <>
                <Play size={14} color="#10B981" /> Start Acquisition
              </>
            )}
          </button>
        </div>

        {/* Mode Toggle: Real vs Simulation */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ fontSize: "0.75rem", color: "#94A3B8" }}>Mode:</span>
          <button
            className={`btn ${!isMock ? "btn-cyan" : "btn-secondary"}`}
            style={{ padding: "0.35rem 0.75rem", fontSize: "0.75rem" }}
            onClick={() => onSetSimulation(false)}
          >
            Real Hardware
          </button>
          <button
            className={`btn ${isMock ? "btn-cyan" : "btn-secondary"}`}
            style={{ padding: "0.35rem 0.75rem", fontSize: "0.75rem" }}
            onClick={() => onSetSimulation(true)}
          >
            Simulation
          </button>
        </div>
      </div>
    </div>
  );
}
