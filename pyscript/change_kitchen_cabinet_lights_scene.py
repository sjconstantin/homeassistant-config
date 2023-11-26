from send_tuya_device_commands import send_commands

SCENES = {
    "read": "010e0d0000000000000003e801f4",
    "night": "000e0d0000000000000000c80000",
    "working": "020e0d0000000000000003e803e8",
    "leisure": "030e0d0000000000000001f401f4",
    "soft": "04464602007803e803e800000000464602007803e8000a00000000",
    "colorful": "05464601000003e803e800000000464601007803e803e80000000046460100f003e803e800000000464601003d03e803e80000000046460100ae03e803e800000000464601011303e803e800000000",
    "dazzling": "06464601000003e803e800000000464601007803e803e80000000046460100f003e803e800000000",
    "gorgeous": "07464602000003e803e800000000464602007803e803e80000000046460200f003e803e800000000464602003d03e803e80000000046460200ae03e803e800000000464602011303e803e800000000"
}

def get_commands(scene):
    return {'commands':[{'code': 'switch_led', 'value': True},{'code': 'scene_data', 'value': SCENES[scene]},{'code': 'work_mode', 'value': 'scene'}]}

@service
def change_kitchen_cabinet_lights_scene(scene=None):
    log.info(f'Changing kitchen cabinet lights scene to {scene}')

    send_commands(light.fixturesmart_v3_0.deviceId, get_commands(scene));
    send_commands(light.under_cabinet_light.deviceId, get_commands(scene));
    send_commands(light.under_cabinet_light_2.deviceId, get_commands(scene));
