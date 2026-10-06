"""Compatibility entry point; both launch paths use the shared authenticated API."""

from .app import app, create_app

__all__ = ["app", "create_app"]
