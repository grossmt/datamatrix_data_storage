from dm_storager.structs import (
    Config,
    NetworkSettings,
    ScannerInfo,
    ScannerInternalSettings,
    FileFormat,
)

TEMPLATE_CONFIG = Config(
    title="Network settings of server and scanners",
    subtitle="Settings template. Fill it correctly.",
    debug_flag="y",
    server=NetworkSettings(host="", port=0),
    scanners={
        "1": {
            "info": ScannerInfo(
                name="Example Scanner #1",
                description="Example scanner with dec integer ID",
                address="",
                update_settings_on_connect="yes",
                # data_format=FileFormat.CSV,
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
    },
)
