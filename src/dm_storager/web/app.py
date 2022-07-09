import logging

from flask import Flask, render_template
from flask import Response

from dm_storager.__config__ import __version__
from dm_storager.web.log_parser import flask_logger

APP = Flask(__name__, static_folder="static/", template_folder="templates/")

log = logging.getLogger("werkzeug")
log.setLevel(logging.CRITICAL)


def get_version():
    return __version__


@APP.route("/", methods=["GET"])
def root():
    """index page"""
    return render_template("index.html")


@APP.route("/logs", methods=["GET"])
def logs():
    return render_template(
        "index.html", DOC_BODY=render_template("log.html"), version=get_version()
    )


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
