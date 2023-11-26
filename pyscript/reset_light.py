from send_tuya_device_commands import send_commands

def get_commands(scene):
    return 

@service
def reset_light(device=None):
    log.info(f'Resetting light {device}')

    send_commands(state.get(device).deviceId, {'commands':[{'code': 'scene_data', 'value': '020e0d0000000000000003e803e8'},{'code': 'work_mode', 'value': 'scene'}]});
