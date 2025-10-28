"""
Performance Monitoring Middleware
API response time ve diğer metrikleri takip eder
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import psutil
import os


class PerformanceMonitorMiddleware(BaseHTTPMiddleware):
    """Performance monitoring middleware"""
    
    async def dispatch(self, request: Request, call_next):
        # Start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        duration_ms = round(duration * 1000, 2)
        
        # Add headers
        response.headers["X-Response-Time"] = f"{duration_ms}ms"
        response.headers["X-Process-Memory"] = f"{self.get_memory_usage()}MB"
        
        # Log slow requests (>1000ms)
        if duration_ms > 1000:
            print(f"⚠️ SLOW REQUEST: {request.method} {request.url.path} - {duration_ms}ms")
        
        # Log to console (development)
        if os.getenv("DEBUG", "false").lower() == "true":
            print(f"{request.method} {request.url.path} - {duration_ms}ms")
        
        return response
    
    @staticmethod
    def get_memory_usage() -> float:
        """Get current process memory usage (MB)"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return round(memory_info.rss / 1024 / 1024, 2)
    
    @staticmethod
    def get_system_stats() -> dict:
        """Get system statistics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "process_memory_mb": PerformanceMonitorMiddleware.get_memory_usage()
        }

