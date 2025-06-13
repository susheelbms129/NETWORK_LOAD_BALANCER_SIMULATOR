from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
from .load_balancer import LoadBalancer
from .servers.server import RealServer
import threading
import time
import random
import os
import logging
from collections import deque
from datetime import datetime

APP_DIR = os.path.dirname(os.path.abspath(__file__))

LOG_DIR = os.path.join(APP_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    filename=os.path.join(LOG_DIR, 'app.log'),
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__,
    template_folder=os.path.join(APP_DIR, 'templates'),
    static_folder=os.path.join(APP_DIR, 'static')
)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

servers = []
load_balancer = None
simulation_running = False

total_requests = 0
successful_requests = 0
request_times = deque(maxlen=100)
requests_per_second = deque(maxlen=10) 
last_request_time = time.time()
current_second_requests = 0

def log_callback(message):
    logger.debug(f"Log callback: {message}")
    socketio.emit('log_message', {'message': message})

def update_request_metrics(success=True, processing_time=None):
    global total_requests, successful_requests, current_second_requests, last_request_time
    
    total_requests += 1
    if success:
        successful_requests += 1
    
    if processing_time:
        request_times.append(processing_time)
    
    current_time = time.time()
    if current_time - last_request_time >= 1:
        requests_per_second.append(current_second_requests)
        current_second_requests = 0
        last_request_time = current_time
    current_second_requests += 1

def get_metrics():
    success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
    avg_response_time = sum(request_times) / len(request_times) if request_times else 0
    active_servers = sum(1 for server in servers if server.status == "healthy")
    
    current_rps = current_second_requests
    if requests_per_second:
        current_rps = sum(requests_per_second) / len(requests_per_second)
    
    return {
        "total_requests": total_requests,
        "success_rate": round(success_rate, 2),
        "active_servers": active_servers,
        "avg_response_time": round(avg_response_time * 1000, 2), 
        "requests_per_second": round(current_rps, 2)
    }

@app.route('/')
def index():
    logger.debug("Serving index page")
    try:
        logger.debug(f"Template folder: {app.template_folder}")
        logger.debug(f"Available templates: {os.listdir(app.template_folder)}")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        return str(e), 500

@app.route('/api/start', methods=['POST'])
def start_simulation():
    global servers, load_balancer, simulation_running, total_requests, successful_requests, request_times, requests_per_second
    
    logger.debug("Received start simulation request")
    
    if simulation_running:
        logger.warning("Simulation already running")
        return jsonify({'error': 'Simulation already running'}), 400
    
    try:
        data = request.get_json()
        logger.debug(f"Start simulation data: {data}")
        
        total_requests = 0
        successful_requests = 0
        request_times.clear()
        requests_per_second.clear()
        
        num_servers = data.get('num_servers', 3)
        algorithm = data.get('algorithm', 'round_robin')
        health_check_interval = data.get('health_check_interval', 2)
        fail_rate = data.get('fail_rate', 0)
        
        servers = []
        for i in range(num_servers):
            server = RealServer(f"S{i}", 8000 + i, fail_rate=fail_rate, health_check_interval=health_check_interval)
            server.start()
            servers.append(server)
            logger.debug(f"Started server {i} on port {8000 + i}")
        
        load_balancer = LoadBalancer(servers, algorithm, log_callback)
        load_balancer.start_health_checker(health_check_interval)
        
        simulation_running = True
        logger.info("Simulation started successfully")
        return jsonify({'message': 'Simulation started successfully'})
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_simulation():
    global simulation_running
    
    logger.debug("Received stop simulation request")
    
    if not simulation_running:
        logger.warning("No simulation running")
        return jsonify({'error': 'No simulation running'}), 400
    
    try:
        if load_balancer:
            load_balancer.stop_health_checker()
        
        for server in servers:
            server.stop()
        
        simulation_running = False
        logger.info("Simulation stopped successfully")
        return jsonify({'message': 'Simulation stopped successfully'})
    except Exception as e:
        logger.error(f"Error stopping simulation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_request', methods=['POST'])
def send_request():
    logger.debug("Received send request")
    
    if not simulation_running:
        logger.warning("No simulation running")
        return jsonify({'error': 'No simulation running'}), 400
    
    try:
        data = request.get_json()
        
        logger.debug(f"Request data: {data}")
        
        client_id = data.get('client_id', f'C{random.randint(1000, 9999)}')
        client_ip = data.get('client_ip', request.remote_addr)
        payload = data.get('payload', 'Test request')
        
        client_port = request.environ.get('REMOTE_PORT')
        response = load_balancer.process_request(client_id, client_port, client_ip, payload)
        
        if response:
            update_request_metrics(True, response.get('processing_time'))
        else:
            update_request_metrics(False)
            
        logger.debug(f"Request response: {response}")
        return jsonify(response if response else {'error': 'Request failed'})
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        update_request_metrics(False)
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    logger.debug("Received status request")
    
    if not simulation_running:
        logger.warning("No simulation running")
        return jsonify({'error': 'No simulation running'}), 400
    
    try:
        server_status = [
            {
                'id': server.server_id,
                'status': server.status,
                'active_connections': server.active_connections
            }
            for server in servers
        ]
        
        response = {
            'servers': server_status,
            'algorithm': load_balancer.algorithm,
            'metrics': get_metrics()
        }
        logger.debug(f"Status response: {response}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test():
    return "Flask app is working!"

if __name__ == '__main__':
    os.makedirs('app/static', exist_ok=True)
    os.makedirs('app/templates', exist_ok=True)
    
    logger.info("Starting Flask application")
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')