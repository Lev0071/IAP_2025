from smbus import SMBus
import time

ADDRESSES = list(range(0x08, 0x19))  # Scan 0x08..0x18
last = {a: None for a in ADDRESSES}

bus = SMBus(1)
print("Polling heartbeats… Ctrl+C to stop.")
try:
    while True:
        for addr in ADDRESSES:
            try:
                hb = bus.read_byte(addr)   # read 1-byte heartbeat
            except OSError:
                if last[addr] is not None:
                    print(f"0x{addr:02X}: disconnected")
                last[addr] = None
                continue

            if hb != last[addr]:
                print(f"0x{addr:02X}: heartbeat {hb}")
                last[addr] = hb

        time.sleep(0.2)  # poll rate (5 Hz)
finally:
    bus.close()
