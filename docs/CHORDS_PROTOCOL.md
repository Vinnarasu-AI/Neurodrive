# Upside Down Labs / Chords Serial Framing Protocol Specification

This document details the exact hardware packet specification used by Upside Down Labs NPG Lite (and Chords USB firmware family), as decoded by `ChordsPacketDecoder` in `app/serial/chords_decoder.py`.

---

## 1. Physical Serial Parameters
- **Baud Rate**: `230400` bps (default for NPG Lite ESP32-C6) or `115200` bps.
- **Data Bits**: 8
- **Parity**: None
- **Stop Bits**: 1
- **Flow Control**: None
- **Sample Rate**: 500 Hz nominal ($2.0\text{ ms}$ sample interval)

---

## 2. Handshake Commands (ASCII CRLF)
Before or during connection:
- Host sends `WHORU\n`
  - Board replies with identifier string, e.g. `NPG-LITE` or `NPG-LITE-3CH`.
- Host sends `START\n`
  - Board starts streaming continuous binary packets.
- Host sends `STOP\n`
  - Board halts streaming.

---

## 3. Binary Packet Framing (10 Bytes for 3 Channels)

Each packet sent by the board consists of:

| Byte Index | Field Name | Type | Value / Description |
|---|---|---|---|
| `0` | `SYNC_BYTE_1` | `uint8` | `0xC7` (Sync marker byte 1) |
| `1` | `SYNC_BYTE_2` | `uint8` | `0x7C` (Sync marker byte 2) |
| `2` | `COUNTER` | `uint8` | `0x00 - 0xFF` (Rolling sequence counter) |
| `3` | `CH1_HIGH` | `uint8` | Channel 1 High Byte: `(val >> 8) & 0xFF` |
| `4` | `CH1_LOW` | `uint8` | Channel 1 Low Byte: `val & 0xFF` |
| `5` | `CH2_HIGH` | `uint8` | Channel 2 High Byte |
| `6` | `CH2_LOW` | `uint8` | Channel 2 Low Byte |
| `7` | `CH3_HIGH` | `uint8` | Channel 3 High Byte |
| `8` | `CH3_LOW` | `uint8` | Channel 3 Low Byte |
| `9` | `END_BYTE` | `uint8` | `0x01` (Packet termination delimiter) |

### Sample Reassembly
For Channel $k$ ($0$-indexed):
$$\text{Sample}_k = (\text{Payload}[2k] \ll 8) \mid \text{Payload}[2k + 1]$$
The value is a 12-bit unsigned ADC reading ranging from `0` to `4095` ($V_{ref} \approx 3.3\text{V}$), with baseline approximately around `2048`.

---

## 4. Robust Parser & Error Recovery
`ChordsPacketDecoder` enforces:
1. **Sliding Sync Search**: If corrupt bytes or noise are received, buffer scans until the `0xC7, 0x7C` doublet is located.
2. **Boundary Validation**: The byte at index $3 + 2 \times N$ is strictly verified to equal `0x01`. If false, only the first sync byte is dropped to recover overlapping alignment without desyncing.
3. **Drop Tracking**: The rolling packet counter detects skipped packets if serial buffers or USB transfer queues overflow.

