const API_BASE = "http://localhost:8000";

export async function fetchAppStatus() {
  const res = await fetch(`${API_BASE}/api/apps/status`);
  if (!res.ok) throw new Error("Failed to fetch application status");
  return res.json();
}

export async function activateApp(mode) {
  const res = await fetch(`${API_BASE}/api/apps/activate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to activate app");
  }
  return res.json();
}

export async function deactivateApp() {
  const res = await fetch(`${API_BASE}/api/apps/deactivate`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to deactivate app");
  return res.json();
}

export async function fetchDeviceStatus() {
  const res = await fetch(`${API_BASE}/api/device/status`);
  if (!res.ok) throw new Error("Failed to fetch device status");
  return res.json();
}

export async function connectNpg(port, baudRate = 230400) {
  const res = await fetch(`${API_BASE}/api/device/npg/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ port, baud_rate: baudRate }),
  });
  if (!res.ok) throw new Error("Failed to connect NPG Lite");
  return res.json();
}

export async function disconnectNpg() {
  const res = await fetch(`${API_BASE}/api/device/npg/disconnect`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to disconnect NPG Lite");
  return res.json();
}

export async function startAcquisition() {
  const res = await fetch(`${API_BASE}/api/device/npg/start_acquisition`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to start acquisition");
  return res.json();
}

export async function stopAcquisition() {
  const res = await fetch(`${API_BASE}/api/device/npg/stop_acquisition`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to stop acquisition");
  return res.json();
}

export async function setSimulationMode(useMock) {
  const res = await fetch(`${API_BASE}/api/device/npg/set_mode`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ use_mock: useMock }),
  });
  if (!res.ok) throw new Error("Failed to switch simulation mode");
  return res.json();
}

export async function fetchCalibrationStatus() {
  const res = await fetch(`${API_BASE}/api/calibration/status`);
  if (!res.ok) throw new Error("Failed to fetch calibration status");
  return res.json();
}

export async function startCalibration(target = "smart_home") {
  const res = await fetch(`${API_BASE}/api/calibration/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target }),
  });
  if (!res.ok) throw new Error("Failed to start calibration");
  return res.json();
}

export async function resetCalibration(target = "smart_home") {
  const res = await fetch(`${API_BASE}/api/calibration/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target }),
  });
  if (!res.ok) throw new Error("Failed to reset calibration");
  return res.json();
}

export async function manualRelayOn() {
  const res = await fetch(`${API_BASE}/api/device/relay/on`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to turn relay ON");
  return res.json();
}

export async function manualRelayOff() {
  const res = await fetch(`${API_BASE}/api/device/relay/off`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to turn relay OFF");
  return res.json();
}

// Assistive Wheelchair REST API calls
export async function fetchWheelchairStatus() {
  const res = await fetch(`${API_BASE}/api/device/wheelchair/status`);
  if (!res.ok) throw new Error("Failed to fetch wheelchair status");
  return res.json();
}

export async function sendWheelchairCommand(command) {
  const res = await fetch(`${API_BASE}/api/device/wheelchair/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command }),
  });
  if (!res.ok) throw new Error("Failed to send wheelchair command");
  return res.json();
}

export async function sendWheelchairStop() {
  const res = await fetch(`${API_BASE}/api/device/wheelchair/stop`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to stop wheelchair");
  return res.json();
}

export async function sendWheelchairSpeed(speed) {
  const res = await fetch(`${API_BASE}/api/device/wheelchair/speed`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ speed }),
  });
  if (!res.ok) throw new Error("Failed to set wheelchair speed");
  return res.json();
}

export async function emergencyStop() {
  const res = await fetch(`${API_BASE}/api/device/emergency_stop`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to trigger emergency stop");
  return res.json();
}

export async function configureSerialPort(port, baudRate = 230400, useMock = false) {
  const res = await fetch(`${API_BASE}/api/device/npg/configure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ port, baud_rate: baudRate, use_mock: useMock }),
  });
  if (!res.ok) throw new Error("Failed to configure serial port");
  return res.json();
}

export async function configureThresholds(thresholds) {
  const res = await fetch(`${API_BASE}/api/device/detector/configure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(thresholds),
  });
  if (!res.ok) throw new Error("Failed to configure detector thresholds");
  return res.json();
}

export async function fetchLogs() {
  const res = await fetch(`${API_BASE}/api/device/logs?limit=40`);
  if (!res.ok) throw new Error("Failed to fetch event logs");
  return res.json();
}
