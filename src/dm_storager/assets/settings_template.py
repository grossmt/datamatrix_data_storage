from dm_storager.py_structs import Config

TEMPLATE_CONFIG = Config(
    title="Сетевые настройки сервера и сканеров",
    subtitle="Шаблон для заполнения настроек.",
    server={"host": "", "port": 0},
    clients={
        "clients.scanner_0": {
            "clients.scanner_0.info": {
                "name": "Default scanner",
                "scanner_id": 0,
                "address": "",
            },
            "clients.scanner_0.settings": {
                "gateway_ip": "",
                "netmask": "",
                "products": ["", "", "", "", "", ""],
                "server_ip": "",
                "server_port": 0,
            },
        }
    },
)