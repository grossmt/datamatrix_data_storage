# import asyncio
# import datetime
# import time


# class TestClass:
#     def __init__(self) -> None:
#         self._is_alive = True
#         self._received_ping = False
#         self._loop = None

#     async def coruitine_one(self):
#         while self._is_alive:
#             print("cor 1")
#             # if int(datetime.datetime.now().timestamp()) % 30 == 0:
#             #     self._received_ping = True
#             #     print("received ping is true")

#             await asyncio.sleep(0.5)

#     async def coruitine_control(self):

#         while self._is_alive:
#             print("cor control")

#             try:
#                 # future = asyncio.wait_for(self.event_handler(), timeout=2)
#                 future = asyncio.wait_for(self.event_handler(), timeout=2)
#                 self._loop.add_signal_handler(future)
#                 await asyncio.sleep(0.5)
#             except asyncio.exceptions.TimeoutError:
#                 print("State control packet timeout!")
#                 self._is_alive = False
#                 return

#             # print("STATE CONTROL PACKET ACCEPTED")
#             self._received_ping = False

#     async def event_handler(self):
#         while self._received_ping is False:
#             await asyncio.sleep(0.5)
#             # time.sleep(0.1)
#         # return pp

#     def run(self):
#         self._loop = asyncio.get_event_loop()
#         self._loop.run_until_complete(
#             asyncio.gather(self.coruitine_control(), self.coruitine_one())
#         )
#         self._loop.close()
#         # while self._is_alive:
#         #     # asyncio.run(self.coruitine_control())
#         #     # asyncio.run(self.coruitine_one())

#         #     # await self.coruitine_control()
#         #     # await self.coruitine_one()
#         #     # await asyncio.sleep(1)

#         # loop.close()


# # async def main():

# t = TestClass()
# t.run()


# # asyncio.run(main())


from dm_storager.utils.path import default_log_file

RED = '<span style="color: brown">'
BLACK = '<span style="color: black">'
GREEN = '<span style="color: green">'
BROWN = '<span style="color: brown">'
END = "</span>"


def flask_logger():
    """creates logging information"""
    # with open(default_log_file()) as log_info:
    #     data = log_info.read()
    #     yield data.encode()

    with open(default_log_file()) as log_info:
        data = log_info.readlines()
        # for i, next_string in (iter(data), data):
        for i in range(len(data)):

            if data[i].find("DEBUG    ") > 0:
                data[i] = BLACK + data[i] + END
            if data[i].find("INFO    ") > 0:
                data[i] = GREEN + data[i] + END
            if data[i].find("ERROR    ") > 0:
                data[i] = RED + data[i] + END
            if data[i].find("WARNING    ") > 0:
                data[i] = BROWN + data[i] + END

        _data = "".join(data)
        yield _data.encode()
        # return _data


flask_logger()
