from parser import parse_custom_syntax, match_line_to_syntax
from translator import translate_to_python

def run_custom_code_line(line: str, syntax_map: dict, enclosures: dict = {}, settings: dict = {}):
    keyword = extract_first_word(line)
    syntax_string = syntax_map.get(keyword)

    if not syntax_string:
        return {"error": f"❌ No syntax defined for keyword '{keyword}'."}

    # Step 1: Parse the expected syntax structure
    syntax_obj = parse_custom_syntax(syntax_string)

    # Step 2: Match user input against the syntax
    match_result = match_line_to_syntax(line, syntax_obj, enclosures=enclosures, settings=settings)
    if "error" in match_result:
        return {"error": match_result["error"]}

    # Step 3: Translate matched elements into Python
    translation_result = translate_to_python(match_result, syntax_obj)

    return {"success": True, "python_code": translation_result}

def extract_first_word(line: str) -> str:
    return line.strip().split()[0] if line.strip() else ""
