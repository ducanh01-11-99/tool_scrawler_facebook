import json
import time
import websocket
from threading import Thread
from wsclient.event_type import EventType


class WebsocketClientSingleton(type):
    """
    Define an Instance operation that lets clients access its unique
    instance.
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        # print("WebsocketClientSingleton __init________________________")
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        # print("WebsocketClientSingleton __call________________________")
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class WebsocketClient(metaclass=WebsocketClientSingleton):
    def __init__(self, url=None, event_callback=None):
        self.ws = None
        self.url = url
        self.event_callback = event_callback

    def connect_background(self):
        Thread(target=self.connect).start()

    def connect(self):
        self.ws = websocket.WebSocketApp(self.url,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.run_forever()

    def send(self, data):
        self.ws.send(data)

    def close(self):
        self.ws.close()

    def on_open(self, ws):
        data = {"message": "You are connected"}
        event = EventType.connection_established
        message_json = {'event': event, 'data': data}
        self.event_callback(message_json)

    def on_message(self, ws, message):
        message_json = json.loads(message)
        event = message_json['event']
        data = message_json['data']
        message_json = {'event': event, 'data': data}
        self.event_callback(message_json)

    def on_error(self, ws, error):
        data = {"message": "WebSocket error", "error": error}
        event = EventType.connection_error
        message_json = {'event': event, 'data': data}
        self.event_callback(message_json)

    def on_close(self, ws, close_status_code, close_msg):
        data = {"message": f"close_status_code = {close_status_code} close_msg = {close_msg}"}
        event = EventType.connection_lost
        message_json = {'event': event, 'data': data}
        self.event_callback(message_json)

        print("Trying reconnect")
        time.sleep(10)
        self.ws.run_forever()
