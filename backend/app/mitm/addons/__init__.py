"""MITM Proxy addons"""
from app.mitm.addons.interceptor import CursorInterceptor
from app.mitm.addons.rewriter import RequestRewriter
__all__ = ["CursorInterceptor", "RequestRewriter"]
