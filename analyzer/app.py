import json
import os
import requests
import logging
import httpx
import yaml
import connexion
from datetime import datetime
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import urllib.parse
import logging.config
import threading
from pykafka import KafkaClient
from pykafka.common import OffsetType

# Load configuration
with open("app_conf.yml", "r") as f:
    app_config = yaml.safe_load(f)

# Load logging configuration
with open("log_conf.yml", "r") as f:
    log_config = yaml.safe_load(f)
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

# Kafka Configuration
KAFKA_HOST = app_config["events"]["hostname"]
KAFKA_PORT = app_config["events"]["port"]
KAFKA_TOPIC = app_config["events"]["topic"]

# Initialize Kafka Consumer
client = KafkaClient(hosts=f"{KAFKA_HOST}:{KAFKA_PORT}")
topic = client.topics[str.encode(KAFKA_TOPIC)]
consumer = topic.get_simple_consumer(consumer_group=b'analyzer_group',
                                     reset_offset_on_start=False,
                                     auto_offset_reset=OffsetType.LATEST)

rain_conditions = []
flooding_events = []

def process_messages():
    for msg in consumer:
        if msg is not None:
            try:
                msg_str = msg.value.decode("utf-8")
                msg_data = json.loads(msg_str)
                event_type = msg_data.get("type")
                payload = msg_data.get("payload")

                logger.info(f"Received event '{event_type}' from Kafka")

                if event_type == "rainfall":
                    rain_conditions.append(payload)
                elif event_type == "flooding":
                    flooding_events.append(payload)

                consumer.commit_offsets()
            except Exception as e:
                logger.error(f"Error processing Kafka message: {str(e)}")


def get_rainfall_event(index):
    counter = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if counter == index:
            payload = data["payload"]
            fixed_payload = {
                "trace_id": payload.get("trace_id"),
                "device_id": payload.get("device_id"),
                "rain_location_logitude": payload.get("rain_location_logitude"),
                "rain_location_latitude": payload.get("rain_location_latitude"),
                "rainfall_nm": payload.get("rainfall_nm"),
                "intensity": payload.get("intensity"),
                "timestamp": payload.get("timestamp")
            }
            return jsonify(data["payload"]), 200
        counter += 1
    return {"message": f"No message at index {index}!"}, 404


# def get_flooding_event(index):
#     counter = 0
#     for msg in consumer:
#         message = msg.value.decode("utf-8")
#         data = json.loads(message)
#         if counter == index:
#             return jsonify(data["payload"]), 200
#         counter += 1
#     return {"message": f"No message at index {index}!"}, 404

def get_flooding_event(index):
    counter = 0
    for msg in consumer:
        message = msg.value.decode("utf-8")
        data = json.loads(message)

        if counter == index:
            payload = data["payload"]


            fixed_payload = {
                "trace_id": payload.get("trace_id"),
                "device_id": payload.get("device_id"),
                "flood_location_longitude": payload.get("flood_location_longitude"),
                "flood_location_latitude": payload.get("flood_location_latitude"),
                "flood_level": payload.get("flood_level"),
                "severity": payload.get("severity"),
                "timestamp": payload.get("timestamp")
            }

            return jsonify(fixed_payload), 200
        
        counter += 1

    return {"message": f"No message at index {index}!"}, 404

def get_event_statistics():
    stats = {
        "num_rain_conditions": len(rain_conditions),
        "num_flooding_events": len(flooding_events)
    }
    return jsonify(stats), 200


# Setup Kafka Consumer Thread
def setup_kafka_thread():
    kafka_thread = threading.Thread(target=process_messages)
    kafka_thread.setDaemon(True)
    kafka_thread.start()


# Initialize Connexion App
app = connexion.FlaskApp(__name__, specification_dir="./")
app.add_api("analyzer_conf.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    logger.info("Analyzer service starting...")
    setup_kafka_thread()
    app.run(port=8080, host="0.0.0.0")
