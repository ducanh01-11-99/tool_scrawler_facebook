import config
import traceback
import device_config_utils
from account_utils import read_and_convert_account_from_json,\
    write_account_list_to_local_db_file, \
    delete_local_account

def delete_and_update_device_config(data):
    local_device_config = device_config_utils.get_local_device_config()
    for device_config in local_device_config:
        account_user = device_config['account']['username']
        if data['account']['username'] == account_user:
            local_device_config.remove(device_config)
            device_config_utils.write_device_config_list_to_local_file(local_device_config=local_device_config)
            break
def delete_and_update_account(data):
    local_accounts = read_and_convert_account_from_json(file_path=config.account_path)
    delete_local_account(local_account=local_accounts, data=data)
    write_account_list_to_local_db_file(local_account=local_accounts, file_path=config.account_path)
    
def kill_clawer_thread(crawler, crawler_threads):
    try:
        crawler.is_active = False
        crawler.web_browser.driver.quit()
        crawler.join(0)
        crawler.web_browser = None
        crawler_threads.remove(crawler)
    except Exception as ex:
        print("Exception: loi trong khi kill clawer thread", ex)