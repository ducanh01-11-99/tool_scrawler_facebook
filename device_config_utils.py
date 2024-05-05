import json
import config

def get_local_device_config():
    device_config = list()

    with open(config.device_config_path, 'r') as f:
        try:
            device_config = json.load(f)
        except Exception as ex:
            print("Exception: File device config chua co du lieu!")
    print('device_config', device_config)
    return device_config

def write_device_config_list_to_local_file(local_device_config):
    with open(config.device_config_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(local_device_config, indent=2))