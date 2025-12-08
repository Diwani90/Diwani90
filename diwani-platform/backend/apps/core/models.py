"""
===================================
منصة ديواني - Core Models
النماذج الأساسية للنواة
===================================
"""

# Import AuditLog from audit module for migrations
from apps.core.audit import AuditLog, AuditModelMixin

__all__ = ['AuditLog', 'AuditModelMixin']
