#!/usr/bin/env python3

import evdev
import asyncio
import time
from subprocess import check_output

pwrkey = evdev.InputDevice("/dev/input/event0")
odroidgo2_joypad = evdev.InputDevice("/dev/input/by-path/platform-ff300000.usb-usb-0:1.2:1.0-event-joystick")

need_to_swallow_pwr_key = False # After a resume, we swallow the pwr input that triggered the resume
time_start=0
time_end=0
class Power:
    pwr = 116

class Joypad:
    l1 = 308
    r1 = 309

    f1 = 312

def runcmd(cmd, *args, **kw):
    print(f">>> {cmd}")
    check_output(cmd, *args, **kw)

async def handle_event(device):
    try:
        async for event in device.async_read_loop():
            global need_to_swallow_pwr_key
            global time_start
            global time_end
            if device.name == "rk8xx_pwrkey":
                if event.value == 1 and event.code == Power.pwr: # pwr on release
                    time_start=time.time()
                    time_end=time.time()
                    if need_to_swallow_pwr_key == False:
                        need_to_swallow_pwr_key = True
                        runcmd("/bin/systemctl suspend || true", shell=True)
                    else:
                        need_to_swallow_pwr_key = False
                if event.value == 0 and event.code == Power.pwr:
                    time_end=time.time()
                    if (time_end-time_start) >= 3:
                        runcmd("/bin/systemctl poweroff", shell=True)

            elif device.name.find('OpenSimHardware') != -1:
                keys = odroidgo2_joypad.active_keys()
                print(keys)
                if event.value == 1 and Joypad.f1 in keys:
                    if event.code == Joypad.r1:
                        runcmd("/emuelec/scripts/odroidgoa_utils.sh bright +", shell=True)
                    elif event.code == Joypad.l1:
                        runcmd("/emuelec/scripts/odroidgoa_utils.sh bright -", shell=True)

            if event.code != 0:
                print(device.name, event)
    except OSError as err:
        print(err)
        print("device err!restart loop event")
        loop = asyncio.get_event_loop() 
        loop.stop()
        await asyncio.sleep(8)

def run():
    while True:
        global pwrkey
        global odroidgo2_joypad
        try:
            pwrkey = evdev.InputDevice("/dev/input/event0")
            odroidgo2_joypad = evdev.InputDevice("/dev/input/by-path/platform-ff300000.usb-usb-0:1.2:1.0-event-joystick")

            task1= asyncio.ensure_future(handle_event(pwrkey))
            task2=asyncio.ensure_future(handle_event(odroidgo2_joypad))

            loop = asyncio.get_event_loop()
            loop.run_forever()
            task1.cancel()
            task2.cancel()
        except FileNotFoundError as err:
            print(err) 
            # time.sleep(1)

if __name__ == "__main__": # admire
    run()
