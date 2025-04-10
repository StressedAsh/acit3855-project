import connexion
import json
import uuid
import httpx
import yaml
import logging.config
from datetime import datetime
import logging.config
from pykafka import KafkaClient
from datetime import datetime
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

with open("config/receiver/app_conf.yml", "r") as f:
    app_config = yaml.safe_load(f)

# Kafka configurations
KAFKA_HOST = app_config["events"]["hostname"]
KAFKA_PORT = app_config["events"]["port"]
KAFKA_TOPIC = app_config["events"]["topic"]

STORAGE_SERVICE_URL = app_config["storage_service"]["url"]

with open("config/receiver/log_conf.yml", "r") as f:
    log_config = yaml.safe_load(f)
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

# Initialize Kafka producer
client = KafkaClient(hosts=f"{KAFKA_HOST}:{KAFKA_PORT}")
topic = client.topics[str.encode(KAFKA_TOPIC)]
producer = topic.get_sync_producer()


# def forward_event(event_type, event_data=None, params=None, method="post"):
#     url = f'{STORAGE_SERVICE_URL}/rain/{event_type}'
#     try:
#         if method == "post":
#             response = httpx.post(url, json=event_data)
#         elif method == "get":
#             response = httpx.get(url, params=params)

#         response.raise_for_status()
#         return response.text, response.status_code

#     except httpx.HTTPStatusError as e:
#         logger.error(f"Failed to forward event {event_type}: {e.response.text}")
#         return json.dumps({"error": e.response.text}), e.response.status_code

#     except httpx.RequestError as e:
#         logger.error(f"Request error when forwarding event {event_type}: {str(e)}")
#         return json.dumps({"error": str(e)}), 500

def send_to_kafka(event_type, event_data):
    try:
        trace_id = str(uuid.uuid4())
        event_data["trace_id"] = trace_id
        event_data["timestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        message = {
            "type": event_type,
            "payload": event_data
        }

        producer.produce(json.dumps(message).encode("utf-8"))
        logger.info(f"Produced event '{event_type}' with trace_id: {trace_id}")

        return {"message": f"Event '{event_type}' sent to Kafka", "trace_id": trace_id}, 201

    except Exception as e:
        logger.error(f"Error producing event '{event_type}': {str(e)}")
        return json.dumps({"error": str(e)}), 500

def report_rainfalls(body):
    return send_to_kafka("rainfall", body)

def report_floodings(body):
    return send_to_kafka("flooding", body)


app = connexion.FlaskApp(__name__, specification_dir="./")
app.add_api("receiver_conf.yaml", strict_validation=True, validate_responses=True) 

app.add_middleware(CORSMiddleware,position=MiddlewarePosition.BEFORE_EXCEPTION,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

if __name__ == "__main__":
    logger.info("Receiver service starting...")
    app.run(port=8080, host="0.0.0.0")