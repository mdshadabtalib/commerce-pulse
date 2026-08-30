from __future__ import annotations

from .auth_service import AuthService
from .rbac_service import RBACService
from .audit_service import AuditService
from .notification_service import NotificationService

auth_service = AuthService()
rbac_service = RBACService()
audit_service = AuditService()
notification_service = NotificationService()

__all__ = [
    "AuthService",
    "RBACService",
    "AuditService",
    "NotificationService",
    "auth_service",
    "rbac_service",
    "audit_service",
    "notification_service",
]
