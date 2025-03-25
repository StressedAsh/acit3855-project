import connexion
from connexion import NoContent
import json
import yaml
import logging.config
import threading
from datetime import datetime
from flask import request, jsonify
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from models import RainConditions, Floodings, Base
import functools
from pykafka import KafkaClient
from pykafka.common import OffsetType
from manage import create_tables

with open("app_conf.yml", "r") as f:
    app_config = yaml.safe_load(f.read())

with open("log_conf.yml", "r") as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger("basicLogger")

# DATABASE_URI = "mysql+pymysql://myuser:mypassword@localhost/mydatabase"
DATABASE_URI = "mysql+pymysql://myuser:mypassword@db/mydatabase"
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

# Kafka setup
KAFKA_HOST = app_config["events"]["hostname"]
KAFKA_PORT = app_config["events"]["port"]
KAFKA_TOPIC = app_config["events"]["topic"]

def make_session():
    return sessionmaker(bind=engine)()

def process_messages():
    client = KafkaClient(hosts=f"{KAFKA_HOST}:{KAFKA_PORT}")
    # topic = client.topics[str.encode(KAFKA_TOPIC)]
    topic = client.topics[KAFKA_TOPIC]
    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                         reset_offset_on_start=False,
                                         auto_offset_reset=OffsetType.LATEST)
    
    for msg in consumer:
        if msg is not None:
            msg_str = msg.value.decode("utf-8")
            msg_data = json.loads(msg_str)
            event_type = msg_data["type"]
            payload = msg_data["payload"]

            logger.info(f"Received event '{event_type}' from Kafka")

            session = Session()
            try:
                if event_type == "rainfall":
                    event = RainConditions(
                        device_id=payload["device_id"],
                        rain_location_longitude=payload["rain_location_longitude"],
                        rain_location_latitude=payload["rain_location_latitude"],
                        rainfall_nm=payload["rainfall_nm"],
                        intensity=payload["intensity"],
                        timestamp=datetime.fromisoformat(payload["timestamp"]),
                        trace_id=payload["trace_id"]
                    )
                    session.add(event)

                elif event_type == "flooding":
                    event = Floodings(
                        device_id=payload["device_id"],
                        flood_location_longitude=payload["flood_location_longitude"],
                        flood_location_latitude=payload["flood_location_latitude"],
                        flood_level=payload["flood_level"],
                        severity=payload["severity"],
                        timestamp=datetime.fromisoformat(payload["timestamp"]),
                        trace_id=payload["trace_id"]
                    )
                    session.add(event)

                session.commit()
                logger.info(f"Stored {event_type} event with trace_id {payload['trace_id']}")
            
            except Exception as e:
                session.rollback()
                logger.error(f"Error processing event '{event_type}': {str(e)}")
            
            finally:
                session.close()
                consumer.commit_offsets()

def setup_kafka_thread():
    t1 = threading.Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()


app = connexion.FlaskApp(__name__, specification_dir="./")
app.add_api("storage_conf.yaml", strict_validation=True, validate_responses=True)

def use_db_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = make_session()
        trace_id = kwargs.get("body", {}).get("trace_id")
        event_name = func.__name__[7:]
        try:
            return func(session, *args, **kwargs)
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding data to database: {e}")
            return {"message": "Failed to add data"}, 500
        finally:
            session.close()
            logger.info(f"Stored {event_name} event with a trace id of {trace_id}")
    return wrapper

# Get Requests
@use_db_session
def get_rain_conditions(session):
    try:
        start_timestamp = request.args.get("start_timestamp")
        end_timestamp = request.args.get("end_timestamp")

        if not start_timestamp or not end_timestamp:
            return jsonify({"error": "Both start_timestamp and end_timestamp are required"}), 400

        start = datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S")

        results = session.query(RainConditions).filter(
            RainConditions.timestamp >= start,
            RainConditions.timestamp <= end
        ).all()

        logger.info("Found %d rain condition events (start: %s, end: %s)", len(results), start, end)
        return jsonify([event.to_dict() for event in results]), 200

    except Exception as e:
        logger.error(f"Error retrieving rain conditions: {str(e)}")
        return jsonify({"error": str(e)}), 400

@use_db_session
def get_flooding_events(session):
    try:
        start_timestamp = request.args.get("start_timestamp")
        end_timestamp = request.args.get("end_timestamp")

        if not start_timestamp or not end_timestamp:
            return jsonify({"error": "Both start_timestamp and end_timestamp are required"}), 400

        start = datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S")

        results = session.query(Floodings).filter(
            Floodings.timestamp >= start,
            Floodings.timestamp <= end
        ).all()

        logger.info("Found %d flooding events (start: %s, end: %s)", len(results), start, end)
        return jsonify([event.to_dict() for event in results]), 200

    except Exception as e:
        logger.error(f"Error retrieving flooding events: {str(e)}")
        return jsonify({"error": str(e)}), 400
    
# Post Requests
@use_db_session
def report_rainfalls(session, body):
    try:
        timestamp = datetime.fromisoformat(body["timestamp"])
        event = RainConditions(
            device_id=body["device_id"],
            rain_location_longitude=body["rain_location_longitude"],
            rain_location_latitude=body["rain_location_latitude"],
            rainfall_nm=body["rainfall_nm"],
            intensity=body["intensity"],
            timestamp=timestamp,
            trace_id=body["trace_id"]
        )
        session.add(event)
        session.commit()
        return NoContent, 201

    except Exception as e:
        session.rollback()
        logger.error(f"Error adding rainfall event: {str(e)}")
        return jsonify({"error": str(e)}), 400

@use_db_session
def report_floodings(session, body):
    try:
        timestamp = datetime.fromisoformat(body["timestamp"])
        event = Floodings(
            device_id=body["device_id"],
            flood_location_longitude=body["flood_location_longitude"],
            flood_location_latitude=body["flood_location_latitude"],
            flood_level=body["flood_level"],
            severity=body["severity"],
            timestamp=timestamp,
            trace_id=body["trace_id"]
        )
        session.add(event)
        session.commit()
        return NoContent, 201

    except Exception as e:
        session.rollback()
        logger.error(f"Error adding flooding event: {str(e)}")
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    create_tables()
    setup_kafka_thread()
    app.run(port=8080, host="0.0.0.0")

