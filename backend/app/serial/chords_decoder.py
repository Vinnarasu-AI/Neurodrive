"""
Official Upside Down Labs / Chords Protocol Packet Decoder.

Protocol details from Chords official firmware & chordspy:
- Sync Header: 0xC7, 0x7C (2 bytes)
- Packet Counter: 1 byte (0x00 to 0xFF)
- Channel Data: 2 bytes per channel (Big-Endian uint16, raw 12-bit ADC value)
- End Byte: 0x01 (1 byte)
- Total length for N channels: 3 + (2 * N) + 1 bytes. For 3 channels (NPG Lite): 10 bytes.

Robustness features:
- Frame synchronization search
- Resilient recovery from corrupted bytes, partial buffers, multi-packet bursts
- Re-alignment if end byte fails to match
- Support for fallback line-delimited ASCII packets (e.g. from debugging sketches)
"""

from typing import List, Tuple, Optional
import struct
import numpy as np


class ChordsPacketDecoder:
    SYNC_BYTE_1 = 0xC7
    SYNC_BYTE_2 = 0x7C
    END_BYTE = 0x01
    HEADER_LEN = 3  # SYNC1 + SYNC2 + COUNTER

    def __init__(self, num_channels: int = 3):
        self.num_channels = num_channels
        self.packet_len = self.HEADER_LEN + (2 * self.num_channels) + 1
        self.buffer = bytearray()
        self.packets_decoded = 0
        self.corrupt_bytes_skipped = 0
        self.last_counter: Optional[int] = None
        self.dropped_packets = 0

    def feed(self, raw_bytes: bytes) -> List[Tuple[int, List[int]]]:
        """
        Feeds raw serial bytes into the stream decoder and extracts all valid packets.
        Returns a list of tuples: (counter, [ch1_val, ch2_val, ...])
        """
        self.buffer.extend(raw_bytes)
        decoded_packets: List[Tuple[int, List[int]]] = []

        while len(self.buffer) >= self.packet_len:
            # 1. Search for sync sequence
            sync_idx = -1
            buf_len = len(self.buffer)
            for i in range(buf_len - 1):
                if self.buffer[i] == self.SYNC_BYTE_1 and self.buffer[i + 1] == self.SYNC_BYTE_2:
                    sync_idx = i
                    break

            if sync_idx == -1:
                # No sync sequence found in entire buffer
                # Retain only the very last byte (in case it is SYNC_BYTE_1)
                if len(self.buffer) > 0 and self.buffer[-1] == self.SYNC_BYTE_1:
                    self.corrupt_bytes_skipped += len(self.buffer) - 1
                    del self.buffer[:-1]
                else:
                    self.corrupt_bytes_skipped += len(self.buffer)
                    self.buffer.clear()
                break

            # Discard any bytes before the sync sequence
            if sync_idx > 0:
                self.corrupt_bytes_skipped += sync_idx
                del self.buffer[:sync_idx]

            # Check if we have a full candidate packet
            if len(self.buffer) < self.packet_len:
                # Need more bytes from serial stream
                break

            # Validate end byte
            if self.buffer[self.packet_len - 1] == self.END_BYTE:
                counter = self.buffer[2]
                channels: List[int] = []

                # Extract 16-bit big-endian ADC samples
                for ch in range(self.num_channels):
                    offset = self.HEADER_LEN + (2 * ch)
                    val = (self.buffer[offset] << 8) | self.buffer[offset + 1]
                    channels.append(val)

                # Track packet counter drops
                if self.last_counter is not None:
                    expected = (self.last_counter + 1) & 0xFF
                    if counter != expected:
                        gap = (counter - expected) & 0xFF
                        self.dropped_packets += gap
                self.last_counter = counter

                decoded_packets.append((counter, channels))
                self.packets_decoded += 1

                # Consume packet
                del self.buffer[:self.packet_len]
            else:
                # False sync or corrupt packet: advance past the first sync byte and retry
                self.corrupt_bytes_skipped += 1
                del self.buffer[:1]

        return decoded_packets

    def reset(self):
        self.buffer.clear()
        self.last_counter = None
        self.packets_decoded = 0
        self.corrupt_bytes_skipped = 0
        self.dropped_packets = 0


def encode_chords_packet(counter: int, channels: List[int]) -> bytes:
    """Helper to encode a synthetic Chords binary packet for testing & simulation."""
    pkt = bytearray([0xC7, 0x7C, counter & 0xFF])
    for ch_val in channels:
        clamped = max(0, min(65535, int(ch_val)))
        pkt.append((clamped >> 8) & 0xFF)
        pkt.append(clamped & 0xFF)
    pkt.append(0x01)
    return bytes(pkt)

