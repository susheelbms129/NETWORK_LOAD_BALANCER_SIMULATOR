from flask import Flask, jsonify, request
import time
import random
import logging
import threading
import sys
import socket
from werkzeug.serving import make_server
import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Lock 
import os

log_directory = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_directory, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_directory, 'server.log')), 
        logging.StreamHandler(sys.stdout)  
    ]
)

logger = logging.getLogger("Server")

class RealServer:
    def __init__(self, server_id, port, fail_rate=0, health_check_interval=2):
        self.server_id = server_id
        self.port = port
        self.fail_rate = fail_rate
        self.app = Flask(f"server_{server_id}")
        self.status = "healthy"
        self.active_connections = 0
        self.connection_lock = Lock() 
        self.interval = health_check_interval
        self.server_thread = None
        self.status_thread = None
        self.server = None
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.setup_routes()
        logger.info(f"Initialized server {server_id} on port {port} with fail rate {fail_rate}%")

    def is_port_available(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return True
            except socket.error:
                return False

    def should_fail(self):
        """Determine if the server should fail based on fail rate"""
        result = random.randint(1, 100) <= self.fail_rate
        logger.debug(f"Server {self.server_id} should fail: {result}")
        return result

    def update_status(self): 
        """Update server status at regular intervals"""
        while self.running:  
            if self.should_fail():
                self.status = "down"
                logger.info(f"Server {self.server_id} marked as down due to fail rate")
            else:
                self.status = "healthy"
                logger.info(f"Server {self.server_id} is healthy")
            time.sleep(self.interval) 

    def setup_routes(self):
        @self.app.route('/health')
        def health_check():
            logger.debug(f"Health check for server {self.server_id}")
            return jsonify({
                "status": self.status,
                "server_id": self.server_id,
                "active_connections": self.active_connections
            })

        @self.app.route('/process', methods=['POST'])
        def process_request():
            logger.debug(f"Processing request for server {self.server_id}")
            with self.connection_lock:
                self.active_connections += 1
            start_time = time.time()

            def process_in_background():
                try:
                    time.sleep(random.uniform(0.5, 1.5))
                    data = request.get_json()
                    client_id = data.get('client_id', 'unknown')

                    response = {
                        "server_id": self.server_id,
                        "client_id": client_id,
                        "message": f"Request processed by server {self.server_id}",
                        "processing_time": round(time.time() - start_time, 3),
                        "active_connections": self.active_connections
                    }

                    logger.info(f"Server {self.server_id} processed request from client {client_id}")
                    return response
                except Exception as e:
                    logger.error(f"Error processing request on server {self.server_id}: {str(e)}")
                    return {"error": str(e)}, 500
                finally:
                    with self.connection_lock:
                        self.active_connections -= 1

            self.executor.submit(process_in_background)
            
            return jsonify({
                "server_id": self.server_id,
                "message": "Request accepted for processing",
                "active_connections": self.active_connections
            })

    def start(self):
        try:
            if not self.is_port_available(self.port):
                raise Exception(f"Port {self.port} is already in use")
            
            logger.info(f"Starting server {self.server_id} on port {self.port}")
            self.running = True  
            self.status_thread = threading.Thread(target=self.update_status)
            self.status_thread.daemon = True
            self.status_thread.start()

            self.server = make_server('127.0.0.1', self.port, self.app)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            logger.info(f"Server {self.server_id} started successfully")
        except Exception as e:
            logger.error(f"Error starting server {self.server_id}: {str(e)}")
            raise

    def stop(self):
        try:
            logger.info(f"Stopping server {self.server_id}")
            self.running = False
            if self.server:
                self.server.shutdown()
                self.server_thread.join(timeout=5)
                self.server = None
                self.server_thread = None
            if self.status_thread:
                self.status_thread.join(timeout=5)
                self.status_thread = None
            self.executor.shutdown(wait=True) 
            logger.info(f"Server {self.server_id} stopped")
        except Exception as e:
            logger.error(f"Error stopping server {self.server_id}: {str(e)}")
            raise

    def is_alive(self):
        return self.status == "healthy"
