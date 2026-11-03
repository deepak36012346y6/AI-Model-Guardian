class DemoModel:
    """A simulated AI model for testing."""

    def __init__(self, name, should_fail=False):
        self.name = name
        self.should_fail = should_fail

    def generate(self, prompt):
        if self.should_fail:
            raise RuntimeError(f"{self.name} is unavailable!")

        return f"Response generated successfully by {self.name}."


class ModelRouter:
    """Routes requests between a primary and backup model."""

    def __init__(self, primary, backup):
        self.primary = primary
        self.backup = backup
        self.last_used_model = None

    def generate(self, prompt):
        try:
            response = self.primary.generate(prompt)
            self.last_used_model = self.primary.name

            return {
                "response": response,
                "model": self.primary.name,
                "fallback_used": False,
            }

        except Exception as primary_error:
            print(f"Primary model failed: {primary_error}")
            print("Trying backup model...")

        try:
            response = self.backup.generate(prompt)
            self.last_used_model = self.backup.name

            return {
                "response": response,
                "model": self.backup.name,
                "fallback_used": True,
            }

        except Exception as backup_error:
            self.last_used_model = None

            return {
                "response": (
                    "Both the primary and backup models failed."
                ),
                "model": None,
                "fallback_used": True,
                "error": str(backup_error),
            }