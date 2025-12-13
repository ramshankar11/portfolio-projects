import time
import json
import random
import logging
from kafka import KafkaProducer
from faker import Faker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fake = Faker()

def generate_log():
    """Generate a random web server log."""
    return {
        "timestamp": fake.iso8601(),
        "ip": fake.ipv4(),
        "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
        "endpoint": random.choice(["/api/v1/users", "/login", "/home", "/products", "/checkout"]),
        "status_code": random.choice([200, 201, 400, 401, 403, 404, 500]),
        "latency_ms": random.randint(10, 1000)
    }

def main():
    # Wait for Kafka to be ready
    time.sleep(10)
    
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

    logger.info("Starting log generation...")
    try:
        while True:
            log_entry = generate_log()
            producer.send('web-server-logs', value=log_entry)
            logger.info(f"Sent: {log_entry['method']} {log_entry['endpoint']} {log_entry['status_code']}")
            time.sleep(random.uniform(0.5, 2.0)) # Simulate traffic
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        producer.close()

if __name__ == "__main__":
    main()
