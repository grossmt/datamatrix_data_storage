import logging

from flask import Flask, render_template
from flask import Response

from dm_storager.web.log_parser import flask_logger

APP = Flask(__name__, static_folder="app/static/", template_folder="app/static/")

log = logging.getLogger("werkzeug")
log.setLevel(logging.CRITICAL)


@APP.route("/", methods=["GET"])
def root():
    """index page"""
    return render_template("index.html")


@APP.route("/log_stream", methods=["GET"])
def log_stream():
    """returns logging information"""
    return Response(
        flask_logger(),
        mimetype="text/plain",
        content_type="text/event-stream",
    )


def run_app(host: str = "127.0.0.1", port: int = 80):
    APP.run(host, port, threaded=True, debug=False)
