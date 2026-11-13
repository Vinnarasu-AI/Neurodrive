export function createSignalWebSocket(onMessage, onStatusChange) {
  const wsUrl = "ws://localhost:8000/ws/stream";
  let socket = null;
  let reconnectTimer = null;
  let isClosing = false;

  function connect() {
    try {
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        if (onStatusChange) onStatusChange(true);
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessage) onMessage(data);
        } catch (e) {
          console.error("WS Parse Error:", e);
        }
      };

      socket.onclose = () => {
        if (onStatusChange) onStatusChange(false);
        if (!isClosing) {
          reconnectTimer = setTimeout(connect, 1500);
        }
      };

      socket.onerror = (err) => {
        socket.close();
      };
    } catch (err) {
      if (!isClosing) reconnectTimer = setTimeout(connect, 2000);
    }
  }

  connect();

  return () => {
    isClosing = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    if (socket) socket.close();
  };
}

