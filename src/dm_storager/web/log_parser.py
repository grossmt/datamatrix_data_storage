from dm_storager.utils.path import default_log_file

RED = '<div style="color:red">'
BLACK = '<div style="color:black">'
GREEN = '<div style="color:green">'
YELLOW = '<div style="color:yellow">'
END = "</div>"


def flask_logger():
    """creates logging information"""

    with open(default_log_file()) as log_info:
        data = log_info.readlines()

    for i in range(len(data)):

        if data[i].find("DEBUG    ") > 0:
            data[i] = BLACK + data[i][:-1] + END
        if data[i].find("INFO    ") > 0:
            data[i] = GREEN + data[i][:-1] + END
        if data[i].find("ERROR    ") > 0:
            data[i] = RED + data[i][:-1] + END
        if data[i].find("WARNING    ") > 0:
            data[i] = YELLOW + data[i][:-1] + END

    _data = "".join(data)
    yield _data.encode()
    # yield _data
