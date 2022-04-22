import threading
import socketserver

from typing import List, Tuple

from dm_storager.structs import ClientMessage


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass  # noqa: WPS420


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):  # noqa: WPS110
        while True:
            b_data = self.request.recv(4096)

            cur_thread = threading.current_thread()
            client_ip = self.client_address[0]
            client_port = self.client_address[1]

            _message = ClientMessage(
                client_thread=cur_thread,
                client_ip=client_ip,
                client_port=int(client_port),
                client_message=b_data
            )

            self.server.queue.add(_message)


class ServerQueue:
    def __init__(self, ip, port):
        self.server = ThreadedTCPServer((ip, port), ThreadedTCPRequestHandler)
        self.server.queue = self
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.messages: List[ClientMessage] = []

    @property
    def connection_info(self) -> Tuple[str, int]:
        return self.server.server_address

    def start_server(self):
        self.server_thread.start()

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()

    def add(self, message):
        self.messages.append(message)

    def view(self):
        return self.messages

    def get(self):
        return self.messages.pop()

    def exists(self):
        return len(self.messages)
