import csv
import os
from datetime import date, datetime, timedelta


class ModelLifecycleRegistry:
    """Store and track AI model lifecycle information."""

    FIELDNAMES = [
        "provider",
        "model_name",
        "status",
        "retirement_date",
        "official_notice",
        "last_checked",
        "notes",
    ]

    VALID_STATUSES = {
        "active",
        "deprecated",
        "scheduled_for_retirement",
        "retired",
        "unknown",
    }

    def __init__(self, file_path="logs/model_lifecycle.csv"):
        self.file_path = file_path

        folder = os.path.dirname(self.file_path)

        if folder:
            os.makedirs(folder, exist_ok=True)

        if not os.path.exists(self.file_path):
            with open(
                self.file_path,
                "w",
                newline="",
                encoding="utf-8",
            ) as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=self.FIELDNAMES,
                )
                writer.writeheader()

    def get_all_models(self):
        """Return all models saved in the registry."""

        with open(
            self.file_path,
            "r",
            newline="",
            encoding="utf-8",
        ) as file:
            return list(csv.DictReader(file))

    def add_or_update_model(
        self,
        provider,
        model_name,
        status="unknown",
        retirement_date="",
        official_notice="",
        notes="",
    ):
        """Add a model or update an existing model."""

        provider = provider.strip()
        model_name = model_name.strip()
        status = status.strip().lower()

        if not provider or not model_name:
            raise ValueError(
                "Provider and model name are required."
            )

        if status not in self.VALID_STATUSES:
            raise ValueError(
                f"Invalid status: {status}. "
                f"Choose one of: {sorted(self.VALID_STATUSES)}"
            )

        if retirement_date:
            try:
                date.fromisoformat(retirement_date)
            except ValueError:
                raise ValueError(
                    "Retirement date must use YYYY-MM-DD format."
                )

        models = self.get_all_models()

        updated_model = {
            "provider": provider,
            "model_name": model_name,
            "status": status,
            "retirement_date": retirement_date,
            "official_notice": official_notice,
            "last_checked": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "notes": notes,
        }

        found = False

        for index, model in enumerate(models):
            if (
                model["provider"].lower() == provider.lower()
                and model["model_name"].lower()
                == model_name.lower()
            ):
                models[index] = updated_model
                found = True
                break

        if not found:
            models.append(updated_model)

        with open(
            self.file_path,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=self.FIELDNAMES,
            )
            writer.writeheader()
            writer.writerows(models)

        return updated_model

    def get_upcoming_retirements(self, days=30):
        """Find models scheduled for retirement within a time window."""

        if days < 0:
            raise ValueError("Days cannot be negative.")

        today = date.today()
        deadline = today + timedelta(days=days)

        upcoming = []

        for model in self.get_all_models():
            retirement_date = model["retirement_date"]

            if not retirement_date:
                continue

            try:
                retirement = date.fromisoformat(retirement_date)
            except ValueError:
                continue

            if (
                today <= retirement <= deadline
                and model["status"]
                in {
                    "deprecated",
                    "scheduled_for_retirement",
                }
            ):
                upcoming.append(model)

        return upcoming