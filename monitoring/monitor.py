import csv
import os
from datetime import datetime, timezone

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "model_logs.csv")

FIELDNAMES = [
    "timestamp",
    "model",
    "response_time_seconds",
    "status",
    "fallback_used",
    "error",
]


def log_request(
    model,
    response_time,
    status,
    fallback_used,
    error=None,
):
    """Save model request details to a CSV file."""

    os.makedirs(LOG_DIR, exist_ok=True)
    file_exists = os.path.exists(LOG_FILE)

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)

        if not file_exists or os.path.getsize(LOG_FILE) == 0:
            writer.writeheader()

        writer.writerow(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": model or "None",
                "response_time_seconds": round(response_time, 4),
                "status": status,
                "fallback_used": fallback_used,
                "error": error or "",
            }
        )


def read_logs():
    """Return all recorded requests."""

    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))