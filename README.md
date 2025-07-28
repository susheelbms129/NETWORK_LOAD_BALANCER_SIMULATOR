Network Load Balancer Simulator
A Python-based project that simulates how a network load balancer works by distributing client requests to multiple backend servers using different algorithms.
It is designed to provide an interactive learning experience for understanding how load balancing improves performance and fault tolerance.

Features
Implements multiple load balancing algorithms:

Round Robin

Least Connections

IP Hashing

Monitors server health and automatically handles failures

Simulates real-world scenarios of client request routing and server failover

Provides a simple web-based dashboard for live monitoring

Uses multithreading to handle concurrent client-server communication

Maintains real-time logs for traffic and server status

Motivation
This project was developed as part of our academic work to gain a practical understanding of load balancing concepts.
It bridges the gap between theoretical networking knowledge and its real-world applications in modern distributed systems.

Technologies Used
Python 3 for core simulation logic

Flask for the web interface

HTML + Tailwind CSS for the front-end UI

Threading & Logging modules in Python for concurrency and monitoring

How to Run

Clone the repository

git clone https://github.com/susheelbms129/NETWORK_LOAD_BALANCER_SIMULATOR.git
cd Network-Load-Balancer

Install dependencies


pip install flask


Run the application


python app.py


Open your browser and go to

http://127.0.0.1:5000
