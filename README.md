# Network Load Balancer Simulation

A Python-based simulation of a Network Load Balancer that demonstrates traffic routing, failure handling, and server health monitoring using customizable load balancing strategies.

## 📌 Features

- 🔁 Load balancing using:
  - Round Robin
  - Least Connections
  - IP Hashing
- 🩺 Server health monitoring with periodic health checks
- ⚠️ Simulated server failure and failover
- 👥 Client request simulation
- 🖥️ Interactive and modern web-based GUI (Flask + Tailwind)
- 📜 Real-time logging and file-based logs
- 🧵 Concurrency handled using Python threading

## 🎯 Motivation

The project was built to provide a **visual, interactive simulation of load balancing** for academic and educational purposes. It aims to bridge the gap between theoretical networking concepts and their practical applications in modern distributed systems.

## 🛠️ Technologies Used

- **Python 3**
  - `socket`, `threading`, `logging` (standard libraries)
- **Flask** – for the backend web server
- **HTML + Tailwind CSS** – for the frontend UI
- **Concurrency** – via Python threading
- **Logging** – both live and file-based logs

## 🧱 Project Structure & Modules

- **Traffic Distribution** using custom algorithms
- **Server Failure Simulation** with control over failure rates
- **Client Simulation** with configurable load
- **Health Check Daemon** for backend server status
- **GUI** to:
  - Select algorithm
  - Define number of servers/clients
  - Tune failure and health check frequency
  - View live logs and status

## 🗓️ Development Timeline

| Week | Work |
|------|------|
| 1    | Research on load balancing & architecture |
| 2    | Basic request routing with Python threads |
| 3    | Implement algorithms: Round Robin, Least Connections, IP Hash |
| 4    | Add server health checks & failure simulation |
| 5    | Build GUI with Flask + Tailwind |
| 6    | Add logs, tuning options, delay control |
| 7    | Final testing, cleanup & documentation |

## ⚙️ Requirements

### Software
- Python 3.x
- Flask
- HTML + Tailwind (no build tools required)

### Hardware
- Standard PC or laptop
- OS: Windows/Linux/macOS

## 🚀 How to Run

1. **Clone the repository**:
   ```bash
   git clone https://github.com/AbdMuh/network-load-balancer.git
   cd network-load-balancer
# Network Load Balancer

