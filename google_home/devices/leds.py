import logging
import time

import socketio

import config

logger = logging.getLogger()


def on_query(custom_data):
    sio = connect_to_socketio()
    state = blocking_get_lamp_state(sio)
    return {
        "online": True,
        "on": state['softwareSwitchState']['switchState'],
        "brightness": state['brightness']
    }


def on_action(custom_data, command, params):
    sio = connect_to_socketio()

    success_response = {"status": "SUCCESS"}
    if command == "action.devices.commands.OnOff":
        if params['on']:
            sio.emit('lamp-switch', {'switchState': True})
        else:
            sio.emit('lamp-switch', {'switchState': False})
        return success_response
    elif command == "action.devices.commands.BrightnessAbsolute":
        sio.emit('brightness', int(params["brightness"] / 100 * 255))
        return success_response
    elif command == "action.devices.commands.ColorAbsolute":
        spectrum = params['color']['spectrumRGB']
        blue = spectrum & 255
        green = (spectrum >> 8) & 255
        red = (spectrum >> 16) & 255
        sio.emit('solid-color', {'r': red, 'g': green, 'b': blue})
        return success_response
    else:
        return {"status": "ERROR"}


def connect_to_socketio():
    sio = socketio.Client()
    sio.connect(config.websocket_address)
    return sio


def blocking_get_lamp_state(sio):
    state = None

    @sio.on('lamp-state')
    def lamp_state_received(data):
        nonlocal state
        state = data

    sio.emit('lamp-state', data={})
    timeout_ms = 2000
    deadline = time.time() + timeout_ms
    while state is None and time.time() < deadline:
        time.sleep(0.1)
    return state
