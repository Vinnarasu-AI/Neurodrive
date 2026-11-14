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

    print("\n--- 2. Toggling ESP32 Relay ON directly ---")
    try:
        on_req = urllib.request.Request(f"{ESP32_IP}/api/light/on", data=b"", headers={"Authorization": f"Bearer {TOKEN}"})
        with urllib.request.urlopen(on_req, timeout=3) as resp:
            print("ESP32 Direct ON response:", resp.read().decode())
        
        time.sleep(1.5)

        print("\n--- 3. Toggling ESP32 Relay OFF directly ---")
        off_req = urllib.request.Request(f"{ESP32_IP}/api/light/off", data=b"", headers={"Authorization": f"Bearer {TOKEN}"})
        with urllib.request.urlopen(off_req, timeout=3) as resp:
            print("ESP32 Direct OFF response:", resp.read().decode())
    except Exception as e:
        print("Direct ESP32 toggle error:", e)
        return False

    return True

if __name__ == "__main__":
    ok = test_esp32_relay()
    print("Result:", "SUCCESS" if ok else "FAILED")
