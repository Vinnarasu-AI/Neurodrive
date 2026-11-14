import urllib.request
import json
import time

ESP32_IP = "http://10.54.195.220"
TOKEN = "neurodrive_secure_token_abc123"

def test_esp32_relay():
    print("--- 1. Testing ESP32 Relay Direct Endpoints ---")
    status_url = f"{ESP32_IP}/api/light/status"
    req = urllib.request.Request(status_url, headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            print("ESP32 Direct Status:", data)
    except Exception as e:
        print("Failed to contact ESP32 directly:", e)
        return False

    print("\n--- 2. Testing Relay Toggle (ON -> OFF) via Backend API ---")
    try:
        on_req = urllib.request.Request("http://127.0.0.1:8000/api/device/relay/on", data=b"", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(on_req, timeout=5) as resp:
            print("Backend Relay ON response:", resp.read().decode())
        
        time.sleep(1.5)

        off_req = urllib.request.Request("http://127.0.0.1:8000/api/device/relay/off", data=b"", headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(off_req, timeout=5) as resp:
            print("Backend Relay OFF response:", resp.read().decode())
    except Exception as e:
        print("Backend Relay control error:", e)
        return False

    return True

def test_npg_lite():
    print("\n--- 3. Testing Real NPG Lite EOG Stream ---")
    status_url = "http://127.0.0.1:8000/api/device/status"
    try:
        with urllib.request.urlopen(status_url, timeout=5) as resp:
            status = json.loads(resp.read().decode())
            npg = status.get("npg_lite", {})
            print("NPG Connected:", npg.get("connected"))
            print("NPG Port:", npg.get("port"))
            print("NPG Board ID:", npg.get("board_id"))
            print("NPG Source:", npg.get("source"))
            print("NPG Measured Sampling Rate:", npg.get("sample_rate_measured"), "Hz")
            print("NPG Signal Quality:", npg.get("signal_quality"))
            return npg.get("connected") and npg.get("source") == "REAL HARDWARE"
    except Exception as e:
        print("Failed to query NPG status:", e)
        return False

if __name__ == "__main__":
    relay_ok = test_esp32_relay()
    npg_ok = test_npg_lite()
    print("\n===============================")
    print(f"ESP32 RELAY TEST: {'PASSED' if relay_ok else 'FAILED'}")
    print(f"NPG LITE TEST:    {'PASSED' if npg_ok else 'FAILED'}")
    print("===============================")
