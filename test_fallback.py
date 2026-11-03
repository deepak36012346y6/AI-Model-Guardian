from models.real_router import RealModelRouter


def main():
    print("=" * 45)
    print(" AI MODEL GUARDIAN - FAILOVER TEST")
    print("=" * 45)

    router = RealModelRouter()

    # Simulate OpenAI without making an API request.
    def simulated_openai(prompt):
        return (
            "[SIMULATED RESPONSE] "
            "The OpenAI backup logic works!"
        )

    # Avoid writing fake successes to production logs.
    def skip_logging(*args, **kwargs):
        pass

    router._call_openai = simulated_openai
    router._log = skip_logging

    print("\nSimulating a Gemini failure...")

    result = router.generate(
        "Explain artificial intelligence.",
        force_gemini_failure=True,
    )

    print("\n--- TEST RESULTS ---")
    print("Provider:", result["model"])
    print("Fallback used:", result["fallback_used"])
    print("Response:", result["response"])

    if (
        result["fallback_used"]
        and result["model"] is not None
        and result["response"].startswith("[SIMULATED RESPONSE]")
    ):
        print("\nSUCCESS: Simulated failover works!")
        print("No OpenAI API request was made.")
    else:
        print("\nTEST FAILED: Check the router logic.")


if __name__ == "__main__":
    main()