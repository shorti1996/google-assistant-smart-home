import time
from contextlib import contextmanager
from typing import Optional, Callable

import socketio

import config
import custom_logger

logger = custom_logger.logger


@contextmanager
def sio_context(url):
    sio = socketio.Client(logger=False)
    try:
        sio.connect(url)
        block_until(lambda: sio.connected)
        yield sio
    finally:
        sio.disconnect()
        del sio


def on_query(custom_data):
    with sio_context(config.websocket_address) as sio:
        state = blocking_get_lamp_state(sio)
    switch_state = state['softwareSwitchState']['switchState']
    # logger.debug(f"switch_state={switch_state}")
    brightness = min(max(int(state['brightness'] / 255 * 100), 1), 255)
    # print(f"brightness={brightness}")
    return {
        "online": True,
        "on": switch_state,
        "brightness": brightness,
        "currentToggleSettings": {
            "nightmode_toggle": state['nightMode']
        }
    }


def on_action(custom_data, command, params):
    action_timeout_s = 0.1
    with sio_context(config.websocket_address) as sio:
        success_response = {"status": "SUCCESS"}
        if command == "action.devices.commands.OnOff":
            if params['on']:
                sio.call('lamp-switch', {'switchState': True}, timeout=action_timeout_s)
            else:
                sio.call('lamp-switch', {'switchState': False}, timeout=action_timeout_s)
            return success_response
        elif command == "action.devices.commands.BrightnessAbsolute":
            sio.call('brightness', int(params["brightness"] / 100 * 255), timeout=action_timeout_s)
            return success_response
        elif command == "action.devices.commands.ColorAbsolute":
            spectrum = params['color']['spectrumRGB']
            blue = spectrum & 255
            green = (spectrum >> 8) & 255
            red = (spectrum >> 16) & 255
            sio.call('solid-color', {'r': red, 'g': green, 'b': blue}, timeout=action_timeout_s)
            return success_response
        elif command == "action.devices.commands.SetToggles":
            night_mode = params['updateToggleSettings']['nightmode_toggle']
            sio.call('night-mode', night_mode, timeout=action_timeout_s)
            return success_response
        else:
            return {"status": "ERROR"}


def blocking_get_lamp_state(sio: socketio.Client) -> Optional[dict]:
    state: Optional[dict] = None

    @sio.on('lamp-state')
    def lamp_state_received(data):
        nonlocal state
        state = data

    sio.emit('lamp-state', data={})
    block_until(lambda: state is not None)
    return state


def block_until(break_condition: Callable[[], bool], timeout_ms=2000, sleep_interval_ms=50):
    deadline = time.time() + timeout_ms
    while not break_condition() and time.time() < deadline:
        time.sleep(sleep_interval_ms / 1000)
