import os

from dotenv import load_dotenv

from models.real_router import RealModelRouter

load_dotenv()


def main():
    if not os.getenv("GEMINI_API_KEY"):
        print("GEMINI_API_KEY is missing from .env.")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is missing from .env.")
        return

    router = RealModelRouter()

    prompt = (
        "Explain an AI model backup system "
        "in two short sentences."
    )

    print("\nAI MODEL GUARDIAN")
    print("-" * 35)
    print("Primary: Gemini")
    print("Backup: OpenAI")
    print("\nSending a real API request...")
    print("Please wait.\n")

    result = router.generate(prompt)

    print("-" * 35)
    print("Provider used:", result["model"])
    print("Backup used:", result["fallback_used"])
    print("\nResponse:")
    print(result["response"])

    if result["error"]:
        print("\nError details:")
        print(result["error"])

    print("-" * 35)


if __name__ == "__main__":
    main()