import os
import traceback

import requests
from threading import Thread


class APIThread(Thread):
    def __init__(self, callback=None, *args, **kwargs):
        super(APIThread, self).__init__(*args, **kwargs)
        self.callback = callback
        self.daemon = True

    def run(self):
        try:
            if self._target:
                response = self._target(*self._args, **self._kwargs)
                self.callback(response)
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs


class ApiClient:
    def __init__(self):
        # print("ApiClient")
        self.base_url = "http://192.168.14.217:8083"#os.environ['REST_HOST']

    def set_base_url(self, base_url):
        self.base_url = base_url

    def get_config_api_callback(self, device_ip_addr=None, callback=None):
        get_config_api_thread = APIThread(target=self.get_config_api, callback=callback, args=device_ip_addr)
        get_config_api_thread.start()

    def get_config_api(self, device_ip_addr=None):
        try:
            query_param = {
                'device_ip_addr': device_ip_addr
            }
            get_vms_camera_api_url = self.base_url + "/api/config/get/"
            response = requests.get(url=get_vms_camera_api_url, params=query_param)
            return response
        except Exception as e:
            print("Exception: get_config_api: ", + str(e))
            response = requests.Response()
            response.status_code = requests.codes.internal_server_error
            response.reason = str(e)
            return response
