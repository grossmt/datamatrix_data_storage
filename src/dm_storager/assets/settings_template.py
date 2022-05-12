from dm_storager.structs import (
    Config,
    NetworkSettings,
    ScannerInfo,
    ScannerInternalSettings,
)

TEMPLATE_CONFIG = Config(
    title="Network settings of server and scanners",
    subtitle="Settings template. Fill it correctly.",
    server=NetworkSettings(host="", port=0),
    clients={
        "scanner_0": {
            "info": ScannerInfo(
                name="Default scanner",
                description="Enter optional description or delete it.",
                scanner_id=0,
                address="",
            ),
            "settings": ScannerInternalSettings(
                gateway_ip="",
                netmask="255.255.255.0",
                products=["", "", "", "", "", ""],
                server_ip="",
                server_port=0,
            ),
        }
    },
)
