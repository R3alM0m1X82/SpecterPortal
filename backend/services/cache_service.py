"""
Cache Service - File-based persistent cache
NO external dependencies - uses disk storage
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import hashlib
import json
import pickle
import os


class CacheService:
    """File-based cache with TTL support"""
    
    def __init__(self, cache_dir: str = None):
        # Default cache directory
        if cache_dir is None:
            base_dir = Path(__file__).parent.parent.parent
            cache_dir = base_dir / 'data' / 'cache'
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[✓] File cache initialized: {self.cache_dir}")
    
    def _generate_key(self, token_id: int, endpoint: str, params: dict = None) -> str:
        """Generate cache filename from token ID and endpoint"""
        key_parts = [str(token_id), endpoint]
        if params:
            key_parts.append(json.dumps(params, sort_keys=True))
        
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{cache_key}.cache"
    
    def get(self, token_id: int, endpoint: str, params: dict = None) -> Optional[Any]:
        """Get cached data if not expired"""
        cache_key = self._generate_key(token_id, endpoint, params)
        cache_file = self._get_cache_file(cache_key)
        
        if not cache_file.exists():
            print(f"[CACHE MISS] {endpoint}")
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cached_item = pickle.load(f)
            
            # Check if expired
            if datetime.utcnow() < cached_item['expires_at']:
                print(f"[CACHE HIT] {endpoint}")
                return cached_item['data']
            else:
                # Remove expired file
                cache_file.unlink()
                print(f"[CACHE EXPIRED] {endpoint}")
                return None
                
        except Exception as e:
            # Corrupted cache file, remove it
            print(f"[CACHE ERROR] {endpoint}: {e}")
            try:
                cache_file.unlink()
            except:
                pass
            return None
    
    def set(self, token_id: int, endpoint: str, data: Any, ttl_seconds: int = 300, params: dict = None):
        """Cache data with TTL (default 5 minutes)"""
        cache_key = self._generate_key(token_id, endpoint, params)
        cache_file = self._get_cache_file(cache_key)
        
        cached_item = {
            'data': data,
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl_seconds),
            'cached_at': datetime.utcnow()
        }
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_item, f)
            print(f"[CACHE SET] {endpoint} (TTL: {ttl_seconds}s)")
        except Exception as e:
            print(f"[CACHE SET ERROR] {endpoint}: {e}")
    
    def invalidate(self, token_id: int, endpoint: str = None, params: dict = None):
        """Invalidate cache for token/endpoint"""
        if endpoint:
            cache_key = self._generate_key(token_id, endpoint, params)
            cache_file = self._get_cache_file(cache_key)
            
            if cache_file.exists():
                try:
                    cache_file.unlink()
                    print(f"[CACHE INVALIDATE] {endpoint}")
                except Exception as e:
                    print(f"[CACHE INVALIDATE ERROR] {endpoint}: {e}")
        else:
            # Invalidate all entries for this token (scan directory)
            try:
                for cache_file in self.cache_dir.glob('*.cache'):
                    # Try to load and check token_id (expensive but rare operation)
                    try:
                        with open(cache_file, 'rb') as f:
                            # We don't store token_id in cache, so just delete all
                            # In practice, this is rarely called
                            pass
                    except:
                        pass
                print(f"[CACHE INVALIDATE] Token {token_id} (manual cleanup needed)")
            except Exception as e:
                print(f"[CACHE INVALIDATE ERROR] {e}")
    
    def clear_all(self):
        """Clear entire cache"""
        try:
            deleted = 0
            for cache_file in self.cache_dir.glob('*.cache'):
                try:
                    cache_file.unlink()
                    deleted += 1
                except:
                    pass
            print(f"[CACHE CLEAR] {deleted} entries cleared")
        except Exception as e:
            print(f"[CACHE CLEAR ERROR] {e}")
    
    def cleanup_expired(self):
        """Remove expired cache files"""
        try:
            now = datetime.utcnow()
            deleted = 0
            
            for cache_file in self.cache_dir.glob('*.cache'):
                try:
                    with open(cache_file, 'rb') as f:
                        cached_item = pickle.load(f)
                    
                    if now >= cached_item['expires_at']:
                        cache_file.unlink()
                        deleted += 1
                except:
                    # Corrupted or unreadable, delete it
                    try:
                        cache_file.unlink()
                        deleted += 1
                    except:
                        pass
            
            if deleted > 0:
                print(f"[CACHE CLEANUP] {deleted} expired entries removed")
        except Exception as e:
            print(f"[CACHE CLEANUP ERROR] {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            now = datetime.utcnow()
            total_entries = 0
            active_entries = 0
            expired_entries = 0
            total_size = 0
            
            for cache_file in self.cache_dir.glob('*.cache'):
                try:
                    total_entries += 1
                    total_size += cache_file.stat().st_size
                    
                    with open(cache_file, 'rb') as f:
                        cached_item = pickle.load(f)
                    
                    if now < cached_item['expires_at']:
                        active_entries += 1
                    else:
                        expired_entries += 1
                except:
                    expired_entries += 1
            
            return {
                'backend': 'file',
                'cache_dir': str(self.cache_dir),
                'total_entries': total_entries,
                'active_entries': active_entries,
                'expired_entries': expired_entries,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            return {
                'backend': 'file',
                'error': str(e)
            }


# Global cache instance
graph_cache = CacheService()
