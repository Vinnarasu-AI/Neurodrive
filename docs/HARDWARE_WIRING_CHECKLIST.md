# Hardware Integration & Electrical Safety Checklist

## 1. Electrical Safety First
- [ ] **NO MAINS VOLTAGE**: Under no circumstances connect 110V/230V AC lines during prototyping.
- [ ] **Low-Voltage Test Load**: Connect a 5V/12V DC power supply and an LED indicator or low-power 12V DC bulb across the relay NO (Normally Open) and COM (Common) terminals.
- [ ] **Laptop Battery Isolation**: As recommended by Upside Down Labs BioAmp guidelines, disconnect your laptop's AC wall charger while running electrode acquisitions. Run on laptop battery power to minimize 50Hz/60Hz ground hum and ensure patient isolation.

---

## 2. NPG Lite (Vertical EOG Channel 1) Setup
- [ ] Board model: Upside Down Labs NPG Lite (ESP32-C6).
- [ ] Electrodes connect **only** to the Proto Playmate BioAmp electrode pads/jacks. Never plug electrode leads into raw ESP32 GPIOs!
- [ ] **Placement for Vertical EOG (Blinks & Vertical Gaze)**:
  - **IN+**: Placed approximately 1.5 cm above the center of the dominant eyebrow.
  - **IN-**: Placed approximately 1.5 cm below the lower eyelid/orbital ridge on the same eye.
  - **REF (Ground)**: Placed on an electrically neutral bony reference site (e.g., earlobe or mastoid process behind the ear).
- [ ] Skin Preparation: Clean skin with an alcohol wipe and allow it to dry before applying gel electrodes.

---

## 3. Dedicated ESP32 Relay Hardware Verification
- [ ] Relay module model: Songle SRD-05VDC-SL-C (or compatible optocoupler module).
- [ ] Power supply: Supply dedicated 5V to Relay `VCC` and `GND`.
- [ ] **Trigger Voltage Compatibility**:
  - Many 5V relay modules require a 5V pull-up on their optocoupler anode. An ESP32 GPIO outputs 3.3V logic.
  - Test if driving `RELAY_PIN` LOW activates the relay LED and produces an audible contact click.
  - If a 3.3V GPIO fails to turn the relay off completely when set HIGH (due to leakage through the 5V pull-up resistor), insert an NPN transistor (e.g. 2N2222) or small level shifter, or power the optocoupler VCC from 3.3V (if JD-VCC jumper is isolated).
- [ ] **Polarity**: Ensure firmware `RELAY_ACTIVE_LOW` is set to match the module logic.
- [ ] **Startup Safe State**: Verify the relay does not cycle/pulse when ESP32 powers on or reconnects to Wi-Fi.

