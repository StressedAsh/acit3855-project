import os
import json
import yaml
import time
import logging
import logging.config
import connexion
from flask import Response
from pykafka import KafkaClient

with open("config/anomaly_conf.yml", "r") as f:
    app_config = yaml.safe_load(f.read())

KAFKA_HOST = app_config["kafka"]["hostname"]
KAFKA_PORT = app_config["kafka"]["port"]
ANOMALY_FILE = app_config["datastore"]["filename"]
MAX_LON = app_config["thresholds"]["max_longitude"]

MAX_LON = int(os.environ.get("MAX_LON", 180))

with open("config/log_conf.yml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")
logger.info(f"Anomaly Detector started. Threshold MAX_LON={MAX_LON}")

def detect_longitude_anomaly(event_type, payload):
    if event_type == "RainConditions":
        lon = payload.get("rain_location_longitude")
    elif event_type == "Flooding":
        lon = payload.get("flood_location_longitude")
    else:
        return None

    if lon is not None and (lon < -MAX_LON or lon > MAX_LON):
        return f"Detected longitude: {lon}; threshold ±{MAX_LON}"
    return None

def update_anomalies():
    logger.debug("PUT /update called")
    start_time = time.time()

    client = KafkaClient(hosts=f"{KAFKA_HOST}:{KAFKA_PORT}")
    topic = client.topics[b"events"]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    anomaly_list = []
    count = 0

    for msg in consumer:
        if msg is not None:
            event = json.loads(msg.value.decode("utf-8"))
            event_type = event.get("type")
            trace_id = event.get("trace_id")
            payload = event.get("payload")
            event_id = payload.get("device_id")

            description = detect_longitude_anomaly(event_type, payload)
            if description:
                anomaly = {
                    "event_id": event_id,
                    "trace_id": trace_id,
                    "event_type": event_type,
                    "description": description
                }
                anomaly_list.append(anomaly)
                logger.debug(f"Anomaly detected and logged: {description}")
                count += 1

    with open(ANOMALY_FILE, "w") as f:
        json.dump(anomaly_list, f, indent=2)

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"PUT /update processed {count} anomalies in {elapsed}s")
    return { "num_anomalies": count }, 200

def get_anomalies(event_type=None):
    logger.debug(f"GET /anomalies called with event_type={event_type}")

    if not os.path.isfile(ANOMALY_FILE):
        return { "message": "Datastore missing" }, 404

    try:
        with open(ANOMALY_FILE, "r") as f:
            anomalies = json.load(f)
    except Exception:
        return { "message": "Datastore is corrupted" }, 404

    if event_type:
        if event_type not in ["RainConditions", "Flooding"]:
            return { "message": "Invalid event type. Must be RainConditions or Flooding" }, 400
        anomalies = [a for a in anomalies if a["event_type"] == event_type]

    if not anomalies:
        return Response(status=204)

    logger.debug(f"GET /anomalies returned {len(anomalies)} anomalies")
    return anomalies, 200

app = connexion.FlaskApp(__name__, specification_dir="./")
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    logger.info("Anomaly Detector's threshold values are set to - 180 and 180")
    app.run(port=8120)
