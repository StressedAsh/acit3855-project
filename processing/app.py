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
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

with open("config/processing/app_conf.yml", "r") as file:
    config = yaml.safe_load(file)

DATA_FILE = config["datastore"]["filename"]
SCHEDULER_INTERVAL = config["scheduler"]["interval"]
RAINFALL_URL = config["eventstores"]["RainConditions"]["url"]
FLOODING_URL = config["eventstores"]["floodings"]["url"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

with open("config/processing/log_conf.yml", "r") as f:
    log_config = yaml.safe_load(f)
    logging.config.dictConfig(log_config)
    
logger = logging.getLogger("basicLogger")

app = connexion.FlaskApp(__name__, specification_dir="")
app.add_api("processing_conf.yaml", strict_validation=True, validate_responses=True, base_path="/processing")

def read_stats():
    if not os.path.exists(DATA_FILE):
        logging.warning("Stats file not found. Creating an empty one.")
        default_stats = {
            "num_rain_events": 0,
            "max_rainfall": 0,
            "min_rainfall": 0,
            "avg_rainfall": 0,
            "num_flood_events": 0,
            "max_flood_level": 0,
            "min_flood_level": 0,
            "avg_flood_level": 0,
            "last_updated": "2025-01-01 00:00:00"
        }
        write_stats(default_stats)
        logger.info("Created new stats file.")
        return default_stats

    with open(DATA_FILE, "r") as file:
        return json.load(file)


def write_stats(stats):
    try:
        with open(DATA_FILE, "w") as file:
            json.dump(stats, file, indent=4)
        logging.info(f"Stats successfully written to {DATA_FILE}")
        logger.info(f"Stats successfully written to {DATA_FILE}")
    except Exception as e:
        logging.error(f"Failed to write stats.json: {e}")
        logger.error(f"Failed to write stats.json: {e}")

def fetch_events(event_type):
    stats = read_stats()
    last_updated = stats.get("last_updated")
    print(last_updated)
    start_time = last_updated
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    url = RAINFALL_URL if event_type == "RainConditions" else FLOODING_URL
    
    params = {
        "start_timestamp": start_time,
        "end_timestamp": end_time
    }
    query_string = urllib.parse.urlencode(params)

    logging.info(f"Fetching {event_type} events from {url} with params {query_string}")
    logger.info(f"Fetching {event_type} events from {url} with params {query_string}")

    try:
        response = httpx.get(f"{url}?{query_string}")

        if response.status_code == 200:
            data = response.json()
            logging.info(f"Received {len(data)} {event_type} events.")
            logger.info(f"Received {len(data)} {event_type} events.")
            return data
        else:
            logging.error(f"Failed to fetch {event_type} events. Status: {response.status_code} | Response: {response.text}")
            logger.error(f"Failed to fetch {event_type} events. Status: {response.status_code} | Response: {response.text}")
            return []
    except requests.RequestException as e:
        logging.error(f"Request failed for {event_type}: {e}")
        logger.error(f"Request failed for {event_type}: {e}")
        return []

def populate_stats():
    logging.info("Starting periodic statistics calculation...")

    rain_events = fetch_events("RainConditions")
    flood_events = fetch_events("floodings")

    if not rain_events and not flood_events:
        logging.warning("No new events received. Skipping stats update.")
        logger.warning("No new events received. Skipping stats update.")
        return

    stats = read_stats()
    if rain_events:
        stats["num_rain_events"] += len(rain_events)
        stats["max_rainfall"] = max((event["rainfall_nm"] for event in rain_events), default=stats["max_rainfall"])
        stats["min_rainfall"] = min((event["rainfall_nm"] for event in rain_events), default=stats["min_rainfall"])
        stats["avg_rainfall"] = sum(event["rainfall_nm"] for event in rain_events) / len(rain_events)

    if flood_events:
        stats["num_flood_events"] += len(flood_events)
        stats["max_flood_level"] = max((event["flood_level"] for event in flood_events), default=stats["max_flood_level"])
        stats["min_flood_level"] = min((event["flood_level"] for event in flood_events), default=stats["min_flood_level"])
        stats["avg_flood_level"] = sum(event["flood_level"] for event in flood_events) / len(flood_events)

    stats["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_stats(stats)
    logging.info("Finished periodic statistics calculation.")
    logger.info("Finished periodic statistics calculation.")

def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=SCHEDULER_INTERVAL)
    sched.start()

def get_stats():
    stats = read_stats()
    if stats is None:
        logging.error("Statistics file not found.")
        logger.error("Statistics file not found.")
        return jsonify({"message": "Statistics do not exist"}), 404
    print(stats)
    return jsonify(stats), 200

app.add_middleware(CORSMiddleware,position=MiddlewarePosition.BEFORE_EXCEPTION,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")
