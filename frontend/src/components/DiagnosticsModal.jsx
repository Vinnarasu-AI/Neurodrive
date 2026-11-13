import React, { useState } from "react";
import { Settings, RefreshCw, X, Save } from "lucide-react";

export default function DiagnosticsModal({
  isOpen,
  onClose,
  availablePorts = [],
  currentPort = "AUTO",
  isMockSerial = false,
  onUpdatePort,
  onUpdateThresholds,
  currentThreshold = 250,
}) {
  const [selectedPort, setSelectedPort] = useState(currentPort);
  const [useMock, setUseMock] = useState(isMockSerial);
  const [minGap, setMinGap] = useState(150);
  const [maxGap, setMaxGap] = useState(850);
  const [refractory, setRefractory] = useState(600);
  const [peakThresh, setPeakThresh] = useState(currentThreshold);
  const [saveMsg, setSaveMsg] = useState("");

  if (!isOpen) return null;

  const handleSavePort = async () => {
    try {
      await onUpdatePort(selectedPort, 230400, useMock);
      setSaveMsg("Port configuration saved successfully!");
      setTimeout(() => setSaveMsg(""), 3000);
    } catch (e) {
      setSaveMsg("Failed to update port.");
    }
  };

  const handleSaveThresholds = async () => {
    try {
      await onUpdateThresholds({
        min_gap_ms: parseInt(minGap),
        max_gap_ms: parseInt(maxGap),
        refractory_ms: parseInt(refractory),
        blink_peak_threshold: parseFloat(peakThresh),
      });
      setSaveMsg("Threshold parameters applied!");
      setTimeout(() => setSaveMsg(""), 3000);
    } catch (e) {
      setSaveMsg("Failed to update thresholds.");
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: "620px" }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Settings size={20} color="#06B6D4" />
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700 }}>Diagnostics & Device Settings</h3>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#94A3B8", cursor: "pointer" }}>
            <X size={20} />
          </button>
        </div>

        {saveMsg && (
          <div style={{ background: "rgba(16, 185, 129, 0.15)", color: "#10B981", padding: "0.5rem", borderRadius: "8px", fontSize: "0.85rem", textAlign: "center" }}>
            {saveMsg}
          </div>
        )}

        {/* Section 1: NPG Lite COM Port Selection */}
        <div style={{ background: "#0d1322", padding: "1rem", borderRadius: "10px", border: "1px solid #22304E", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <h4 style={{ fontSize: "0.95rem", color: "#F8FAFC" }}>NPG Lite Hardware Connection</h4>
          
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <label style={{ fontSize: "0.85rem", color: "#94A3B8", width: "120px" }}>Port:</label>
            <select
              value={selectedPort}
              onChange={(e) => setSelectedPort(e.target.value)}
              style={{ flex: 1, padding: "0.5rem", background: "#131B2E", color: "#FFF", border: "1px solid #22304E", borderRadius: "6px" }}
            >
              <option value="AUTO">AUTO (Auto-detect USB CDC / CP210x)</option>
              {availablePorts.map((p) => (
                <option key={p.device} value={p.device}>
                  {p.device} — {p.description}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <label style={{ fontSize: "0.85rem", color: "#94A3B8", width: "120px" }}>Hardware Mode:</label>
            <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.85rem", color: "#CBD5E1", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={useMock}
                onChange={(e) => setUseMock(e.target.checked)}
              />
              Use Synthetic EOG Generator (Test without physical board)
            </label>
          </div>

          <button className="btn btn-secondary" style={{ alignSelf: "flex-end", marginTop: "0.25rem" }} onClick={handleSavePort}>
            <Save size={14} /> Update Port Setting
          </button>
        </div>

        {/* Section 2: Gesture Detection Parameters */}
        <div style={{ background: "#0d1322", padding: "1rem", borderRadius: "10px", border: "1px solid #22304E", display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          <h4 style={{ fontSize: "0.95rem", color: "#F8FAFC" }}>Double Blink Detection Tuning</h4>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#94A3B8", display: "block", marginBottom: "0.25rem" }}>Min Gap (ms)</label>
              <input
                type="number"
                value={minGap}
                onChange={(e) => setMinGap(e.target.value)}
                style={{ width: "100%", padding: "0.45rem", background: "#131B2E", color: "#FFF", border: "1px solid #22304E", borderRadius: "6px" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#94A3B8", display: "block", marginBottom: "0.25rem" }}>Max Gap (ms)</label>
              <input
                type="number"
                value={maxGap}
                onChange={(e) => setMaxGap(e.target.value)}
                style={{ width: "100%", padding: "0.45rem", background: "#131B2E", color: "#FFF", border: "1px solid #22304E", borderRadius: "6px" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#94A3B8", display: "block", marginBottom: "0.25rem" }}>Refractory Period (ms)</label>
              <input
                type="number"
                value={refractory}
                onChange={(e) => setRefractory(e.target.value)}
                style={{ width: "100%", padding: "0.45rem", background: "#131B2E", color: "#FFF", border: "1px solid #22304E", borderRadius: "6px" }}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "#94A3B8", display: "block", marginBottom: "0.25rem" }}>Blink Threshold (uV)</label>
              <input
                type="number"
                value={peakThresh}
                onChange={(e) => setPeakThresh(e.target.value)}
                style={{ width: "100%", padding: "0.45rem", background: "#131B2E", color: "#FFF", border: "1px solid #22304E", borderRadius: "6px" }}
              />
            </div>
          </div>

          <button className="btn btn-secondary" style={{ alignSelf: "flex-end", marginTop: "0.25rem" }} onClick={handleSaveThresholds}>
            <Save size={14} /> Apply Detection Thresholds
          </button>
        </div>
      </div>
    </div>
  );
}

