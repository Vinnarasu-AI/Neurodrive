import React, { useState } from "react";
import { Sliders, Eye, RotateCcw, X, Home, Gamepad2, Navigation } from "lucide-react";

export default function CalibrationModal({
  isOpen,
  onClose,
  calibrationStatus = {},
  onStartCalibration,
  onResetCalibration,
}) {
  const [selectedTarget, setSelectedTarget] = useState("smart_home"); // "smart_home", "game", or "wheelchair"

  if (!isOpen) return null;

  const stage = calibrationStatus.stage;
  const isCalibrating = calibrationStatus.is_calibrating;

  const currentProf = selectedTarget === "game"
    ? calibrationStatus.game || {}
    : selectedTarget === "wheelchair"
    ? calibrationStatus.wheelchair || {}
    : calibrationStatus.smart_home || {};

  const isTargetCalibrated = currentProf.calibrated;

  const handleStart = () => {
    if (onStartCalibration) {
      onStartCalibration(selectedTarget);
    }
  };

  const handleReset = () => {
    if (onResetCalibration) {
      onResetCalibration(selectedTarget);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Sliders size={20} color="#06B6D4" />
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700 }}>Guided EOG Calibration</h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "#94A3B8", cursor: "pointer" }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Target Profile Switcher Tabs */}
        <div style={{ display: "flex", background: "#0D1322", padding: "0.3rem", borderRadius: "8px", gap: "0.4rem", border: "1px solid var(--border-subtle)" }}>
          <button
            onClick={() => setSelectedTarget("smart_home")}
            style={{
              flex: 1,
              padding: "0.5rem",
              borderRadius: "6px",
              border: "none",
              cursor: "pointer",
              fontSize: "0.8rem",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.4rem",
              background: selectedTarget === "smart_home" ? "#1E293B" : "transparent",
              color: selectedTarget === "smart_home" ? "#06B6D4" : "#94A3B8",
            }}
          >
            <Home size={14} /> Smart Home Profile
          </button>
          <button
            onClick={() => setSelectedTarget("game")}
            style={{
              flex: 1,
              padding: "0.5rem",
              borderRadius: "6px",
              border: "none",
              cursor: "pointer",
              fontSize: "0.8rem",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.4rem",
              background: selectedTarget === "game" ? "#1E293B" : "transparent",
              color: selectedTarget === "game" ? "#10B981" : "#94A3B8",
            }}
          >
            <Gamepad2 size={14} /> Dino Game Profile
          </button>
          <button
            onClick={() => setSelectedTarget("wheelchair")}
            style={{
              flex: 1,
              padding: "0.5rem",
              borderRadius: "6px",
              border: "none",
              cursor: "pointer",
              fontSize: "0.8rem",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.4rem",
              background: selectedTarget === "wheelchair" ? "#1E293B" : "transparent",
              color: selectedTarget === "wheelchair" ? "#3B82F6" : "#94A3B8",
            }}
          >
            <Navigation size={14} /> Wheelchair Profile
          </button>
        </div>

        <p style={{ fontSize: "0.85rem", color: "#94A3B8" }}>
          {selectedTarget === "game"
            ? "Calibrates quick single-blink trigger amplitude and duration for responsive Dino jumps without false triggers."
            : "Calibrates double-blink envelope threshold and baseline stability for reliable lighting actuation."}
        </p>

        {/* Step-by-Step Interactive Cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
          {/* Step 1: Baseline */}
          <div
            style={{
              padding: "1rem",
              borderRadius: "10px",
              background: stage === "BASELINE" ? "rgba(6, 182, 212, 0.15)" : "#0d1322",
              border: `1px solid ${stage === "BASELINE" ? "#06B6D4" : "#22304E"}`,
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
            }}
          >
            <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "#06B6D4" }}>1</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>Center Gaze Baseline (3 seconds)</div>
              <div style={{ fontSize: "0.75rem", color: "#94A3B8" }}>
                Keep eyes relaxed looking straight ahead at screen center.
              </div>
            </div>
            {stage === "BASELINE" && <span className="pulse-dot pulse-green" style={{ marginLeft: "auto" }} />}
          </div>

          {/* Step 2: Deliberate Blinks */}
          <div
            style={{
              padding: "1rem",
              borderRadius: "10px",
              background: stage === "BLINKS" ? "rgba(245, 158, 11, 0.15)" : "#0d1322",
              border: `1px solid ${stage === "BLINKS" ? "#F59E0B" : "#22304E"}`,
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
            }}
          >
            <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "#F59E0B" }}>2</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>Perform 3-4 Deliberate Blinks (4 seconds)</div>
              <div style={{ fontSize: "0.75rem", color: "#94A3B8" }}>
                Blink naturally and deliberately with a brief pause between each.
              </div>
            </div>
            {stage === "BLINKS" && <span className="pulse-dot pulse-green" style={{ marginLeft: "auto" }} />}
          </div>
        </div>

        {/* Results Overview */}
        <div style={{ background: "#0a0e1a", padding: "0.9rem", borderRadius: "10px", border: "1px solid #22304E" }}>
          <div style={{ fontSize: "0.75rem", color: "#64748B", textTransform: "uppercase", fontWeight: 700, marginBottom: "0.4rem" }}>
            {selectedTarget === "game" ? "Game Calibration Metrics" : "Smart Home Calibration Metrics"}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem", fontSize: "0.85rem" }}>
            <div>Baseline DC: <strong style={{ color: "#F8FAFC" }}>{currentProf.baseline_mean || 2048}</strong></div>
            <div>Baseline Noise (Std): <strong style={{ color: "#F8FAFC" }}>{currentProf.baseline_std || 15}</strong></div>
            <div>Peak Threshold: <strong style={{ color: selectedTarget === "game" ? "#10B981" : "#06B6D4" }}>{currentProf.blink_peak_threshold || 180}</strong></div>
            <div>Profile Status: <strong style={{ color: isTargetCalibrated ? "#10B981" : "#F59E0B" }}>{isTargetCalibrated ? "CALIBRATED" : "PENDING"}</strong></div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "0.5rem" }}>
          <button className="btn btn-secondary" onClick={handleReset} disabled={isCalibrating}>
            <RotateCcw size={14} /> Reset
          </button>
          <button className="btn btn-cyan" onClick={handleStart} disabled={isCalibrating}>
            <Eye size={14} /> {isCalibrating ? "Calibrating..." : `Start ${selectedTarget === "game" ? "Game" : "Smart Home"} Calibration`}
          </button>
        </div>
      </div>
    </div>
  );
}
