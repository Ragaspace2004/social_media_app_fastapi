# Efficient in-memory rate limiter - no external dependencies
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from fastapi import HTTPException, Request
from collections import defaultdict
import asyncio
import time

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity  # Maximum tokens
        self.tokens = capacity    # Current tokens
        self.refill_rate = refill_rate  # Tokens per second
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens, return True if successful"""
        now = time.time()
        # Add tokens based on time elapsed
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class SimpleRateLimiter:
    def __init__(self):
        # Store token buckets per IP
        self.buckets: Dict[str, TokenBucket] = {}
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # Clean every 5 minutes
    
    def cleanup_old_buckets(self):
        """Prevent memory leaks by removing old buckets"""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            # Remove buckets that haven't been used for 1 hour
            cutoff_time = now - 3600
            self.buckets = {
                ip: bucket for ip, bucket in self.buckets.items()
                if bucket.last_refill > cutoff_time
            }
            self.last_cleanup = now
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request, handling proxies"""
        # Check for forwarded headers (common in production with proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    async def check_rate_limit(
        self, 
        request: Request, 
        max_requests: int = 10, 
        window_seconds: int = 60
    ) -> bool:
        """
        Check if request should be rate limited using token bucket algorithm returns true if request allowed, raises HTTPException if rate limited
        """
        # Cleanup old buckets periodically
        self.cleanup_old_buckets()
        
        client_ip = self.get_client_ip(request)
        
        # Create bucket if doesn't exist
        if client_ip not in self.buckets:
            # Refill rate: max_requests per window_seconds
            refill_rate = max_requests / window_seconds
            self.buckets[client_ip] = TokenBucket(max_requests, refill_rate)
        
        bucket = self.buckets[client_ip]
        
        if not bucket.consume(1):
            # Calculate retry after time
            tokens_needed = 1
            retry_after = int(tokens_needed / bucket.refill_rate)
            
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {max_requests} per {window_seconds} seconds",
                    "retry_after": retry_after
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        return True

rate_limiter = SimpleRateLimiter()

# Dependency functions for FastAPI
async def auth_rate_limit(request: Request):
    """Strict rate limiting for authentication endpoints (5 requests per minute)"""
    return await rate_limiter.check_rate_limit(request, max_requests=5, window_seconds=60)

async def general_rate_limit(request: Request):
    """General rate limiting for most endpoints (30 requests per minute)"""
    return await rate_limiter.check_rate_limit(request, max_requests=30, window_seconds=60)

async def strict_rate_limit(request: Request):
    """Very strict rate limiting for sensitive operations (3 requests per minute)"""
    return await rate_limiter.check_rate_limit(request, max_requests=3, window_seconds=60)

async def api_rate_limit(request: Request):
    """API rate limiting for high-frequency endpoints (100 requests per minute)"""
    return await rate_limiter.check_rate_limit(request, max_requests=100, window_seconds=60)

async def moderate_rate_limit(request: Request):
    """Moderate rate limiting for regular operations (15 requests per minute)"""
    return await rate_limiter.check_rate_limit(request, max_requests=15, window_seconds=60)

# For testing purposes
simple_rate_limiter = rate_limiter
