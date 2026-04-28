"""
Genealogy project - Celery app loader
"""
import os

# Try to load Celery, but don't fail if not installed
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed, skip
    __all__ = ()
