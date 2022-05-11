from dm_storager.py_structs import Config

TEMPLATE_CONFIG = Config(
    title="Network settings of server and scanners",
    subtitle="Settings template. Fill it correctly.",
    server={"host": "", "port": 0},
    clients={
        "scanner_0": {
            "info": {
                "name": "Default scanner",
                "scanner_id": 0,
                "address": "",
            },
            "settings": {
                "gateway_ip": "",
                "netmask": "255.255.255.0",
                "products": ["", "", "", "", "", ""],
                "server_ip": "",
                "server_port": 0,
            },
        }
    },
)
