# Export endpoint modules for router to import
from . import account
from . import health
from . import service_status

__all__ = ["account", "health", "service_status"]
