import requests
import time
import random
import logging
import threading
import os

class LoadBalancer:
    def __init__(self, servers, algorithm="round_robin", log_callback=None):
        self.servers = servers
        self.algorithm = algorithm
        self.log_callback = log_callback
        self.counter = 0 
        self.health_checker = None
        
        log_directory = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_directory, exist_ok=True)  # Ensure the logs directory exists

        logging.basicConfig(
            filename=os.path.join(log_directory, 'load_balancer.log'),  # Save logs to 'logs/load_balancer.log'
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filemode='a'  # Append to the log file
        )
        self.logger = logging.getLogger("LoadBalancer")

    def start_health_checker(self, interval=2):
        self.health_checker = HealthChecker(
            self.servers,
            self.log_callback,
            interval
        )
        self.health_checker.start()

    def stop_health_checker(self):
        if self.health_checker:
            self.health_checker.stop()

    def process_request(self, client_id, client_port, payload, client_ip=None):
        start_time = time.time()
        try:
            server = self.select_server(client_ip or client_port)
            if not server:
                msg = f"No healthy server available for Client {client_id}"
                self.log_callback(msg)
                self.logger.warning(msg)
                return None

            msg = f"{self.algorithm.upper()} -> Client {client_id} (IP: {client_ip or client_port}) assigned to Server {server.server_id} [Active: {server.active_connections}]"
            self.log_callback(msg)
            self.logger.info(msg)

            try:
                response = requests.post(
                    f"http://127.0.0.1:{server.port}/process",
                    json={"client_id": client_id, "payload": payload},
                    timeout=5
                )
                response_data = response.json()
                processing_time = time.time() - start_time
                response_data['processing_time'] = processing_time
                msg = f"Client {client_id} Response: {response_data['message']} [Time: {processing_time:.3f}s]"
                self.log_callback(msg)
                return response_data

            except requests.RequestException as e:
                self.log_callback(str(e))
                self.logger.warning(str(e))
                redirected_server = self.select_server(client_port, exclude=server)
                if redirected_server:
                    self.log_callback(f"Redirecting Client {client_id} to Server {redirected_server.server_id}")
                    self.logger.info(f"Redirecting Client {client_id} to Server {redirected_server.server_id}")
                    response = requests.post(
                        f"http://127.0.0.1:{redirected_server.port}/process",
                        json={"client_id": client_id, "payload": payload},
                        timeout=5
                    )
                    response_data = response.json()
                    processing_time = time.time() - start_time
                    response_data['processing_time'] = processing_time
                    return response_data
                else:
                    self.log_callback(f"No healthy server available to redirect Client {client_id}")
                    return None

        except Exception as e:
            msg = f"Error serving Client {client_id}: {str(e)}"
            self.log_callback(msg)
            self.logger.error(msg)
            return None

    def select_server(self, client_identifier, exclude=None):
        healthy_servers = [s for s in self.servers if s.is_alive() and s != exclude]
        if not healthy_servers:
            return None

        if self.algorithm == "round_robin":
            server = healthy_servers[self.counter % len(healthy_servers)]
            self.counter += 1
            return server
        elif self.algorithm == "least_connections":
            return min(healthy_servers, key=lambda s: s.active_connections)
        elif self.algorithm == "ip_hash":
            if isinstance(client_identifier, str) and '.' in client_identifier:
                ip_parts = client_identifier.split('.')
                hash_value = sum(int(part) * (256 ** (3-i)) for i, part in enumerate(ip_parts))
            else:
                hash_value = hash(client_identifier)
            server_index = hash_value % len(healthy_servers)
            return healthy_servers[server_index]
        else:
            return random.choice(healthy_servers)

class HealthChecker(threading.Thread):
    def __init__(self, servers, log_callback, interval):
        super().__init__(daemon=True)
        self.servers = servers
        self.log_callback = log_callback
        self.interval = interval
        self.running = True
        self._stop_event = threading.Event()

    def stop(self):
        self.running = False
        self._stop_event.set()

    def run(self):
        while self.running and not self._stop_event.is_set():
            for server in self.servers:
                try:
                    response = requests.get(f"http://127.0.0.1:{server.port}/health", timeout=2)
                    if response.status_code == 200:
                        response_data = response.json()
                        server.status = response_data.get('status', 'down')
                    else:
                        server.status = "down"
                except requests.RequestException:
                    server.status = "down"

                msg = f"Health Check: Server {server.server_id} is {server.status.upper()}"
                self.log_callback(msg)
                logging.info(msg)

            self._stop_event.wait(self.interval)
