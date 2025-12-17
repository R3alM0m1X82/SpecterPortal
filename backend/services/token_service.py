"""
Token Service - WITH JWT IDENTITY EXTRACTION
Extracts UPN (user) or AppID/AppName (service principal) from Access Tokens
"""
import json
import base64
from datetime import datetime
from database import db
from models.token import Token
from models.extraction import ExtractionMetadata


class TokenService:
    
    @staticmethod
    def import_from_json(json_data, filename=None):
        """Import tokens from JSON - supports both TBRes and BrokerDecrypt formats"""
        try:
            if 'tokens' not in json_data or not isinstance(json_data['tokens'], list):
                return {
                    'success': False,
                    'error': 'Invalid JSON format',
                    'message': 'JSON must contain "tokens" array'
                }
            
            tokens_list = json_data['tokens']
            if not tokens_list:
                return {
                    'success': False,
                    'error': 'Empty tokens array',
                    'message': 'No tokens to import'
                }
            
            broker_tokens = []
            tbres_tokens = []
            
            for token in tokens_list:
                if 'type' in token:
                    broker_tokens.append(token)
                else:
                    tbres_tokens.append(token)
            
            if broker_tokens and tbres_tokens:
                return TokenService._import_mixed_format(json_data, broker_tokens, tbres_tokens, filename)
            elif broker_tokens:
                return TokenService._import_broker_format(json_data, filename)
            else:
                return TokenService._import_tbres_format(json_data, filename)
                
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to import tokens: {str(e)}'
            }
    
    @staticmethod
    def _import_broker_format(json_data, filename):
        """Import from BrokerDecrypt JSON format"""
        tokens_data = json_data.get('tokens', [])
        metadata = json_data.get('metadata', {})
        
        target = metadata.get('hostname', metadata.get('target_computer', 'Unknown'))
        
        imported_tokens = []
        skipped_tokens = 0
        expired_tokens = 0
        duplicates = 0
        seen_cache_paths = set()
        
        for token_data in tokens_data:
            try:
                cache_path = token_data.get('cache_path')
                
                if cache_path:
                    if cache_path in seen_cache_paths:
                        duplicates += 1
                        continue
                    
                    existing = Token.query.filter_by(broker_cache_path=cache_path).first()
                    if existing:
                        duplicates += 1
                        continue
                
                token = Token.from_broker_data(token_data)
                token.imported_from = filename or 'BrokerDecrypt'
                
                if token.token_type == 'access_token' and token.is_expired:
                    expired_tokens += 1
                    continue
                
                db.session.add(token)
                imported_tokens.append(token)
                
                if cache_path:
                    seen_cache_paths.add(cache_path)
            except Exception as e:
                print(f"[!] Skip token: {e}")
                skipped_tokens += 1
        
        # Create extraction metadata
        extraction_time = None
        if metadata.get('timestamp'):
            try:
                extraction_time = datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
            except:
                pass
        
        extraction_meta = ExtractionMetadata(
            target=target,
            extraction_time=extraction_time or datetime.utcnow(),
            extraction_method='BrokerDecrypt',
            tokens_count=len(imported_tokens),
            source_file=filename
        )
        db.session.add(extraction_meta)
        
        db.session.commit()
        
        # Count by type
        stats = {}
        for token in imported_tokens:
            stats[token.token_type] = stats.get(token.token_type, 0) + 1
        
        stats_str = ', '.join([f"{count} {ttype}" for ttype, count in stats.items()])
        
        message = f'Imported {len(imported_tokens)} token(s) from {target} ({stats_str})'
        if expired_tokens > 0:
            message += f' - Skipped {expired_tokens} expired token(s)'
        if skipped_tokens > 0:
            message += f' - Skipped {skipped_tokens} invalid token(s)'
        if duplicates > 0:
            message += f' - Skipped {duplicates} duplicate token(s)'
        
        return {
            'success': True,
            'tokens_imported': len(imported_tokens),
            'tokens_skipped': skipped_tokens,
            'tokens_expired': expired_tokens,
            'tokens_duplicates': duplicates,
            'token_stats': stats,
            'extraction_metadata': extraction_meta.to_dict(),
            'message': message
        }
    
    @staticmethod
    def _import_mixed_format(json_data, broker_tokens, tbres_tokens, filename):
        """Import mixed format - both Broker and TBRes tokens"""
        metadata = json_data.get('metadata', {})
        target_broker = metadata.get('hostname', metadata.get('target_computer', 'Unknown'))
        target_tbres = json_data.get('target', 'Unknown')
        target = target_broker if target_broker != 'Unknown' else target_tbres
        
        imported_tokens = []
        skipped_tokens = 0
        expired_tokens = 0
        duplicates = 0
        stats = {}
        seen_cache_paths = set()
        seen_token_values = set()
        
        for token_data in broker_tokens:
            try:
                cache_path = token_data.get('cache_path')
                
                if cache_path:
                    if cache_path in seen_cache_paths:
                        duplicates += 1
                        continue
                    
                    existing = Token.query.filter_by(broker_cache_path=cache_path).first()
                    if existing:
                        duplicates += 1
                        continue
                
                token = Token.from_broker_data(token_data)
                token.imported_from = filename or 'BrokerDecrypt'
                
                if token.token_type == 'access_token' and token.is_expired:
                    expired_tokens += 1
                    continue
                
                db.session.add(token)
                imported_tokens.append(token)
                stats[token.token_type] = stats.get(token.token_type, 0) + 1
                
                if cache_path:
                    seen_cache_paths.add(cache_path)
            except Exception as e:
                print(f"[!] Skip broker token: {e}")
                skipped_tokens += 1
        
        for token_data in tbres_tokens:
            if not token_data.get('access_token'):
                skipped_tokens += 1
                continue
            
            access_token_str = token_data.get('access_token')
            source_file = token_data.get('source_file')
            
            if access_token_str in seen_token_values:
                duplicates += 1
                continue
            
            if source_file:
                existing = Token.query.filter_by(broker_cache_path=source_file).first()
                if existing:
                    duplicates += 1
                    continue
            
            audience = TokenService._extract_audience(access_token_str)
            expires_at = TokenService._extract_expires(access_token_str)
            
            if expires_at and expires_at < datetime.utcnow():
                expired_tokens += 1
                continue
            
            token = Token(
                client_id=token_data.get('client_id', 'unknown'),
                upn=token_data.get('upn'),
                scope=token_data.get('scope'),
                audience=audience,
                access_token=access_token_str,
                refresh_token=token_data.get('refresh_token'),
                expires_at=expires_at,
                imported_from=filename,
                token_type='access_token',
                source='tbres',
                broker_cache_path=source_file
            )
            
            db.session.add(token)
            imported_tokens.append(token)
            stats['access_token'] = stats.get('access_token', 0) + 1
            seen_token_values.add(access_token_str)
        
        extraction_time = None
        if metadata.get('timestamp'):
            try:
                extraction_time = datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
            except:
                pass
        
        extraction_meta = ExtractionMetadata(
            target=target,
            extraction_time=extraction_time or datetime.utcnow(),
            extraction_method='Mixed (BrokerDecrypt + TBRes)',
            tokens_count=len(imported_tokens),
            source_file=filename
        )
        db.session.add(extraction_meta)
        db.session.commit()
        
        stats_str = ', '.join([f"{count} {ttype}" for ttype, count in stats.items()])
        
        message = f'Imported {len(imported_tokens)} token(s) from {target} ({stats_str})'
        if expired_tokens > 0:
            message += f' - Skipped {expired_tokens} expired token(s)'
        if skipped_tokens > 0:
            message += f' - Skipped {skipped_tokens} invalid token(s)'
        if duplicates > 0:
            message += f' - Skipped {duplicates} duplicate token(s)'
        
        return {
            'success': True,
            'tokens_imported': len(imported_tokens),
            'tokens_skipped': skipped_tokens,
            'tokens_expired': expired_tokens,
            'tokens_duplicates': duplicates,
            'token_stats': stats,
            'extraction_metadata': extraction_meta.to_dict(),
            'message': message,
            'format_detected': 'mixed'
        }
    
    @staticmethod
    def _import_tbres_format(json_data, filename):
        """Import from TBRes JSON format (legacy)"""
        tokens = json_data.get('tokens', [])
        target = json_data.get('target', 'Unknown')
        extraction_time_str = json_data.get('extraction_time')
        
        extraction_time = None
        if extraction_time_str:
            try:
                extraction_time = datetime.fromisoformat(extraction_time_str.replace('Z', '+00:00'))
            except:
                pass
        
        imported_tokens = []
        skipped_tokens = 0
        expired_tokens = 0
        duplicates = 0
        seen_token_values = set()
        
        for token_data in tokens:
            if not token_data.get('access_token'):
                skipped_tokens += 1
                continue
            
            access_token_str = token_data.get('access_token')
            source_file = token_data.get('source_file')
            
            if access_token_str in seen_token_values:
                duplicates += 1
                continue
            
            if source_file:
                existing = Token.query.filter_by(broker_cache_path=source_file).first()
                if existing:
                    duplicates += 1
                    continue
            
            audience = TokenService._extract_audience(access_token_str)
            expires_at = TokenService._extract_expires(access_token_str)
            
            if expires_at and expires_at < datetime.utcnow():
                expired_tokens += 1
                continue
            
            token = Token(
                client_id=token_data.get('client_id', 'unknown'),
                upn=token_data.get('upn'),
                scope=token_data.get('scope'),
                audience=audience,
                access_token=access_token_str,
                refresh_token=token_data.get('refresh_token'),
                expires_at=expires_at,
                imported_from=filename,
                token_type='access_token',
                source='tbres',
                broker_cache_path=source_file
            )
            
            db.session.add(token)
            imported_tokens.append(token)
            seen_token_values.add(access_token_str)
        
        metadata = ExtractionMetadata(
            target=target,
            extraction_time=extraction_time,
            extraction_method='PSRemoting',
            tokens_count=len(imported_tokens),
            source_file=filename
        )
        db.session.add(metadata)
        
        db.session.commit()
        
        message = f'Imported {len(imported_tokens)} token(s) from {target}'
        if expired_tokens > 0:
            message += f' - Skipped {expired_tokens} expired token(s)'
        if skipped_tokens > 0:
            message += f' - Skipped {skipped_tokens} invalid token(s)'
        if duplicates > 0:
            message += f' - Skipped {duplicates} duplicate token(s)'
        
        return {
            'success': True,
            'tokens_imported': len(imported_tokens),
            'tokens_skipped': skipped_tokens,
            'tokens_expired': expired_tokens,
            'tokens_duplicates': duplicates,
            'extraction_metadata': metadata.to_dict(),
            'message': message
        }
    
    @staticmethod
    def _extract_audience(access_token):
        """Extract audience (aud) from JWT"""
        if not access_token:
            return None
        
        try:
            parts = access_token.split('.')
            if len(parts) < 2:
                return None
            
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            return payload_data.get('aud', None)
            
        except:
            return None
    
    @staticmethod
    def _extract_expires(access_token):
        """Extract expiration (exp) from JWT"""
        if not access_token:
            return None
        
        try:
            parts = access_token.split('.')
            if len(parts) < 2:
                return None
            
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            exp = payload_data.get('exp')
            
            if exp:
                return datetime.utcfromtimestamp(exp)
            
            return None
            
        except:
            return None
    
    @staticmethod
    def _extract_jwt_claims(access_token):
        """
        Extract identity claims from JWT Access Token
        
        Returns:
        {
            'upn': 'user@domain.com',  # User Principal Name (user tokens)
            'appid': 'guid',           # Application ID (service principal tokens)
            'app_displayname': 'Name', # Application Display Name (SP tokens)
            'tenant_id': 'guid'        # Tenant ID (tid claim)
        }
        """
        if not access_token:
            return {}
        
        try:
            parts = access_token.split('.')
            if len(parts) < 2:
                return {}
            
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)
            
            payload_data = json.loads(base64.urlsafe_b64decode(payload))
            
            claims = {}
            
            # User tokens have 'upn' claim
            if 'upn' in payload_data:
                claims['upn'] = payload_data['upn']
            
            # Service Principal tokens have 'appid' and optionally 'app_displayname'
            if 'appid' in payload_data:
                claims['appid'] = payload_data['appid']
            
            if 'app_displayname' in payload_data:
                claims['app_displayname'] = payload_data['app_displayname']
            
            # Tenant ID (tid claim)
            if 'tid' in payload_data:
                claims['tenant_id'] = payload_data['tid']
            
            return claims
            
        except Exception as e:
            return {}
    
    @staticmethod
    def get_all_tokens():
        """Get all tokens with JWT identity claims"""
        tokens = Token.query.order_by(Token.created_at.desc()).all()
        tokens_list = []
        
        for token in tokens:
            token_dict = token.to_dict()
            
            # Extract JWT claims for access tokens AND Managed Identity tokens
            if token.token_type in ['access_token', 'Managed Identity'] and token.access_token:
                claims = TokenService._extract_jwt_claims(token.access_token)
                token_dict.update(claims)
            
            tokens_list.append(token_dict)
        
        return tokens_list
    
    @staticmethod
    def get_token_by_id(token_id, full=False):
        """Get token by ID with JWT identity claims"""
        token = Token.query.get(token_id)
        if not token:
            return None
        
        token_dict = token.to_dict_full() if full else token.to_dict()
        
        # Extract JWT claims for access tokens AND Managed Identity tokens
        if token.token_type in ['access_token', 'Managed Identity'] and token.access_token:
            claims = TokenService._extract_jwt_claims(token.access_token)
            token_dict.update(claims)
        
        return token_dict
    
    @staticmethod
    def get_active_token():
        """Get active token with JWT identity claims"""
        token = Token.query.filter_by(is_active=True).first()
        if not token:
            return None
        
        token_dict = token.to_dict_full()
        
        # Extract JWT claims for access tokens AND Managed Identity tokens
        if token.token_type in ['access_token', 'Managed Identity'] and token.access_token:
            claims = TokenService._extract_jwt_claims(token.access_token)
            token_dict.update(claims)
        
        return token_dict
    
    @staticmethod
    def activate_token(token_id):
        try:
            Token.query.update({'is_active': False})
            
            token = Token.query.get(token_id)
            if not token:
                return {'success': False, 'error': 'Token not found'}
            
            token.is_active = True
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Token {token_id} activated',
                'token': token.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_token(token_id):
        try:
            token = Token.query.get(token_id)
            if not token:
                return {'success': False, 'error': 'Token not found'}
            
            db.session.delete(token)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Token {token_id} deleted'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def delete_expired_tokens():
        """Delete all expired access tokens"""
        try:
            # Find expired access tokens
            expired_tokens = Token.query.filter(
                Token.token_type == 'access_token',
                Token.expires_at < datetime.utcnow()
            ).all()
            
            deleted_count = len(expired_tokens)
            
            for token in expired_tokens:
                db.session.delete(token)
            
            db.session.commit()
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'message': f'Deleted {deleted_count} expired token(s)'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_stats():
        total_tokens = Token.query.count()
        active_token = Token.query.filter_by(is_active=True).first()
        office_master_count = Token.query.filter_by(
            client_id='d3590ed6-52b3-4102-aeff-aad2292ab01c'
        ).count()
        
        # Stats by type
        at_count = Token.query.filter_by(token_type='access_token').count()
        rt_count = Token.query.filter_by(token_type='refresh_token').count()
        ngc_count = Token.query.filter_by(token_type='ngc_token').count()
        
        # Stats by source
        broker_count = Token.query.filter_by(source='broker').count()
        
        # Count expired access tokens
        expired_count = Token.query.filter(
            Token.token_type == 'access_token',
            Token.expires_at < datetime.utcnow()
        ).count()
        
        return {
            'total_tokens': total_tokens,
            'active_token_id': active_token.id if active_token else None,
            'office_master_tokens': office_master_count,
            'has_active_token': bool(active_token),
            'access_tokens': at_count,
            'refresh_tokens': rt_count,
            'ngc_tokens': ngc_count,
            'broker_tokens': broker_count,
            'expired_tokens': expired_count
        }
