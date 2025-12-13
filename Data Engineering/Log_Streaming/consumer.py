import json
import logging
from kafka import KafkaConsumer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_suspicious(log):
    """Simple logic to identify suspicious activity."""
    # Example: High latency or Server Errors
    if log['status_code'] >= 500:
        return True
    if log['status_code'] == 401 and log['endpoint'] == '/login':
        return True
    return False

def main():
    logger.info("Starting Consumer...")
    
    # Auto-commit offset, start from latest
    consumer = KafkaConsumer(
        'web-server-logs',
        bootstrap_servers=['kafka:9092'],
        auto_offset_reset='latest',
        enable_auto_commit=True,
        group_id='monitor-service',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    for message in consumer:
        log = message.value
        if is_suspicious(log):
            logger.warning(f"ALERT: Suspicious detected! IP={log['ip']} Status={log['status_code']} Path={log['endpoint']}")
        else:
            logger.debug(f"Processed: {log['timestamp']}")

if __name__ == "__main__":
    main()
