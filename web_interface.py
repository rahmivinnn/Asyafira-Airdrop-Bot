#!/usr/bin/env python3
"""
Asyafira Airdrop Bot - Web Interface
Flask-based web dashboard for bot management and monitoring
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
import logging
import threading

# Flask imports
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Local imports
from config.database import get_database
from utils.cookie_manager import CookieManager
from utils.twitter_client import TwitterClient
from utils.claimer import AirdropClaimer
from main import AsyafiraBot

class WebInterface:
    """Web interface for Asyafira Bot"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize Flask app
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        
        self.app.secret_key = config.get('WEB_INTERFACE_SECRET_KEY', 'asyafira-bot-secret-key-2024')
        
        # Initialize SocketIO
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Initialize bot components
        self.bot = AsyafiraBot()
        self.db = get_database()
        
        # Web interface settings
        self.host = config.get('WEB_INTERFACE_HOST', '127.0.0.1')
        self.port = int(config.get('WEB_INTERFACE_PORT', 8080))
        self.debug = config.get('DEBUG', False)
        
        # Authentication
        self.admin_username = config.get('WEB_ADMIN_USERNAME', 'admin')
        self.admin_password_hash = generate_password_hash(
            config.get('WEB_ADMIN_PASSWORD', 'asyafira2024')
        )
        
        # Real-time data
        self.connected_clients = set()
        self.real_time_stats = {
            'active_claims': 0,
            'last_claim_time': None,
            'current_status': 'idle'
        }
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio_events()
        
        # Background thread for real-time updates
        self.update_thread = None
        self.running = False
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            if not self._is_authenticated():
                return redirect(url_for('login'))
            return render_template('dashboard.html')
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'POST':
                username = request.form.get('username')
                password = request.form.get('password')
                
                if (username == self.admin_username and 
                    check_password_hash(self.admin_password_hash, password)):
                    session['authenticated'] = True
                    session['username'] = username
                    flash('Login successful!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Invalid credentials!', 'error')
            
            return render_template('login.html')
        
        @self.app.route('/logout')
        def logout():
            session.clear()
            flash('Logged out successfully!', 'info')
            return redirect(url_for('login'))
        
        @self.app.route('/api/status')
        def api_status():
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            try:
                # Get statistics from all components
                claimer_stats = self.bot.claimer.get_statistics()
                twitter_stats = self.bot.twitter_client.get_statistics()
                db_stats = self.db.get_statistics()
                
                status = {
                    'bot': {
                        'running': self.bot.is_running,
                        'uptime': str(datetime.now() - self.bot.stats['start_time']),
                        'version': self.bot.version
                    },
                    'claimer': claimer_stats,
                    'twitter': twitter_stats,
                    'database': db_stats,
                    'real_time': self.real_time_stats,
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify(status)
            
            except Exception as e:
                self.logger.error(f"API status error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/claims', methods=['GET', 'POST'])
        def api_claims():
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            if request.method == 'POST':
                try:
                    data = request.get_json()
                    url = data.get('url')
                    method = data.get('method', 'requests')
                    
                    if not url:
                        return jsonify({'error': 'URL is required'}), 400
                    
                    # Start claim in background
                    def claim_task():
                        self.real_time_stats['active_claims'] += 1
                        self.real_time_stats['current_status'] = 'claiming'
                        
                        try:
                            if method == 'requests':
                                result = self.bot.claimer.claim_with_requests(url)
                            else:
                                result = self.bot.claimer.claim_with_selenium(url)
                            
                            self.real_time_stats['last_claim_time'] = datetime.now().isoformat()
                            
                            # Emit real-time update
                            self.socketio.emit('claim_result', result)
                            
                        except Exception as e:
                            self.logger.error(f"Claim task error: {e}")
                        finally:
                            self.real_time_stats['active_claims'] -= 1
                            if self.real_time_stats['active_claims'] == 0:
                                self.real_time_stats['current_status'] = 'idle'
                    
                    thread = threading.Thread(target=claim_task)
                    thread.start()
                    
                    return jsonify({'message': 'Claim started', 'url': url})
                
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            else:
                # GET: Return recent claims
                try:
                    claims = self.db.get_recent_claims(limit=50)
                    return jsonify(claims)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/twitter', methods=['GET', 'POST'])
        def api_twitter():
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            if request.method == 'POST':
                try:
                    data = request.get_json()
                    action = data.get('action')
                    
                    if action == 'tweet':
                        text = data.get('text')
                        result = self.bot.twitter_client.post_tweet(text)
                    
                    elif action == 'follow':
                        username = data.get('username')
                        result = self.bot.twitter_client.follow_user(username)
                    
                    elif action == 'like':
                        tweet_id = data.get('tweet_id')
                        result = self.bot.twitter_client.like_tweet(tweet_id)
                    
                    elif action == 'retweet':
                        tweet_id = data.get('tweet_id')
                        result = self.bot.twitter_client.retweet(tweet_id)
                    
                    else:
                        return jsonify({'error': 'Invalid action'}), 400
                    
                    return jsonify(result)
                
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            else:
                # GET: Return Twitter statistics
                try:
                    stats = self.bot.twitter_client.get_statistics()
                    return jsonify(stats)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/cookies', methods=['GET', 'POST', 'DELETE'])
        def api_cookies():
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            if request.method == 'POST':
                try:
                    if 'file' in request.files:
                        # Import cookies from file
                        file = request.files['file']
                        if file.filename:
                            filename = secure_filename(file.filename)
                            file_path = os.path.join('temp', filename)
                            os.makedirs('temp', exist_ok=True)
                            file.save(file_path)
                            
                            result = self.bot.cookie_manager.import_cookies(file_path)
                            os.remove(file_path)
                            
                            return jsonify(result)
                    
                    else:
                        # Manual cookie addition
                        data = request.get_json()
                        domain = data.get('domain')
                        cookies = data.get('cookies')
                        
                        if domain and cookies:
                            self.bot.cookie_manager.add_cookies(domain, cookies)
                            return jsonify({'message': 'Cookies added successfully'})
                    
                    return jsonify({'error': 'Invalid request'}), 400
                
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            elif request.method == 'DELETE':
                try:
                    domain = request.args.get('domain')
                    if domain:
                        self.bot.cookie_manager.clear_cookies_for_domain(domain)
                        return jsonify({'message': f'Cookies cleared for {domain}'})
                    else:
                        self.bot.cookie_manager.clear_all_cookies()
                        return jsonify({'message': 'All cookies cleared'})
                
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            else:
                # GET: Return cookie statistics
                try:
                    stats = self.bot.cookie_manager.get_statistics()
                    return jsonify(stats)
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/schedule', methods=['GET', 'POST', 'DELETE'])
        def api_schedule():
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            if request.method == 'POST':
                try:
                    data = request.get_json()
                    task_name = data.get('task_name')
                    url = data.get('url')
                    schedule_type = data.get('schedule_type')
                    schedule_value = data.get('schedule_value')
                    method = data.get('method', 'requests')
                    
                    self.bot.schedule_task(task_name, url, schedule_type, schedule_value, method)
                    
                    return jsonify({'message': f'Task {task_name} scheduled successfully'})
                
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            elif request.method == 'DELETE':
                try:
                    task_name = request.args.get('task_name')
                    if task_name:
                        self.bot.remove_scheduled_task(task_name)
                        return jsonify({'message': f'Task {task_name} removed'})
                    else:
                        return jsonify({'error': 'Task name is required'}), 400
                
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            else:
                # GET: Return scheduled tasks
                try:
                    tasks = []
                    for task_name, task_info in self.bot.active_tasks.items():
                        job = self.bot.scheduler.get_job(task_info['job_id'])
                        next_run = job.next_run_time.isoformat() if job and job.next_run_time else None
                        
                        tasks.append({
                            'name': task_name,
                            'url': task_info['url'],
                            'method': task_info['method'],
                            'schedule_type': task_info['schedule_type'],
                            'schedule_value': task_info['schedule_value'],
                            'next_run': next_run,
                            'created_at': task_info['created_at'].isoformat()
                        })
                    
                    return jsonify(tasks)
                
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config', methods=['GET', 'POST'])
        def api_config():
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            if request.method == 'POST':
                try:
                    data = request.get_json()
                    
                    # Update configuration (limited to safe settings)
                    safe_keys = [
                        'CLAIM_INTERVAL', 'MAX_RETRIES', 'REQUEST_TIMEOUT',
                        'BROWSER_HEADLESS', 'TELEGRAM_NOTIFICATIONS',
                        'AUTO_RETRY', 'SCHEDULE_ENABLED'
                    ]
                    
                    updated = {}
                    for key, value in data.items():
                        if key in safe_keys:
                            self.config[key] = value
                            updated[key] = value
                    
                    return jsonify({
                        'message': 'Configuration updated',
                        'updated': updated
                    })
                
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            else:
                # GET: Return current configuration (safe keys only)
                try:
                    safe_config = {
                        'BOT_NAME': self.config.get('BOT_NAME'),
                        'BOT_VERSION': self.config.get('BOT_VERSION'),
                        'CLAIM_INTERVAL': self.config.get('CLAIM_INTERVAL'),
                        'MAX_RETRIES': self.config.get('MAX_RETRIES'),
                        'REQUEST_TIMEOUT': self.config.get('REQUEST_TIMEOUT'),
                        'BROWSER_HEADLESS': self.config.get('BROWSER_HEADLESS'),
                        'TELEGRAM_NOTIFICATIONS': self.config.get('TELEGRAM_NOTIFICATIONS'),
                        'AUTO_RETRY': self.config.get('AUTO_RETRY'),
                        'SCHEDULE_ENABLED': self.config.get('SCHEDULE_ENABLED'),
                        'CAPTCHA_ENABLED': self.config.get('CAPTCHA_ENABLED')
                    }
                    
                    return jsonify(safe_config)
                
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/logs')
        def api_logs():
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            try:
                limit = int(request.args.get('limit', 100))
                level = request.args.get('level', 'all')
                
                logs = self.db.get_recent_logs(limit=limit, level=level)
                return jsonify(logs)
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/export/<data_type>')
        def api_export(data_type):
            if not self._is_authenticated():
                return jsonify({'error': 'Unauthorized'}), 401
            
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                if data_type == 'claims':
                    file_path = self.bot.claimer.export_results(
                        f"exports/claims_{timestamp}.json"
                    )
                
                elif data_type == 'twitter':
                    file_path = self.bot.twitter_client.export_data(
                        f"exports/twitter_{timestamp}.json"
                    )
                
                elif data_type == 'database':
                    file_path = self.db.backup_database(
                        f"exports/database_{timestamp}.db"
                    )
                
                else:
                    return jsonify({'error': 'Invalid data type'}), 400
                
                return jsonify({
                    'message': 'Export completed',
                    'file_path': file_path,
                    'timestamp': timestamp
                })
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _setup_socketio_events(self):
        """Setup SocketIO events for real-time communication"""
        
        @self.socketio.on('connect')
        def handle_connect():
            if not self._is_authenticated():
                return False
            
            self.connected_clients.add(request.sid)
            join_room('dashboard')
            
            # Send initial status
            emit('status_update', self._get_real_time_status())
            
            self.logger.info(f"Client connected: {request.sid}")
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.connected_clients.discard(request.sid)
            leave_room('dashboard')
            
            self.logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_status')
        def handle_status_request():
            if not self._is_authenticated():
                return
            
            emit('status_update', self._get_real_time_status())
        
        @self.socketio.on('start_auto_claim')
        def handle_start_auto_claim(data):
            if not self._is_authenticated():
                return
            
            try:
                urls = data.get('urls', [])
                method = data.get('method', 'requests')
                interval = data.get('interval', 300)
                
                # Start auto claiming in background thread
                def auto_claim_task():
                    self.bot.start_claiming(urls, method, interval)
                
                thread = threading.Thread(target=auto_claim_task)
                thread.start()
                
                emit('auto_claim_started', {
                    'message': 'Auto claiming started',
                    'urls_count': len(urls)
                })
            
            except Exception as e:
                emit('error', {'message': str(e)})
        
        @self.socketio.on('stop_auto_claim')
        def handle_stop_auto_claim():
            if not self._is_authenticated():
                return
            
            self.bot.is_running = False
            emit('auto_claim_stopped', {'message': 'Auto claiming stopped'})
    
    def _is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return session.get('authenticated', False)
    
    def _get_real_time_status(self) -> Dict[str, Any]:
        """Get real-time status for dashboard"""
        try:
            claimer_stats = self.bot.claimer.get_statistics()
            twitter_stats = self.bot.twitter_client.get_statistics()
            
            return {
                'bot_running': self.bot.is_running,
                'active_claims': self.real_time_stats['active_claims'],
                'current_status': self.real_time_stats['current_status'],
                'last_claim_time': self.real_time_stats['last_claim_time'],
                'total_claims': claimer_stats.get('total_attempts', 0),
                'successful_claims': claimer_stats.get('successful_claims', 0),
                'success_rate': claimer_stats.get('success_rate', 0),
                'twitter_actions': twitter_stats.get('total_actions', 0),
                'scheduled_tasks': len(self.bot.active_tasks),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Error getting real-time status: {e}")
            return {'error': str(e)}
    
    def _start_real_time_updates(self):
        """Start background thread for real-time updates"""
        def update_loop():
            while self.running:
                try:
                    if self.connected_clients:
                        status = self._get_real_time_status()
                        self.socketio.emit('status_update', status, room='dashboard')
                    
                    time.sleep(5)  # Update every 5 seconds
                
                except Exception as e:
                    self.logger.error(f"Real-time update error: {e}")
                    time.sleep(10)
        
        self.update_thread = threading.Thread(target=update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def run(self, debug: bool = None):
        """Run the web interface"""
        debug = debug if debug is not None else self.debug
        
        self.running = True
        self._start_real_time_updates()
        
        self.logger.info(f"Starting web interface on {self.host}:{self.port}")
        
        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=debug,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            self.logger.error(f"Web interface error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """Stop the web interface"""
        self.running = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=5)

def create_web_interface(config: Dict[str, Any]) -> WebInterface:
    """Factory function to create web interface"""
    return WebInterface(config)

if __name__ == "__main__":
    # Load configuration
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        'WEB_INTERFACE_HOST': os.getenv('WEB_INTERFACE_HOST', '127.0.0.1'),
        'WEB_INTERFACE_PORT': int(os.getenv('WEB_INTERFACE_PORT', 8080)),
        'WEB_INTERFACE_SECRET_KEY': os.getenv('WEB_INTERFACE_SECRET_KEY', 'asyafira-secret'),
        'WEB_ADMIN_USERNAME': os.getenv('WEB_ADMIN_USERNAME', 'admin'),
        'WEB_ADMIN_PASSWORD': os.getenv('WEB_ADMIN_PASSWORD', 'asyafira2024'),
        'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true'
    }
    
    # Create and run web interface
    web_interface = create_web_interface(config)
    web_interface.run()