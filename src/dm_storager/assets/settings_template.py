from dm_storager.structs import (
    Config,
    NetworkSettings,
    ScannerInfo,
    ScannerInternalSettings,
)

TEMPLATE_CONFIG = Config(
    title="Network settings of server and scanners",
    subtitle="Settings template. Fill it correctly.",
    debug_flag="y",
    server=NetworkSettings(host="", port=0),
    scanners={
        "0": {
            "info": ScannerInfo(
                name="Scanner #0",
                description="Example scanner with dec integer ID",
                address="",
            ),
            "settings": ScannerInternalSettings(
                gateway_ip="",
                netmask="255.255.255.0",
                products=[
                    "Product 1",
                    "Product 2",
                    "",
                    "",
                    "",
                    "",
                ],
                server_ip="",
                server_port=0,
            ),
        },
        "0x0001": {
            "info": ScannerInfo(
                name="Scanner #0x0001",
                description="Example scanner with hex integer ID",
                address="",
            ),
            "settings": ScannerInternalSettings(
                gateway_ip="",
                netmask="255.255.255.0",
                products=["", "", "", "", "", ""],
                server_ip="",
                server_port=0,
            ),
        },
    },
)
