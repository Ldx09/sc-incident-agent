import os
import time
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError, APIStatusError

load_dotenv()

MODEL = "gpt-4o-mini"
MAX_RETRIES = 3
RETRY_DELAY = 5


def get_client() -> OpenAI:
    import streamlit as st
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found.")
    return OpenAI(api_key=api_key)


def call_model(system_prompt: str, user_message: str, max_tokens: int = 2048) -> str:
    """
    Core function used by Steps 1, 3, and 4.
    Retries on rate limits, raises clean errors on everything else.
    """
    if not user_message or not user_message.strip():
        raise ValueError("Incident text is empty. Please provide an incident description.")

    client = get_client()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=max_tokens,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ]
            )
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise ValueError("Model returned an empty response. Try again.")
            return content.strip()

        except RateLimitError:
            if attempt < MAX_RETRIES:
                wait = RETRY_DELAY * attempt
                print(f"  Rate limit hit — waiting {wait}s before retry {attempt}/{MAX_RETRIES}...")
                time.sleep(wait)
            else:
                raise RuntimeError(
                    "OpenAI rate limit reached after 3 attempts. "
                    "Wait 60 seconds and try again, or check your usage at platform.openai.com."
                )

        except APIConnectionError:
            raise RuntimeError(
                "Cannot connect to OpenAI. "
                "Check your internet connection and try again."
            )

        except APIStatusError as e:
            if e.status_code == 401:
                raise RuntimeError(
                    "Invalid API key. "
                    "Check your OPENAI_API_KEY in .env — it should start with sk-..."
                )
            elif e.status_code == 429:
                raise RuntimeError(
                    "OpenAI quota exceeded. "
                    "Add credits at platform.openai.com/settings/billing."
                )
            elif e.status_code >= 500:
                if attempt < MAX_RETRIES:
                    print(f"  OpenAI server error — retrying ({attempt}/{MAX_RETRIES})...")
                    time.sleep(RETRY_DELAY)
                else:
                    raise RuntimeError(
                        "OpenAI is experiencing issues. Try again in a few minutes."
                    )
            else:
                raise RuntimeError(f"OpenAI API error {e.status_code}: {e.message}")


def call_model_with_search(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 4096
) -> tuple[str, list[str]]:
    """
    Used by Step 2. Uses enriched prompt to reason deeply from training knowledge.
    Returns (response_text, searches_performed).
    """
    if not user_message or not user_message.strip():
        raise ValueError("Incident text is empty. Please provide an incident description.")

    enriched_system = (
        system_prompt
        + "\n\nIMPORTANT: You do not have live web access. Instead, reason "
        "deeply from your training knowledge. Draw on real companies, real ports, "
        "real trade routes, real historical incidents, and real market data you "
        "know about. Be specific — use actual company names, port names, trade "
        "statistics, and historical precedents. In the 'searches_performed' field "
        "of your JSON, list the exact queries you WOULD have run if you had "
        "web access. Make your analysis as grounded and specific as possible. "
        "If you cannot find strong historical data for a specific company mentioned, "
        "reason from similar companies or industry patterns instead — never return "
        "empty lists when you can provide general industry knowledge."
    )

    text = call_model(enriched_system, user_message, max_tokens)
    searches_performed = ["(deep knowledge reasoning — no live search)"]
    return text, searches_performed


def validate_incident_text(text: str) -> tuple[bool, str]:
    """
    Validates incident input before sending to the pipeline.
    Returns (is_valid, error_message).
    """
    if not text or not text.strip():
        return False, "Please enter an incident description."

    if len(text.strip()) < 50:
        return False, (
            "Incident description is too short (minimum 50 characters). "
            "Include what happened, where, and which suppliers or products are affected."
        )

    if len(text) > 8000:
        return False, (
            "Incident description is too long (maximum 8,000 characters). "
            "Please summarize the key facts."
        )

    supply_chain_keywords = [
        "supplier", "supply", "shipment", "port", "warehouse", "inventory",
        "logistics", "freight", "manufacturer", "production", "delivery",
        "tariff", "component", "parts", "vendor", "procurement", "factory",
        "distribution", "cargo", "import", "export", "disruption", "delay"
    ]
    text_lower = text.lower()
    if not any(kw in text_lower for kw in supply_chain_keywords):
        return False, (
            "This doesn't look like a supply chain incident report. "
            "Include details about suppliers, shipments, inventory, or logistics."
        )

    return True, ""


def test_connection() -> bool:
    print(f"Connecting to OpenAI ({MODEL})...")
    result = call_model(
        system_prompt="You are a helpful assistant. Reply with JSON only.",
        user_message=(
            "Reply with exactly this JSON and nothing else: "
            '{"status": "connected", "project": "SC Incident Response Agent", '
            '"model": "gpt-4o-mini"}'
        ),
        max_tokens=60
    )
    print(f"Response: {result}")
    print("\nConnection successful. OpenAI gpt-4o-mini is active.")
    return True


if __name__ == "__main__":
    test_connection()