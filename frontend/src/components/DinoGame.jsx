import React, { useRef, useEffect, useState, useCallback } from "react";
import { Play, RotateCcw, Pause, Zap, Award, Flame, ShieldAlert } from "lucide-react";

export default function DinoGame({
  isGameActive = false,
  latestGameJump = null,
  gameJumpCounter = 0,
  isSignalGood = true,
  isCalibrated = false,
  source = "REAL HARDWARE",
}) {
  const canvasRef = useRef(null);

  // Game state
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isGameOver, setIsGameOver] = useState(false);
  const [score, setScore] = useState(0);
  const [highScore, setHighScore] = useState(0);
  const [jumpCount, setJumpCount] = useState(0);
  const [lastBlinkFlash, setLastBlinkFlash] = useState(false);

  // Physics & entity references
  const gameStateRef = useRef({
    dinoY: 0,
    dinoVY: 0,
    isAirborne: false,
    obstacles: [],
    speed: 5.0,
    nextObstacleTimer: 80,
    score: 0,
  });

  const animFrameRef = useRef(null);
  const lastProcessedJumpIdRef = useRef(0);

  // Jump Action triggered by Single-Blink
  const triggerJump = useCallback(() => {
    if (!isPlaying || isPaused || isGameOver) return;
    const g = gameStateRef.current;
    // Ground level is dinoY == 0. Ignore jumps if already airborne
    if (!g.isAirborne && g.dinoY <= 0) {
      g.dinoVY = 12.5; // Jump velocity
      g.isAirborne = true;
      setJumpCount((prev) => prev + 1);
      setLastBlinkFlash(true);
      setTimeout(() => setLastBlinkFlash(false), 250);
    }
  }, [isPlaying, isPaused, isGameOver]);

  // Listen to single-blink jump events coming from WebSocket
  useEffect(() => {
    if (!isGameActive) return;
    if (latestGameJump && latestGameJump.jump_id && latestGameJump.jump_id !== lastProcessedJumpIdRef.current) {
      lastProcessedJumpIdRef.current = latestGameJump.jump_id;
      triggerJump();
    }
  }, [latestGameJump, isGameActive, triggerJump]);

  // Keyboard spacebar fallback for testing
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.code === "Space" && isGameActive) {
        e.preventDefault();
        if (isGameOver) {
          handleRestart();
        } else if (!isPlaying) {
          handleStart();
        } else {
          triggerJump();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isGameActive, isPlaying, isGameOver, triggerJump]);

  const handleStart = () => {
    gameStateRef.current = {
      dinoY: 0,
      dinoVY: 0,
      isAirborne: false,
      obstacles: [{ x: 600, w: 20, h: 36 }],
      speed: 5.5,
      nextObstacleTimer: 100,
      score: 0,
    };
    setScore(0);
    setIsGameOver(false);
    setIsPaused(false);
    setIsPlaying(true);
  };

  const handleRestart = () => {
    handleStart();
  };

  const handleTogglePause = () => {
    setIsPaused((prev) => !prev);
  };

  // Main Canvas Rendering & Physics Game Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    const groundY = height - 32;

    const gameLoop = () => {
      if (isPlaying && !isPaused && !isGameOver) {
        const g = gameStateRef.current;

        // 1. Gravity & Jump Physics
        if (g.isAirborne) {
          g.dinoY += g.dinoVY;
          g.dinoVY -= 0.65; // Gravity
          if (g.dinoY <= 0) {
            g.dinoY = 0;
            g.dinoVY = 0;
            g.isAirborne = false;
          }
        }

        // 2. Obstacles motion
        for (let i = 0; i < g.obstacles.length; i++) {
          g.obstacles[i].x -= g.speed;
        }

        // Remove off-screen obstacles
        if (g.obstacles.length > 0 && g.obstacles[0].x < -30) {
          g.obstacles.shift();
        }

        // Spawn new obstacles with pseudo-random cadence
        g.nextObstacleTimer--;
        if (g.nextObstacleTimer <= 0) {
          const minH = 26;
          const maxH = 46;
          const h = Math.floor(Math.random() * (maxH - minH + 1)) + minH;
          g.obstacles.push({
            x: width + 20,
            w: 18,
            h: h,
          });
          // Difficulty scaling: speed increases slightly, spawn cadence shortens
          g.speed = Math.min(10.5, g.speed + 0.05);
          g.nextObstacleTimer = Math.floor(Math.random() * 40) + 70;
        }

        // 3. Collision Detection
        // Dino box: x: 60, y: groundY - 38 - g.dinoY, w: 32, h: 38
        const dinoBox = {
          x: 60,
          y: groundY - 38 - g.dinoY,
          w: 28,
          h: 36,
        };

        for (const obs of g.obstacles) {
          const obsBox = {
            x: obs.x,
            y: groundY - obs.h,
            w: obs.w,
            h: obs.h,
          };

          if (
            dinoBox.x + 4 < obsBox.x + obsBox.w &&
            dinoBox.x + dinoBox.w - 4 > obsBox.x &&
            dinoBox.y + 4 < obsBox.y + obsBox.h &&
            dinoBox.y + dinoBox.h > obsBox.y
          ) {
            // Collision occurred!
            setIsGameOver(true);
            setIsPlaying(false);
            setHighScore((prev) => Math.max(prev, Math.floor(g.score)));
            break;
          }
        }

        // Score update
        g.score += 0.15;
        setScore(Math.floor(g.score));
      }

      // ================= DRAW FRAME =================
      // Clear sky
      ctx.fillStyle = "#0A0F1D";
      ctx.fillRect(0, 0, width, height);

      // Starfield dots
      ctx.fillStyle = "rgba(255, 255, 255, 0.25)";
      ctx.fillRect(80, 25, 2, 2);
      ctx.fillRect(220, 45, 2, 2);
      ctx.fillRect(450, 30, 2, 2);
      ctx.fillRect(680, 50, 2, 2);

      // Ground Line
      ctx.strokeStyle = "#22304E";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(0, groundY);
      ctx.lineTo(width, groundY);
      ctx.stroke();

      // Ground decorative dashes
      ctx.strokeStyle = "rgba(6, 182, 212, 0.3)";
      ctx.lineWidth = 1;
      const scrollOffset = (Date.now() / 15) % 30;
      for (let x = -scrollOffset; x < width; x += 30) {
        ctx.beginPath();
        ctx.moveTo(x, groundY + 8);
        ctx.lineTo(x + 10, groundY + 8);
        ctx.stroke();
      }

      const g = gameStateRef.current;
      const dinoScreenY = groundY - 38 - g.dinoY;

      // Draw Dino (Pixel-art cyber style)
      ctx.fillStyle = isGameOver ? "#F43F5E" : "#06B6D4";
      // Body
      ctx.fillRect(60, dinoScreenY, 28, 32);
      // Head
      ctx.fillRect(72, dinoScreenY - 8, 20, 16);
      // Eye
      ctx.fillStyle = isGameOver ? "#FFF" : "#0B0F19";
      ctx.fillRect(84, dinoScreenY - 4, 4, 4);
      // Legs (running animation)
      ctx.fillStyle = isGameOver ? "#F43F5E" : "#06B6D4";
      const legOffset = g.isAirborne ? 0 : Math.sin(Date.now() / 60) * 4;
      ctx.fillRect(64, dinoScreenY + 32, 6, 6 + legOffset);
      ctx.fillRect(78, dinoScreenY + 32, 6, 6 - legOffset);

      // Draw Obstacles (Cyber Cacti)
      ctx.fillStyle = "#10B981";
      for (const obs of g.obstacles) {
        // Main stem
        ctx.fillRect(obs.x + 4, groundY - obs.h, obs.w - 8, obs.h);
        // Left arm
        if (obs.h > 30) {
          ctx.fillRect(obs.x, groundY - obs.h + 8, 4, 12);
        }
        // Right arm
        if (obs.h > 35) {
          ctx.fillRect(obs.x + obs.w - 4, groundY - obs.h + 12, 4, 10);
        }
      }

      // Blink feedback indicator in canvas
      if (lastBlinkFlash) {
        ctx.fillStyle = "rgba(6, 182, 212, 0.25)";
        ctx.fillRect(0, 0, width, height);
        ctx.fillStyle = "#06B6D4";
        ctx.font = "bold 14px monospace";
        ctx.fillText("⚡ SINGLE BLINK: JUMP!", 20, 30);
      }

      animFrameRef.current = requestAnimationFrame(gameLoop);
    };

    animFrameRef.current = requestAnimationFrame(gameLoop);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [isPlaying, isPaused, isGameOver, lastBlinkFlash]);

  return (
    <div className="panel-card" style={{ gridColumn: "1 / -1" }}>
      <div className="panel-title-bar">
        <div className="panel-title">
          <Flame size={20} color="#06B6D4" />
          EOG Dino Runner • Hands-Free Endless Runner
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", fontSize: "0.8rem" }}>
          <span style={{ color: "#94A3B8" }}>
            Control: <strong style={{ color: "#06B6D4" }}>1 Deliberate Blink = Jump</strong>
          </span>
          <span style={{ color: "#F59E0B" }}>
            <Award size={14} style={{ display: "inline", verticalAlign: "middle", marginRight: "3px" }} />
            High Score: {highScore}
          </span>
          <span style={{ color: "#10B981", fontWeight: 700 }}>Score: {score}</span>
        </div>
      </div>

      {/* Main Canvas Container */}
      <div style={{ position: "relative", width: "100%", height: "220px", background: "#0A0F1D", borderRadius: "10px", overflow: "hidden", border: "1px solid var(--border-subtle)" }}>
        <canvas
          ref={canvasRef}
          width={900}
          height={220}
          style={{ width: "100%", height: "100%", display: "block" }}
        />

        {/* Overlay when Game Over */}
        {isGameOver && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: "rgba(10, 15, 29, 0.85)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.85rem",
            }}
          >
            <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "#F43F5E" }}>GAME OVER</div>
            <div style={{ fontSize: "0.9rem", color: "#CBD5E1" }}>
              Score: <strong>{score}</strong> • Jumps Performed: <strong>{jumpCount}</strong>
            </div>
            <button className="btn btn-cyan" onClick={handleRestart}>
              <RotateCcw size={15} /> Play Again (Blink or Click)
            </button>
          </div>
        )}

        {/* Overlay when Idle / Not Started */}
        {!isPlaying && !isGameOver && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              background: "rgba(10, 15, 29, 0.75)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.85rem",
            }}
          >
            <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#F8FAFC" }}>
              {isGameActive ? "Ready to Play!" : "Activate EOG Game Control Above"}
            </div>
            <p style={{ fontSize: "0.85rem", color: "#94A3B8", maxWidth: "420px", textAlign: "center" }}>
              Perform one sharp, deliberate vertical blink to leap over the obstacles. Jump cooldown prevents accidental double jumps.
            </p>
            {isGameActive ? (
              <button className="btn btn-cyan" onClick={handleStart}>
                <Play size={15} /> Start Game (or Space)
              </button>
            ) : (
              <div style={{ fontSize: "0.8rem", color: "#F59E0B" }}>
                Select "Activate Game Control" on the Application Card above to begin.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Game Control Bar & Stats */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem", marginTop: "0.25rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          {isPlaying && (
            <button className="btn btn-secondary" onClick={handleTogglePause}>
              {isPaused ? <Play size={14} /> : <Pause size={14} />} {isPaused ? "Resume" : "Pause"}
            </button>
          )}
          {isPlaying && (
            <button className="btn btn-secondary" onClick={handleRestart}>
              <RotateCcw size={14} /> Restart
            </button>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "1rem", fontSize: "0.8rem" }}>
          <span style={{ color: "#94A3B8" }}>
            EOG Jumps: <strong style={{ color: "#06B6D4" }}>{jumpCount}</strong>
          </span>
          <span style={{ color: "#94A3B8" }}>
            Source: <strong style={{ color: source === "REAL HARDWARE" ? "#06B6D4" : "#F59E0B" }}>{source}</strong>
          </span>
          <span style={{ color: isSignalGood ? "#10B981" : "#F43F5E" }}>
            Quality: <strong>{isSignalGood ? "Optimal" : "Check Contact"}</strong>
          </span>
        </div>
      </div>
    </div>
  );
}

