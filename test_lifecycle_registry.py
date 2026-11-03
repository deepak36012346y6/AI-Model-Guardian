from migration.lifecycle_registry import ModelLifecycleRegistry


def main():
    registry = ModelLifecycleRegistry()

    # Add an example model with a hypothetical retirement date.
    model = registry.add_or_update_model(
        provider="Demo Provider",
        model_name="demo-model-v1",
        status="scheduled_for_retirement",
        retirement_date="2026-11-15",
        official_notice="",
        notes="Example data for testing only.",
    )

    print("\nMODEL LIFECYCLE REGISTRY TEST")
    print("-" * 40)

    print("Saved model:")
    print(model)

    print("\nAll registered models:")
    for item in registry.get_all_models():
        print(item)

    print("\nUpcoming retirements within 30 days:")
    upcoming = registry.get_upcoming_retirements(days=30)

    if upcoming:
        for item in upcoming:
            print(
                f"- {item['provider']}: "
                f"{item['model_name']} "
                f"(retirement: {item['retirement_date']})"
            )
    else:
        print("No upcoming retirements found.")

    print("\nTEST COMPLETED")


if __name__ == "__main__":
    main()