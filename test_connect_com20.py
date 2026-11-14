import urllib.request
import json

def connect_npg():
    payload = json.dumps({"port": "COM20", "baud_rate": 230400}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/device/npg/connect",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print("Response:", resp.read().decode())
    except Exception as e:
        print("Error:", e)

def check_status():
    req = urllib.request.Request("http://127.0.0.1:8000/api/device/status")
    with urllib.request.urlopen(req, timeout=5) as resp:
        print("Device Status:", resp.read().decode())

if __name__ == "__main__":
    connect_npg()
    check_status()
