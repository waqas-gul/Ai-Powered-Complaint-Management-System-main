from .complaints import complaints_bp
from .departments import departments_bp
from .dashboard import dashboard_bp
from .auth import auth_bp

__all__ = ['complaints_bp', 'departments_bp', 'dashboard_bp', 'auth_bp']