import React, { useState, useEffect } from "react";
import {
  Brain,
  Sliders,
  Settings,
  ShieldAlert,
  Power,
  RefreshCw,
} from "lucide-react";

import ApplicationCards from "./components/ApplicationCards";
import DeviceStatusBanner from "./components/DeviceStatusBanner";
import LiveWaveform from "./components/LiveWaveform";
import SmartHomePanel from "./components/SmartHomePanel";
import DinoGame from "./components/DinoGame";
import RoverPanel from "./components/RoverPanel";
import CalibrationModal from "./components/CalibrationModal";
import DiagnosticsModal from "./components/DiagnosticsModal";
import EventLogTable from "./components/EventLogTable";

import {
  fetchAppStatus,
  activateApp,
  deactivateApp,
  fetchDeviceStatus,
  fetchCalibrationStatus,
  startCalibration,
  resetCalibration,
  manualRelayOn,
  manualRelayOff,
  emergencyStop,
  configureSerialPort,
  configureThresholds,
  fetchLogs,
  connectNpg,
  disconnectNpg,
  startAcquisition,
  stopAcquisition,
  setSimulationMode,
  fetchRoverStatus,
  sendRoverCommand,
  sendRoverStop,
  sendRoverSpeed,
} from "./services/api";
import { createSignalWebSocket } from "./services/websocket";

export default function App() {
  // App & Device States
  const [appStatus, setAppStatus] = useState({ current_mode: "IDLE" });
  const [deviceStatus, setDeviceStatus] = useState({
    npg_lite: { connected: false, is_mock: true, source: "SIMULATION" },
    relay: { connected: false, state: "OFF" },
  });
  const [calibrationStatus, setCalibrationStatus] = useState({
    calibrated: false,
    stage: "IDLE",
  });
  const [logs, setLogs] = useState([]);
  const [relayActions, setRelayActions] = useState([]);

  // Live Waveform Stream
  const [rawSamples, setRawSamples] = useState([]);
  const [filteredSamples, setFilteredSamples] = useState([]);
  const [sampleRate, setSampleRate] = useState(500);
  const [quality, setQuality] = useState({ is_good: true, score: 95, status: "GOOD" });
  const [latestDoubleBlink, setLatestDoubleBlink] = useState(null);
  const [latestGameJump, setLatestGameJump] = useState(null);
  const [gameJumpCounter, setGameJumpCounter] = useState(0);

  // MOVO Rover Stream Data
  const [roverStatus, setRoverStatus] = useState({
    connected: false,
    current_command: "STOP",
    command_source: "NONE",
    speed: 140,
  });
  const [movoSignal, setMovoSignal] = useState(null);

  // Modals
  const [isCalibModalOpen, setIsCalibModalOpen] = useState(false);
  const [isDiagModalOpen, setIsDiagModalOpen] = useState(false);

  // Load Initial Status
  const refreshData = async () => {
    try {
      const [app, dev, cal, logData] = await Promise.all([
        fetchAppStatus(),
        fetchDeviceStatus(),
        fetchCalibrationStatus(),
        fetchLogs(),
      ]);
      setAppStatus(app);
      setDeviceStatus(dev);
      setCalibrationStatus(cal);
      setLogs(logData.events || []);
      setRelayActions(logData.relay_actions || []);
    } catch (err) {
      console.warn("Error refreshing backend status:", err);
    }
  };

  useEffect(() => {
    refreshData();
    const interval = setInterval(refreshData, 3000);
    return () => clearInterval(interval);
  }, []);

  // Subscribe to real-time high-speed WebSocket feed
  useEffect(() => {
    const cleanupWs = createSignalWebSocket((data) => {
      if (data.filtered_ch1) setFilteredSamples(data.filtered_ch1);
      if (data.raw_ch1) setRawSamples(data.raw_ch1);
      if (data.quality) setQuality(data.quality);
      if (data.sample_rate !== undefined) setSampleRate(data.sample_rate);
      if (data.latest_double_blink) setLatestDoubleBlink(data.latest_double_blink);
      if (data.latest_game_jump) setLatestGameJump(data.latest_game_jump);
      if (data.game_jump_counter !== undefined) setGameJumpCounter(data.game_jump_counter);
      if (data.rover_status) setRoverStatus(data.rover_status);
      if (data.movo) setMovoSignal(data.movo);
      if (data.calibration) setCalibrationStatus(data.calibration);
      if (data.relay_state) {
        setDeviceStatus((prev) => ({
          ...prev,
          relay: { ...prev.relay, state: data.relay_state },
        }));
      }
      if (data.app_state) setAppStatus(data.app_state);
      if (data.connected !== undefined || data.is_mock !== undefined) {
        setDeviceStatus((prev) => ({
          ...prev,
          npg_lite: {
            ...prev.npg_lite,
            connected: data.connected,
            is_mock: data.is_mock,
            source: data.source || (data.is_mock ? "SIMULATION" : "REAL HARDWARE"),
            port: data.port,
            is_streaming: data.is_streaming,
          },
        }));
      }
    });

    return cleanupWs;
  }, []);

  // Handlers
  const handleActivateSmartHome = async () => {
    try {
      await activateApp("SMART_HOME_ACTIVE");
      await refreshData();
    } catch (err) {
      alert(`Activation Error: ${err.message}`);
    }
  };

  const handleActivateGame = async () => {
    try {
      await activateApp("GAME_ACTIVE");
      await refreshData();
    } catch (err) {
      alert(`Activation Error: ${err.message}`);
    }
  };

  const handleActivateRover = async () => {
    try {
      await activateApp("ROVER_ACTIVE");
      await refreshData();
    } catch (err) {
      alert(`Activation Error: ${err.message}`);
    }
  };

  const handleDeactivate = async () => {
    try {
      await deactivateApp();
      await refreshData();
    } catch (err) {
      alert(`Deactivation Error: ${err.message}`);
    }
  };

  const handleConnectNpg = async (port, baud) => {
    try {
      const res = await connectNpg(port, baud);
      await refreshData();
      if (!res.success) {
        alert(res.message);
      }
    } catch (err) {
      alert(`Connection Error: ${err.message}`);
    }
  };

  const handleDisconnectNpg = async () => {
    try {
      await disconnectNpg();
      await refreshData();
    } catch (err) {
      alert(`Disconnect Error: ${err.message}`);
    }
  };

  const handleStartAcquisition = async () => {
    try {
      await startAcquisition();
      await refreshData();
    } catch (err) {
      alert(`Acquisition start error: ${err.message}`);
    }
  };

  const handleStopAcquisition = async () => {
    try {
      await stopAcquisition();
      await refreshData();
    } catch (err) {
      alert(`Acquisition stop error: ${err.message}`);
    }
  };

  const handleSetSimulation = async (useMock) => {
    try {
      await setSimulationMode(useMock);
      await refreshData();
    } catch (err) {
      alert(`Mode switch error: ${err.message}`);
    }
  };

  const handleManualOn = async () => {
    try {
      await manualRelayOn();
      await refreshData();
    } catch (err) {
      alert(`Relay ON error: ${err.message}`);
    }
  };

  const handleManualOff = async () => {
    try {
      await manualRelayOff();
      await refreshData();
    } catch (err) {
      alert(`Relay OFF error: ${err.message}`);
    }
  };

  const handleEmergencyStop = async () => {
    try {
      await emergencyStop();
      await sendRoverStop();
      await refreshData();
      alert("EMERGENCY STOP: All active gestures and actuators disarmed.");
    } catch (err) {
      alert(`Emergency stop error: ${err.message}`);
    }
  };

  const isSmartHomeActive = appStatus.current_mode === "SMART_HOME_ACTIVE";

  return (
    <div className="dashboard-container">
      {/* Top Header */}
      <header className="header-bar">
        <div className="brand-section">
          <div className="brand-icon">
            <Brain size={26} />
          </div>
          <div>
            <h1 className="brand-title">NEURODRIVE</h1>
            <p className="brand-subtitle">
              Assistive Neural Interface • EOG Smart Home Automation
            </p>
          </div>
        </div>

        <div className="header-controls">
          <button
            className="btn btn-secondary"
            onClick={() => setIsCalibModalOpen(true)}
          >
            <Sliders size={16} /> Calibration
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => setIsDiagModalOpen(true)}
          >
            <Settings size={16} /> Settings
          </button>
          <button className="btn btn-rose" onClick={handleEmergencyStop}>
            <ShieldAlert size={16} /> Emergency Disarm
          </button>
        </div>
      </header>

      {/* Hardware Status Banner with Device Connection Controls & Source Tag */}
      <DeviceStatusBanner
        npgStatus={deviceStatus.npg_lite}
        relayStatus={deviceStatus.relay}
        quality={quality}
        sampleRate={sampleRate}
        onConnectNpg={handleConnectNpg}
        onDisconnectNpg={handleDisconnectNpg}
        onStartAcq={handleStartAcquisition}
        onStopAcq={handleStopAcquisition}
        onSetSimulation={handleSetSimulation}
      />

      {/* Application Cards (Smart Home, Dino Game, MOVO Rover, Wheelchair Disabled) */}
      <ApplicationCards
        currentMode={appStatus.current_mode}
        onActivateSmartHome={handleActivateSmartHome}
        onActivateGame={handleActivateGame}
        onActivateRover={handleActivateRover}
        onDeactivate={handleDeactivate}
        isCalibrated={calibrationStatus.calibrated}
        isSignalGood={quality.is_good}
      />

      {/* Conditional MOVO Rover Dashboard when ROVER_ACTIVE */}
      {appStatus.current_mode === "ROVER_ACTIVE" && (
        <div style={{ marginBottom: "1.5rem" }}>
          <RoverPanel
            isRoverActive={true}
            roverStatus={roverStatus}
            movoSignal={movoSignal}
            onSendCommand={sendRoverCommand}
            onSendStop={sendRoverStop}
            onSetSpeed={sendRoverSpeed}
          />
        </div>
      )}

      {/* Conditional Dino Game when GAME_ACTIVE */}
      {appStatus.current_mode === "GAME_ACTIVE" && (
        <div style={{ marginBottom: "1.5rem" }}>
          <DinoGame
            isGameActive={true}
            latestGameJump={latestGameJump}
            isSignalGood={quality.is_good}
            hardwareSource={deviceStatus.npg_lite?.source || "SIMULATION"}
          />
        </div>
      )}

      {/* Main Signal & Actuation Grid */}
      <div className="main-grid">
        <LiveWaveform
          rawSamples={rawSamples}
          filteredSamples={filteredSamples}
          sampleRate={sampleRate}
          threshold={calibrationStatus.blink_peak_threshold || 250}
          latestDoubleBlink={latestDoubleBlink}
        />

        <SmartHomePanel
          lightState={deviceStatus.relay?.state || "OFF"}
          onTurnOn={handleManualOn}
          onTurnOff={handleManualOff}
          isSmartHomeActive={isSmartHomeActive}
          isSignalGood={quality.is_good}
          isCalibrated={calibrationStatus.calibrated}
          latestDoubleBlink={latestDoubleBlink}
        />
      </div>

      {/* Real-time Audit Trail & History */}
      <EventLogTable logs={logs} relayActions={relayActions} />

      {/* Guided Calibration Modal */}
      <CalibrationModal
        isOpen={isCalibModalOpen}
        onClose={() => setIsCalibModalOpen(false)}
        calibrationStatus={calibrationStatus}
        onStartCalibration={startCalibration}
        onResetCalibration={resetCalibration}
      />

      {/* Diagnostics & Port Settings Modal */}
      <DiagnosticsModal
        isOpen={isDiagModalOpen}
        onClose={() => setIsDiagModalOpen(false)}
        availablePorts={deviceStatus.npg_lite?.available_ports || []}
        currentPort={deviceStatus.npg_lite?.port || "AUTO"}
        isMockSerial={deviceStatus.npg_lite?.is_mock || false}
        onUpdatePort={configureSerialPort}
        onUpdateThresholds={configureThresholds}
        currentThreshold={calibrationStatus.blink_peak_threshold || 250}
      />
    </div>
  );
}
