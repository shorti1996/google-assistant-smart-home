import logging
import subprocess

import config
import socketio
import time

logger = logging.getLogger()


def device_01_query(custom_data):
    sio = connect_to_socketio()
    state = None

    @sio.on('lamp-state')
    def lamp_state_received(data):
        nonlocal state
        state = data['softwareSwitchState']['switchState']

    timeout_ms = 2000
    deadline = time.time() + timeout_ms
    sio.emit('lamp-state', data={})
    while state is None and time.time() < deadline:
        time.sleep(0.1)
    return {"on": state, "online": True}


def device_01_action(custom_data, command, params):
    sio = connect_to_socketio()

    if command == "action.devices.commands.OnOff":
        if params['on']:
            sio.emit('lamp-switch', {'switchState': True})
            # subprocess.run(["wakeonlan", "-i", "192.168.0.255", "00:11:22:33:44:55"])
        else:
            sio.emit('lamp-switch', {'switchState': False})
            # subprocess.run(["sh", "-c", "echo shutdown -h | ssh clust@192.168.0.2"])
        return {"status": "SUCCESS", "states": {"on": params['on'], "online": True}}
    else:
        return {"status": "ERROR"}


def connect_to_socketio():
    sio = socketio.Client()
    sio.connect(config.websocket_address)
    return sio
