import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
import logging

class DatabaseManager:
    """Advanced database manager for Asyafira Airdrop Bot"""
    
    def __init__(self, db_path: str = "config/asyafira_bot.db", encryption_key: str = None):
        self.db_path = db_path
        self.encryption_key = encryption_key
        self.cipher = None
        
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Claims table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_data TEXT,
                    error_message TEXT,
                    execution_time REAL,
                    user_agent TEXT,
                    ip_address TEXT
                )
            """)
            
            # Twitter actions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS twitter_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action_type TEXT NOT NULL,
                    target_id TEXT,
                    target_username TEXT,
                    content TEXT,
                    status TEXT NOT NULL,
                    response_data TEXT,
                    error_message TEXT
                )
            """)
            
            # Cookies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cookies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    domain TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    expires DATETIME,
                    path TEXT,
                    secure BOOLEAN,
                    http_only BOOLEAN,
                    same_site TEXT,
                    is_encrypted BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    end_time DATETIME,
                    total_claims INTEGER DEFAULT 0,
                    successful_claims INTEGER DEFAULT 0,
                    failed_claims INTEGER DEFAULT 0,
                    twitter_actions INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'active',
                    metadata TEXT
                )
            """)
            
            # Configuration table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT,
                    description TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    module TEXT,
                    message TEXT NOT NULL,
                    extra_data TEXT
                )
            """)
            
            # Analytics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    category TEXT,
                    metadata TEXT,
                    UNIQUE(date, metric_name)
                )
            """)
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    def _encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if self.cipher and data:
            return self.cipher.encrypt(data.encode()).decode()
        return data
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if self.cipher and encrypted_data:
            try:
                return self.cipher.decrypt(encrypted_data.encode()).decode()
            except Exception as e:
                self.logger.error(f"Decryption failed: {e}")
                return encrypted_data
        return encrypted_data
    
    def log_claim(self, url: str, status: str, response_data: Dict = None, 
                  error_message: str = None, execution_time: float = None,
                  user_agent: str = None, ip_address: str = None) -> int:
        """Log claim attempt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO claims (url, status, response_data, error_message, 
                                  execution_time, user_agent, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                url, status, 
                json.dumps(response_data) if response_data else None,
                error_message, execution_time, user_agent, ip_address
            ))
            conn.commit()
            return cursor.lastrowid
    
    def log_twitter_action(self, action_type: str, target_id: str = None,
                          target_username: str = None, content: str = None,
                          status: str = "success", response_data: Dict = None,
                          error_message: str = None) -> int:
        """Log Twitter action"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO twitter_actions (action_type, target_id, target_username,
                                           content, status, response_data, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                action_type, target_id, target_username, content, status,
                json.dumps(response_data) if response_data else None,
                error_message
            ))
            conn.commit()
            return cursor.lastrowid
    
    def save_cookies(self, cookies: List[Dict], encrypt: bool = True) -> None:
        """Save cookies to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing cookies
            cursor.execute("DELETE FROM cookies")
            
            for cookie in cookies:
                value = cookie.get('value', '')
                if encrypt and self.cipher:
                    value = self._encrypt_data(value)
                
                cursor.execute("""
                    INSERT INTO cookies (domain, name, value, expires, path,
                                       secure, http_only, same_site, is_encrypted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cookie.get('domain', ''),
                    cookie.get('name', ''),
                    value,
                    cookie.get('expires'),
                    cookie.get('path', '/'),
                    cookie.get('secure', False),
                    cookie.get('httpOnly', False),
                    cookie.get('sameSite', 'Lax'),
                    encrypt
                ))
            
            conn.commit()
            self.logger.info(f"Saved {len(cookies)} cookies to database")
    
    def get_cookies(self, domain: str = None) -> List[Dict]:
        """Retrieve cookies from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if domain:
                cursor.execute("""
                    SELECT domain, name, value, expires, path, secure, 
                           http_only, same_site, is_encrypted
                    FROM cookies WHERE domain LIKE ?
                """, (f"%{domain}%",))
            else:
                cursor.execute("""
                    SELECT domain, name, value, expires, path, secure,
                           http_only, same_site, is_encrypted
                    FROM cookies
                """)
            
            cookies = []
            for row in cursor.fetchall():
                value = row[2]
                if row[8]:  # is_encrypted
                    value = self._decrypt_data(value)
                
                cookies.append({
                    'domain': row[0],
                    'name': row[1],
                    'value': value,
                    'expires': row[3],
                    'path': row[4],
                    'secure': row[5],
                    'httpOnly': row[6],
                    'sameSite': row[7]
                })
            
            return cookies
    
    def create_session(self, session_id: str, metadata: Dict = None) -> int:
        """Create new session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, metadata)
                VALUES (?, ?)
            """, (session_id, json.dumps(metadata) if metadata else None))
            conn.commit()
            return cursor.lastrowid
    
    def update_session_stats(self, session_id: str, **kwargs) -> None:
        """Update session statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            updates = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['total_claims', 'successful_claims', 'failed_claims', 
                          'twitter_actions', 'status']:
                    updates.append(f"{key} = ?")
                    values.append(value)
            
            if updates:
                values.append(session_id)
                cursor.execute(f"""
                    UPDATE sessions SET {', '.join(updates)}
                    WHERE session_id = ?
                """, values)
                conn.commit()
    
    def get_analytics(self, days: int = 30) -> Dict:
        """Get analytics data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Claims statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_claims,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_claims,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_claims,
                    AVG(execution_time) as avg_execution_time
                FROM claims 
                WHERE timestamp >= datetime('now', '-{} days')
            """.format(days))
            
            claims_stats = cursor.fetchone()
            
            # Twitter statistics
            cursor.execute("""
                SELECT 
                    action_type,
                    COUNT(*) as count,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
                FROM twitter_actions 
                WHERE timestamp >= datetime('now', '-{} days')
                GROUP BY action_type
            """.format(days))
            
            twitter_stats = cursor.fetchall()
            
            return {
                'claims': {
                    'total': claims_stats[0] or 0,
                    'successful': claims_stats[1] or 0,
                    'failed': claims_stats[2] or 0,
                    'success_rate': (claims_stats[1] / claims_stats[0] * 100) if claims_stats[0] else 0,
                    'avg_execution_time': claims_stats[3] or 0
                },
                'twitter': {
                    action[0]: {
                        'total': action[1],
                        'successful': action[2],
                        'success_rate': (action[2] / action[1] * 100) if action[1] else 0
                    } for action in twitter_stats
                }
            }
    
    def cleanup_old_data(self, days: int = 90) -> None:
        """Clean up old data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            tables = ['claims', 'twitter_actions', 'logs']
            
            for table in tables:
                cursor.execute(f"""
                    DELETE FROM {table} 
                    WHERE timestamp < datetime('now', '-{days} days')
                """)
            
            conn.commit()
            self.logger.info(f"Cleaned up data older than {days} days")
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Database backup failed: {e}")
            return False
    
    def get_recent_logs(self, limit: int = 100, level: str = None) -> List[Dict]:
        """Get recent logs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = "SELECT timestamp, level, module, message, extra_data FROM logs"
            params = []
            
            if level:
                query += " WHERE level = ?"
                params.append(level)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            return [{
                'timestamp': row[0],
                'level': row[1],
                'module': row[2],
                'message': row[3],
                'extra_data': json.loads(row[4]) if row[4] else None
            } for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        pass  # SQLite connections are closed automatically

# Database instance
db = None

def init_database(db_path: str = "config/asyafira_bot.db", encryption_key: str = None):
    """Initialize global database instance"""
    global db
    db = DatabaseManager(db_path, encryption_key)
    return db

def get_database() -> DatabaseManager:
    """Get global database instance"""
    global db
    if db is None:
        db = DatabaseManager()
    return db