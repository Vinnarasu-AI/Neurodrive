import React, { useRef, useEffect } from "react";
import { Activity } from "lucide-react";

export default function LiveWaveform({
  rawSamples = [],
  filteredSamples = [],
  sampleRate = 500,
  threshold = 250,
  latestDoubleBlink = null,
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;

    // Clear background
    ctx.fillStyle = "#090D16";
    ctx.fillRect(0, 0, width, height);

    // Draw grid lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += 40) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += 40) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Midline (Zero line for bandpassed signal)
    const midY = height / 2;
    ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(0, midY);
    ctx.lineTo(width, midY);
    ctx.stroke();

    // Draw Threshold Line (positive excursion)
    // Scale factor: assume display range +/- 800 uV/ADC
    const scaleY = (height / 2) / 800;
    const threshY = midY - threshold * scaleY;
    ctx.strokeStyle = "rgba(245, 158, 11, 0.4)";
    ctx.setLineDash([6, 6]);
    ctx.beginPath();
    ctx.moveTo(0, threshY);
    ctx.lineTo(width, threshY);
    ctx.stroke();
    ctx.setLineDash([]); // Reset dash

    // Draw Threshold text
    ctx.fillStyle = "#F59E0B";
    ctx.font = "10px monospace";
    ctx.fillText(`+Threshold: ${Math.round(threshold)}`, 10, threshY - 4);

    // Render Filtered EOG Waveform (Cyan)
    if (filteredSamples.length > 1) {
      ctx.strokeStyle = "#06B6D4";
      ctx.lineWidth = 2;
      ctx.beginPath();

      const sliceLen = filteredSamples.length;
      const stepX = width / (sliceLen - 1);

      for (let i = 0; i < sliceLen; i++) {
        const val = filteredSamples[i];
        const y = midY - val * scaleY;
        const x = i * stepX;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    // Highlight recent double-blink event banner if active (<1s ago)
    if (latestDoubleBlink && Date.now() / 1000 - latestDoubleBlink.timestamp < 1.2) {
      ctx.fillStyle = "rgba(16, 185, 129, 0.15)";
      ctx.fillRect(0, 0, width, height);
      ctx.fillStyle = "#10B981";
      ctx.font = "bold 14px sans-serif";
      ctx.fillText(
        `⚡ DOUBLE BLINK DETECTED! (Gap: ${latestDoubleBlink.gap_ms} ms)`,
        width - 320,
        28
      );
    }
  }, [filteredSamples, threshold, latestDoubleBlink]);

  return (
    <div className="panel-card" style={{ flex: 1 }}>
      <div className="panel-title-bar">
        <div className="panel-title">
          <Activity size={18} color="#06B6D4" />
          Channel 1 — Vertical EOG Signal Stream (500 Hz)
        </div>
        <div style={{ display: "flex", gap: "1rem", fontSize: "0.75rem", color: "#94A3B8" }}>
          <span>Bandpass: 0.5–15 Hz + 50Hz Notch</span>
          <span style={{ color: "#06B6D4", fontWeight: 600 }}>Active Stream</span>
        </div>
      </div>

      <div className="waveform-container">
        <canvas
          ref={canvasRef}
          width={800}
          height={240}
          style={{ width: "100%", height: "100%", display: "block" }}
        />
      </div>
    </div>
  );
}

