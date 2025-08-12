from kafka import KafkaProducer
import time

# Configs
KAFKA_TOPIC = "logs"
KAFKA_BOOTSTRAP_SERVERS = "host.docker.internal:9092"  # from your docker compose

# Initialize producer
producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

# Stream the file line by line
with open("data/access.log", "r") as file:  # Replace with actual path
    for line in file:
        producer.send(KAFKA_TOPIC, value=line.strip().encode("utf-8"))
        time.sleep(0.5)  # Simulate stream — adjust for speed

producer.flush()
print("Log file streaming completed.")
