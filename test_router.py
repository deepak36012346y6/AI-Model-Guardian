from models.router import DemoModel, ModelRouter

# Model A will fail
primary = DemoModel("Model A", should_fail=True)

# Model B will work
backup = DemoModel("Model B", should_fail=False)

router = ModelRouter(primary, backup)

result = router.generate("Explain artificial intelligence")

print("\nFinal Result:")
print(result)

assert result["model"] == "Model B"
assert result["fallback_used"] is True

print("\nSUCCESS: Automatic fallback is working!")