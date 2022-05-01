import threading
import socketserver
from socket import timeout

from typing import List, Tuple

from dm_storager.structs import ClientMessage, HandshakeMessage


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass  # noqa: WPS420


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.request.settimeout(1.0)
        # self._is_runnin

    def handle(self):  # noqa: WPS110

        is_first_handshake: bool = True

        while self.server._is_running:
            cur_thread = threading.current_thread()
            client_ip = self.client_address[0]
            client_port = self.client_address[1]

            b_data: bytes = b''
            try:
                b_data = self.request.recv(1024)
            except timeout as ex:
                if is_first_handshake:
                    # self.server._logger.info(f"Got connection from {self.client_address[0]}")
                    _message = HandshakeMessage(
                        client_socket=self.request,
                        client_ip=self.client_address[0],
                        client_port=self.client_address[1],
                    )
                    is_first_handshake = False
                    self.server.queue.add(_message)

                continue
            except Exception:
                b_data = b''

            if b_data:
                _message = ClientMessage(
                    client_thread=cur_thread,
                    client_ip=client_ip,
                    client_port=int(client_port),
                    client_message=b_data,
                )
                self.server.queue.add(_message)
            else:
                break

        self.request.close()
        self.server._logger.warning(f"Connection from {self.client_address[0]} closed.")
        
    
class ServerQueue:
    def __init__(self, ip, port, logger):
        self.server = ThreadedTCPServer((ip, port), ThreadedTCPRequestHandler)
        self.server.queue = self
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = False
        self.server.block_on_close = True
        self.messages: List[ClientMessage] = []
        self.server._is_running = True
        self.server._logger = logger

    @property
    def connection_info(self) -> Tuple[str, int]:
        return self.server.server_address

    def start_server(self):
        self.server_thread.start()

    def stop_server(self):
        pass

    def add(self, message):
        self.messages.append(message)

    def view(self):
        return self.messages

    def get(self):
        return self.messages.pop()

    def exists(self):
        return len(self.messages)
