"""Application factory configuring the Cryptiq backend services."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from .storage import init_db
from .routes.auth_routes import auth_routes
from .routes.message_routes import message_routes
from .session_cache import SessionCache
from .socket_registry import SocketRegistry
from .websocket.socket_server import socketio


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_db()

    app.register_blueprint(auth_routes)
    app.register_blueprint(message_routes)

    app.config.setdefault("SESSION_CACHE", SessionCache())
    app.config.setdefault("SOCKET_REGISTRY", SocketRegistry())
    app.config.setdefault("NOW_FN", datetime.utcnow)

    socketio.init_app(app, cors_allowed_origins="*")
    return app


app = create_app()


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5002)
