import device_config_utils
from crawler_manage import CrawlerManager

if __name__ == '__main__':
    local_device_config = device_config_utils.get_local_device_config()
    crawler_manage = CrawlerManager(local_device_config)