from smbus import SMBus
import time

ADDRESSES = list(range(0x08, 0x19))
last = {a: None for a in ADDRESSES}

bus = SMBus(1)
print("Polling… Ctrl+C to stop.")
try:
    while True:
        for i, addr in enumerate(ADDRESSES, start=1):
            try:
                val = bus.read_byte(addr)
            except OSError:
                val = None
            if val != last[addr]:
                if val is None:
                    print(f"Button {i} (0x{addr:02X}): disconnected")
                else:
                    print(f"Button {i} (0x{addr:02X}): {'PRESSED' if val else 'released'}")
                last[addr] = val
        time.sleep(0.02)
finally:
    bus.close()
