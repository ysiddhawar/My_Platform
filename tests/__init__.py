import atexit

from api.server.api_registry import api_registry


atexit.register(api_registry.close)
