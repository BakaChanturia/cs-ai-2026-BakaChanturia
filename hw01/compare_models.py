import os
import time
from dotenv import load_dotenv

load_dotenv()
print("Loaded API key:", os.getenv("GEMINI_API_KEY"))

try:
    import google.genai as genai
except ImportError:
    print("ERROR: google-genai package not installed.")
    print("Run: pip install google-genai")
    exit(1)

MODEL_1 = "gemini-3-flash-preview"
MODEL_2 = "gemini-3.1-flash-lite-preview"

PROMPT = "Generate a recursive Python script for computing the Fibonacci sequence up to the nth term."

PRICE_INPUT_PER_MILLION = 0.10
PRICE_OUTPUT_PER_MILLION = 0.40


def calculate_paid_tier_cost(input_tokens, output_tokens):
    input_cost = (input_tokens / 1_000_000) * PRICE_INPUT_PER_MILLION
    output_cost = (output_tokens / 1_000_000) * PRICE_OUTPUT_PER_MILLION
    return input_cost + output_cost


def call_model(client, model_name, prompt):
    print(f"\n{'=' * 70}")
    print(f"MODEL: {model_name}")
    print(f"{'=' * 70}")

    token_count_result = client.models.count_tokens(
        model=model_name,
        contents=prompt
    )

    print(f"Prompt: {prompt}")
    print(f"Estimated input tokens before call: {token_count_result.total_tokens}")
    print("\nSending request...\n")

    start_time = time.perf_counter()
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    end_time = time.perf_counter()

    latency_ms = (end_time - start_time) * 1000
    usage = response.usage_metadata

    paid_cost = calculate_paid_tier_cost(
        usage.prompt_token_count,
        usage.candidates_token_count
    )

    print("RESPONSE:")
    print("-" * 70)
    print(response.text)
    print("-" * 70)

    print("\nTOKEN USAGE:")
    print(f"  Input tokens:  {usage.prompt_token_count}")
    print(f"  Output tokens: {usage.candidates_token_count}")
    print(f"  Total tokens:  {usage.total_token_count}")

    print("\nLATENCY:")
    print(f"  Total time: {latency_ms:.0f} ms")

    print("\nCOST ESTIMATE:")
    print("  Free tier: $0.00")
    print(f"  Paid tier equivalent: ${paid_cost:.6f}")

    return {
        "model": model_name,
        "response": response.text,
        "input_tokens": usage.prompt_token_count,
        "output_tokens": usage.candidates_token_count,
        "total_tokens": usage.total_token_count,
        "latency_ms": latency_ms,
        "paid_cost": paid_cost,
    }


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment.")
        print("Make sure you have a .env file with: GEMINI_API_KEY=your_key_here")
        exit(1)

    print(f"Connecting to {MODEL_1} and {MODEL_2}...")
    client = genai.Client(api_key=api_key)

    result1 = call_model(client, MODEL_1, PROMPT)
    result2 = call_model(client, MODEL_2, PROMPT)

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(
        f"{'Model':<35} {'Input':>8} {'Output':>8} {'Total':>8} {'Latency':>10} {'Cost':>12}"
    )
    print("-" * 85)
    for result in [result1, result2]:
        print(
            f"{result['model']:<35} "
            f"{result['input_tokens']:>8} "
            f"{result['output_tokens']:>8} "
            f"{result['total_tokens']:>8} "
            f"{result['latency_ms']:>9.0f}ms "
            f"${result['paid_cost']:>10.6f}"
        )


if __name__ == "__main__":
    main()