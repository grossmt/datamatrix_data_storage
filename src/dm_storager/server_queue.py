import threading
import socketserver
from socket import timeout

from typing import List, Tuple

from dm_storager.structs import ClientMessage, HandshakeMessage


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass  # noqa: WPS420, WPS604


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def setup(self):
        self.request.settimeout(1.0)

    def handle(self):  # noqa: WPS110, WPS231

        is_first_handshake: bool = True
        cur_thread = threading.current_thread()
        setattr(cur_thread, "enabled_socket", True)

        while getattr(cur_thread, "enabled_socket", True) and self.server.is_running:  # type: ignore

            client_ip = self.client_address[0]
            client_port = self.client_address[1]

            b_data: bytes = b""
            try:
                b_data = self.request.recv(2048 * 2)
            except timeout:
                if is_first_handshake:
                    is_first_handshake = False
                    self.server.queue.add(  # type: ignore
                        HandshakeMessage(
                            client_socket=self.request,
                            client_ip=self.client_address[0],
                            client_port=self.client_address[1],
                            client_socket_thread=cur_thread,
                        )
                    )
                continue
            except Exception:
                b_data = b""

            if b_data:
                self.server.queue.add(  # type: ignore
                    ClientMessage(
                        client_ip=client_ip,
                        client_port=int(client_port),
                        client_message=b_data,
                        client_socket_thread=cur_thread,
                    )
                )
            else:
                break

        setattr(cur_thread, "enabled_socket", False)
        self.request.close()
        self.server.logger.warning(  # type: ignore
            f"Connection from {self.client_address[0]} closed."
        )


class ServerQueue:
    def __init__(self, ip, port, logger):
        self.server = ThreadedTCPServer((ip, port), ThreadedTCPRequestHandler)
        self.server.queue = self  # type: ignore
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server.block_on_close = True
        self.messages: List[ClientMessage] = []
        self.server.is_running = True  # type: ignore
        self.server.logger = logger  # type: ignore

    @property
    def connection_info(self) -> Tuple[str, int]:
        return self.server.server_address

    def start_server(self):
        self.server_thread.start()

    def stop_server(self):
        self.server_thread.join()
        pass  # noqa: WPS420

    def add(self, message):
        self.messages.append(message)

    def view(self):
        return self.messages

    def get(self):
        return self.messages.pop()

    def exists(self):
        return len(self.messages)
