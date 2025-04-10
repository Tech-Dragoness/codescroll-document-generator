# parser/gemini_client.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.0-flash-lite")

def describe_snippet(snippets: list[str], types: list[str], generation_id=None, status=None, flags=None) -> list[str]:
    prompt_parts = [
        "You will be given a numbered list of code snippets with their type.",
        "Return a Python-style array (list) of simple, one-line descriptions, in the same order.",
        "Do NOT include extra explanation, quotes, markdown, or backticks.",
        "ONLY return the raw array like: [\"desc1\", \"desc2\"]",
        "Here is the list of snippets:\n"
    ]

    for i, (code, typ) in enumerate(zip(snippets, types), 1):
        prompt_parts.append(f"{i}. Type: {typ}\n{code}")

    final_prompt = "\n\n".join(prompt_parts)

    try:
        # 🛡️ Optional cancellation check
        if flags and generation_id and flags.get(generation_id) == "cancelled":
            raise Exception("Generation cancelled")

        # 🌟 Mark status if applicable
        if status and generation_id:
            status[generation_id] = "generating_descriptions"

        response = model.generate_content(final_prompt)
        raw = response.text.strip()

        # 🧼 Remove code block formatting if present
        if raw.startswith("```"):
            raw = raw.strip("` \n")
            if raw.startswith("python\n"):
                raw = raw[7:]

        # 🛡 Try parsing as Python list
        import ast
        parsed = ast.literal_eval(raw)

        # ✅ Must be a list of strings
        if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
            raise ValueError("Output was not a valid list of strings")

        return parsed

    except Exception as e:
        print("💥 Gemini response error:", e)
        return [f"Error: {e}"] * len(snippets)