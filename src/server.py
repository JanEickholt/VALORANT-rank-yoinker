import json
import logging
from websocket_server import WebsocketServer

from src.constants import VERSION

logging.getLogger('websocket_server.websocket_server').disabled = True


class Server:
    def __init__(self, log, error):
        self.server = None
        self.Error = error
        self.log = log
        self.lastMessages = {}

    def start_server(self):
        try:
            with open("config.json") as conf:
                port = json.load(conf)["port"]
            self.server = WebsocketServer(host="0.0.0.0", port=port)
            self.server.set_fn_new_client(self.handle_new_client)
            self.server.run_forever(threaded=True)
        except Exception as e:
            self.Error.port_error(port)
            self.log(e)

    def handle_new_client(self):
        self.send_payload("version", {
            "core": VERSION
        })
        for key in self.lastMessages:
            if key not in ["chat", "version"]:
                self.send_message(self.lastMessages[key])

    def send_message(self, message):
        self.server.send_message_to_all(message)

    def send_payload(self, payload_type, payload_content):
        payload_content["type"] = payload_type
        msg_str = json.dumps(payload_content)
        self.lastMessages[payload_type] = msg_str
        self.server.send_message_to_all(msg_str)
