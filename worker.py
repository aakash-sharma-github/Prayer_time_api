from app.main import app
from workers import asgi

Default = asgi.entrypoint(app)
