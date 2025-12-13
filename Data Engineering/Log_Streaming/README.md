# Real-Time Log Streaming Pipeline

A scalable streaming architecture that generates high-volume web server logs, buffers them in Apache Kafka, and processes them in real-time to detect anomalies.

## Project Architecture
1. **Producer Service**: 
   - Uses `Faker` to generate realistic web logs (JSON).
   - Simulates traffic spikes and random errors (500, 403).
   - Publishes events to the `web-server-logs` Kafka topic.
2. **Message Broker**:
   - Single-node **Apache Kafka** cluster (managed by Zookeeper).
3. **Consumer Service**:
   - Subscribes to the log stream.
   - Filters for "Suspicious Activity" (e.g., 500 errors or failed logins).
   - Logs alerts to the console (simulating pager duty/slack notification).

## Prerequisites
- Docker & Docker Compose

## How to Run
1. **Clone and Enter Directory**:
   ```bash
   cd Log_Streaming
   ```

2. **Start Cluster**:
   ```bash
   docker-compose up --build
   ```
   
3. **Observe Output**:
   - You will see logs in the `producer` container output.
   - You will see **ALERTS** in the `consumer` container output when errors are generated.

   ```text
   producer_1  | Sent: GET /home 200
   consumer_1  | Processed: 2025-12-13T10:00:00
   producer_1  | Sent: POST /login 401
   consumer_1  | ALERT: Suspicious detected! IP=192.168.1.5 Status=401 Path=/login
   ```

## Technologies
- **Python**
- **Apache Kafka**: Event Streaming
- **Docker**: Orchestration
- **Faker**: Synthetic Data Generation
