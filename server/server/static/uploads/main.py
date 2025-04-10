from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from lexer import tokenize_code
from parser import parse_code
from database import get_all_languages, save_language
from models import LanguageCreate
from interpreter import interpret
from typing import List, Dict
from syntaxProcessor import run_custom_code_line
import io
import contextlib
import re
import tokenize

app = FastAPI()

# 👇 Allow CORS from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global keyword and datatype maps
keyword_map = {}
datatype_map = {}  # 🆕 Added to track datatype enclosure pairs

# ✅ Python keywords not allowed unless aliased
PYTHON_KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally", "for",
    "from", "global", "if", "import", "in", "is", "lambda", "nonlocal", "not", "or",
    "pass", "raise", "return", "try", "while", "with", "yield", "print"
}

def clean_spaces(text: str) -> str:
    return text.replace('\u00A0', ' ').replace('\xa0', ' ')

def validate_syntax(line, alias_map, syntax_map, enclosures, settings):
    print(f"🔍 Validating line: '{line}'")
    for alias, keyword in alias_map.items():
        if line.startswith(alias):
            print(f"🔁 Checking alias: '{alias}' for keyword: '{keyword}'")
            expected_syntax = syntax_map.get(keyword)
            if not expected_syntax:
                print(f"⚠️ No syntax defined for keyword '{keyword}' — allowing by default.")
                return True

            syntax_parts = expected_syntax.strip().split()
            input_parts = line.strip().split()
            print(f"📐 Expected syntax: {syntax_parts}")
            print(f"🧾 Actual line split: {input_parts}")

            if input_parts[0] != alias:
                print(f"❌ First word '{input_parts[0]}' is not expected keyword '{alias}'")
                return False

            if "parameters" in syntax_parts or "statements" in syntax_parts:
                if len(input_parts) < 2:
                    print("❌ Missing parameters or statements.")
                    return False

                for part in input_parts[1:]:
                    # ✅ Check if the part is properly enclosed
                    matched = False
                    for dtype, wrap in enclosures.items():
                        if part.startswith(wrap["start"]) and part.endswith(wrap["end"]):
                            matched = True
                            break

                    if not matched:
                        print(f"❌ Part '{part}' is not enclosed in any valid wrapper.")
                        return False

                if settings.get("enforce_indentation") and "statements" in syntax_parts:
                    # Let indentation-based formats pass — don't check enclosure
                    print("✅ Indentation-based syntax allowed for statements.")
                else:
                    if "statements" in syntax_parts:
                        print("✅ Statement enclosure validation passed.")
                print("✅ Syntax validated based on enclosures.")
                return True
            else:
                if len(input_parts) != len(syntax_parts):
                    print(f"❌ Mismatch in part count: expected {len(syntax_parts)}, got {len(input_parts)}")
                    return False

                for expected, actual in zip(syntax_parts, input_parts):
                    if expected == "keyword" and actual != alias:
                        print(f"❌ Expected keyword '{alias}' but got '{actual}'")
                        return False
                    elif expected not in ["parameters", "statements"] and expected != actual:
                        print(f"❌ Expected literal '{expected}' but got '{actual}'")
                        return False
                print("✅ Exact match syntax passed.")
                return True

    print("❌ No matching alias found.")
    return False

class TranslateRequest(BaseModel):
    code: str
    alias_map: dict
    syntax_map: dict
    enclosures: dict  # {datatype: {"start": "(", "end": ")"}}
    settings: dict    # {"require_types": True, "enforce_indentation": False}

@app.post("/translate/")
def translate(request: TranslateRequest):
    try:
        alias_map = request.alias_map
        syntax_map = {k: clean_spaces(v) for k, v in request.syntax_map.items()}
        raw_code = clean_spaces(request.code)
        enclosures = request.enclosures
        settings = request.settings

        print("🛠 Received code:\n", raw_code)
        print("🛠 Alias map:", alias_map)
        print("🛠 Syntax map:", syntax_map)
        print("⚙️ Settings:", settings)
        print("📦 Enclosures:", enclosures)

        translated_lines = []

        for line in raw_code.strip().splitlines():
            if not validate_syntax(line.strip(), alias_map, syntax_map, enclosures, settings):
                return {"error": f"❌ Invalid syntax: '{line}' doesn't match your custom language rules."}

            matched = False
            for alias, keyword in alias_map.items():
                if re.match(rf"^{re.escape(alias)}\b", line):
                    matched = True
                    args = re.sub(rf"^{re.escape(alias)}\b", "", line).strip()
                    translated_line = f"{keyword}({args})" if args else f"{keyword}()"
                    translated_lines.append(translated_line)
                    break

            if not matched:
                return {"error": f"⚠️ Unknown keyword in line: '{line}'. Please define an alias before using it."}

        final_code = "\n".join(translated_lines)
        print("🔁 Final Translated Code:\n", final_code)

        exec_env = {}
        with contextlib.redirect_stdout(io.StringIO()) as f:
            exec(final_code, {}, exec_env)
        output = f.getvalue()

        return {"output": output or "✅ Terminal connected successfully!"}

    except Exception as e:
        return {"error": str(e)}

class CodeInput(BaseModel):
    code: str
    syntax_map: dict
    enclosures: dict
    settings: dict

@app.post("/run-custom-code")
def run_custom_code(input: CodeInput):
    result_lines = []
    for line in input.code.splitlines():
        if not line.strip():
            continue
        result = run_custom_code_line(line, input.syntax_map)
        if result.get("success"):
            result_lines.append(result["python_code"])
        else:
            return {"error": result["error"]}
    try:
        exec_globals = {}
        exec("\n".join(result_lines), exec_globals)
    except Exception as e:
        return {"error": str(e)}
    return {"output": "Success", "translated_code": "\n".join(result_lines)}

@app.post("/define-language/")
def define_language(blocks: List[Dict]):
    global keyword_map, datatype_map
    keyword_map = {}
    datatype_map = {}

    used_enclosures = set()

    for block in blocks:
        if block["type"].startswith("custom_"):
            keyword_map[block["keyword"]] = block["type"].replace("custom_", "")
        elif block["type"] == "datatype":
            dtype = block["name"]
            start = block.get("enclosure_start", "")
            end = block.get("enclosure_end", "")

            if (start, end) in used_enclosures:
                if not (dtype in ["char", "string"] and any(
                    d in ["char", "string"] and datatype_map[d]["start"] == start and datatype_map[d]["end"] == end
                    for d in datatype_map
                )):
                    return {"error": f"❌ Enclosure ({start}, {end}) already in use for another datatype."}

            datatype_map[dtype] = {"start": start, "end": end}
            used_enclosures.add((start, end))

    return {"status": "Language defined"}

@app.get("/")
def home():
    return {"message": "Welcome to LangForge!"}

@app.post("/languages/")
def create_language(language: LanguageCreate):
    save_language(language.name, language.grammar)
    return {"message": "Language saved successfully"}

@app.get("/languages/")
def list_languages():
    return {"languages": get_all_languages()}