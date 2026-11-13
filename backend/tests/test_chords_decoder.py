import pytest
from app.serial.chords_decoder import ChordsPacketDecoder, encode_chords_packet


def test_single_valid_packet():
    decoder = ChordsPacketDecoder(num_channels=3)
    pkt = encode_chords_packet(counter=10, channels=[2048, 1024, 512])
    packets = decoder.feed(pkt)

    assert len(packets) == 1
    counter, channels = packets[0]
    assert counter == 10
    assert channels == [2048, 1024, 512]
    assert decoder.packets_decoded == 1
    assert decoder.corrupt_bytes_skipped == 0


def test_partial_packet_arrival():
    decoder = ChordsPacketDecoder(num_channels=3)
    pkt = encode_chords_packet(counter=42, channels=[3000, 2500, 2000])

    # Send first 4 bytes
    p1 = decoder.feed(pkt[:4])
    assert len(p1) == 0

    # Send remaining 6 bytes
    p2 = decoder.feed(pkt[4:])
    assert len(p2) == 1
    assert p2[0][0] == 42
    assert p2[0][1] == [3000, 2500, 2000]


def test_multiple_packets_in_single_chunk():
    decoder = ChordsPacketDecoder(num_channels=3)
    pkt1 = encode_chords_packet(1, [100, 200, 300])
    pkt2 = encode_chords_packet(2, [400, 500, 600])
    pkt3 = encode_chords_packet(3, [700, 800, 900])

    packets = decoder.feed(pkt1 + pkt2 + pkt3)
    assert len(packets) == 3
    assert [p[0] for p in packets] == [1, 2, 3]
    assert packets[0][1] == [100, 200, 300]
    assert packets[1][1] == [400, 500, 600]
    assert packets[2][1] == [700, 800, 900]


def test_corrupted_leading_bytes_recovery():
    decoder = ChordsPacketDecoder(num_channels=3)
    garbage = b"\x00\xff\x12\x34\xc7\x05"  # Noise with false sync byte 1
    valid_pkt = encode_chords_packet(15, [2048, 2050, 2045])

    packets = decoder.feed(garbage + valid_pkt)
    assert len(packets) == 1
    assert packets[0][0] == 15
    assert packets[0][1] == [2048, 2050, 2045]
    assert decoder.corrupt_bytes_skipped > 0


def test_packet_drop_tracking():
    decoder = ChordsPacketDecoder(num_channels=3)
    pkt1 = encode_chords_packet(1, [2000, 2000, 2000])
    pkt3 = encode_chords_packet(3, [2000, 2000, 2000])  # Skipped counter 2

    decoder.feed(pkt1)
    decoder.feed(pkt3)
    assert decoder.dropped_packets == 1

