from smbus import SMBus
import time

ADDRESSES = list(range(0x08, 0x19))  # 0x08..0x18
last_pressed = {a: None for a in ADDRESSES}
last_beat    = {a: None for a in ADDRESSES}

def read_status(bus, addr):
    """
    Try SMBus block read: command 0x00 -> [pressedFlag, heartbeat].
    Fallback to single-byte read -> pressedFlag only.
    Returns (pressed, heartbeat) where heartbeat can be None if not available.
    """
    try:
        data = bus.read_i2c_block_data(addr, 0x00, 2)  # sends cmd=0x00, reads 2 bytes
        if len(data) >= 2:
            return (1 if data[0] else 0), data[1]
    except OSError:
        pass

    # Fallback to plain read (old behavior)
    try:
        val = bus.read_byte(addr)
        return (1 if val else 0), None
    except OSError:
        return None, None

bus = SMBus(1)
print("Polling… Ctrl+C to stop.")
try:
    while True:
        for i, addr in enumerate(ADDRESSES, start=1):
            pressed, beat = read_status(bus, addr)
            if pressed is None:
                if last_pressed[addr] is not None:
                    print(f"Button {i} (0x{addr:02X}): disconnected")
                last_pressed[addr] = None
                last_beat[addr] = None
                continue

            # Button state change
            if pressed != last_pressed[addr]:
                print(f"Button {i} (0x{addr:02X}): {'PRESSED' if pressed else 'released'}")
                last_pressed[addr] = pressed

            # Heartbeat change
            if beat is not None and beat != last_beat[addr]:
                print(f"Heartbeat from Button {i} (0x{addr:02X}): {beat}")
                last_beat[addr] = beat

        time.sleep(0.05)  # 50 ms poll; heartbeat ticks every 5 s
finally:
    bus.close()
