import ast
import json
import os
from jinja2 import Template, Environment, FileSystemLoader
import re
from collections import defaultdict
from bs4 import BeautifulSoup
import google.generativeai as genai
from parser.gemini_client import describe_snippet, model
import json
import time  # 🕰️ For spacing requests

# 🐍 Python parser
def parse_python_file(path, generation_id=None, status=None, flags=None, batch_size=5):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        tree = ast.parse(content)
    attach_parents(tree)

    result = {
        "classes": [],
        "functions": [],
        "control_flows": {
            "if": [], "for": [], "while": [], "try": [], "switch": [], "with": []
        }
    }

    snippets_to_describe = []
    types_to_describe = []
    description_targets = []
    placeholders = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node)
            if not doc:
                snippets_to_describe.append(ast.unparse(node))
                types_to_describe.append("class")
                doc = None
            entry = {"name": node.name, "docstring": doc, "methods": []}
            placeholders.append(("class", entry))
            result["classes"].append(entry)

        elif isinstance(node, ast.FunctionDef):
            doc = ast.get_docstring(node)
            if not doc:
                snippets_to_describe.append(ast.unparse(node))
                types_to_describe.append("function")
                doc = None
            func_info = {
                "name": node.name,
                "params": [arg.arg for arg in node.args.args],
                "docstring": doc,
                "returns": getattr(node.returns, 'id', 'Unknown') if node.returns else "None"
            }
            if isinstance(node.parent, ast.ClassDef):
                for cls in result["classes"]:
                    if cls["name"] == node.parent.name:
                        cls["methods"].append(func_info)
                        break
            else:
                placeholders.append(("function", func_info))
                result["functions"].append(func_info)

        elif isinstance(node, ast.If):
            snippets_to_describe.append(ast.unparse(node))
            types_to_describe.append("if statement")
            result["control_flows"]["if"].append({
                "condition": ast.unparse(node.test),
                "lineno": node.lineno,
                "description": None
            })
            description_targets.append(("if", len(result["control_flows"]["if"]) - 1))

        elif isinstance(node, ast.For):
            snippets_to_describe.append(ast.unparse(node))
            types_to_describe.append("for loop")
            result["control_flows"]["for"].append({
                "condition": f"{ast.unparse(node.target)} in {ast.unparse(node.iter)}",
                "lineno": node.lineno,
                "description": None
            })
            description_targets.append(("for", len(result["control_flows"]["for"]) - 1))

        elif isinstance(node, ast.While):
            snippets_to_describe.append(ast.unparse(node))
            types_to_describe.append("while loop")
            result["control_flows"]["while"].append({
                "condition": ast.unparse(node.test),
                "lineno": node.lineno,
                "description": None
            })
            description_targets.append(("while", len(result["control_flows"]["while"]) - 1))

        elif isinstance(node, ast.Match):
            case_entries = []
            for case in node.cases:
                pattern = "default" if isinstance(case.pattern, ast.MatchAs) and case.pattern.pattern is None else ast.unparse(case.pattern)
                body = "\n".join(ast.unparse(stmt) for stmt in case.body)
                case_entries.append({
                    "pattern": pattern,
                    "statements": body
                })
            result["control_flows"]["switch"].append({
                "condition": ast.unparse(node.subject),
                "lineno": node.lineno,
                "description": f"Match statement with {len(node.cases)} case(s)",
                "cases": case_entries
            })

        elif isinstance(node, ast.Try):
            snippets_to_describe.append(ast.unparse(node))
            types_to_describe.append("try block")
            handlers = [h.name or "Exception" for h in node.handlers]
            result["control_flows"]["try"].append({
                "condition": ", ".join(handlers),
                "lineno": node.lineno,
                "description": None
            })
            description_targets.append(("try", len(result["control_flows"]["try"]) - 1))

    # 🌟 Describe in safe spaced-out batches
    if snippets_to_describe:
        descriptions = []
        cooldown = 5
        total = len(snippets_to_describe)

        for i in range(0, total, batch_size):
            batch_snippets = snippets_to_describe[i:i + batch_size]
            batch_types = types_to_describe[i:i + batch_size]

            try:
                batch_result = describe_snippet(batch_snippets, batch_types, generation_id=generation_id, status=status, flags=flags)
            except Exception as e:
                print(f"💥 Gemini failed on batch {i}: {e}")
                batch_result = ["Failed to generate description"] * len(batch_snippets)

            descriptions.extend(batch_result)

            # 🌸 Update progress
            completed = min(i + batch_size, total)
            progress = int((completed / total) * 100)
            status[generation_id] = f"generating:{progress}"
            
            # 🛑 Check for cancellation right here!
            if flags and flags.get(generation_id) == "cancelled":
                status[generation_id] = "cancelled"
                print(f"🛑 Generation {generation_id} was cancelled.")
                return {"cancelled": True}

            if completed < total:
                time.sleep(cooldown)

        # 🌼 Slice and fill
        placeholder_len = len(placeholders)
        placeholder_descriptions = descriptions[:placeholder_len]
        control_descriptions = descriptions[placeholder_len:]

        for (_, entry), desc in zip(placeholders, placeholder_descriptions):
            entry["docstring"] = desc

        for (section, index), desc in zip(description_targets, control_descriptions):
            result["control_flows"][section][index]["description"] = desc

    cache_path = path + ".docjson"
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result

def attach_parents(node, parent=None):
    for child in ast.iter_child_nodes(node):
        child.parent = parent
        attach_parents(child, child)

def js_parser(path, generation_id=None, status=None, flags=None, batch_size=5):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 🧠 Collect AI targets
    snippets_to_describe = []
    types_to_describe = []
    placeholders = []

    # 📦 Classes
    class_matches = re.findall(r'class\s+(\w+)\s*{(.*?)}', content, re.DOTALL)
    classes = []
    for cls_name, cls_body in class_matches:
        method_matches = re.findall(r'(\w+)\s*\(([^)]*)\)\s*{', cls_body)
        methods = []
        for method_name, params in method_matches:
            param_list = [p.strip() for p in params.split(",") if p.strip()]
            methods.append({
                "name": method_name,
                "params": param_list,
                "docstring": None,
                "returns": "Unknown"
            })
        class_entry = {
            "name": cls_name,
            "docstring": None,
            "methods": methods
        }
        classes.append(class_entry)
        snippets_to_describe.append(f"class {cls_name} {{\n{cls_body}\n}}")
        types_to_describe.append("class")
        placeholders.append(("class", class_entry))

    # 🌐 Global functions
    functions = re.findall(r'function\s+(\w+)\s*\(([^)]*)\)', content)
    function_list = []
    seen_names = set()
    for name, params in functions:
        if name in seen_names:
            continue
        param_list = [p.strip() for p in params.split(",") if p.strip()]
        fn_entry = {
            "name": name,
            "params": param_list,
            "docstring": None,
            "returns": "Unknown"
        }
        function_list.append(fn_entry)
        seen_names.add(name)

        snippets_to_describe.append(f"function {name}({params}) {{ ... }}")
        types_to_describe.append("function")
        placeholders.append(("function", fn_entry))

    # 🔄 Control Flow Statements
    control_flows = { "if": [], "for": [], "while": [], "switch": [], "try": [] }
    description_targets = []

    for match in re.finditer(r'\bif\s*\(', content):
        start = match.end() - 1
        condition = extract_condition_block(content, start)
        lineno = content[:match.start()].count('\n') + 1
        control_flows["if"].append({
            "condition": condition,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append(f"if ({condition}) {{ ... }}")
        types_to_describe.append("if statement")
        description_targets.append(("if", len(control_flows["if"]) - 1))

    for match in re.finditer(r'\bfor\s*\(', content):
        start = match.end() - 1
        condition = extract_condition_block(content, start)
        lineno = content[:match.start()].count('\n') + 1
        control_flows["for"].append({
            "condition": condition,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append("for(" + condition + ")")
        types_to_describe.append("for loop")
        description_targets.append(("for", len(control_flows["for"]) - 1))

    for match in re.finditer(r'\bwhile\s*\(', content):
        start = match.end() - 1
        condition = extract_condition_block(content, start)
        lineno = content[:match.start()].count('\n') + 1
        control_flows["while"].append({
            "condition": condition,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append("while(" + condition + ")")
        types_to_describe.append("while loop")
        description_targets.append(("while", len(control_flows["while"]) - 1))

    switch_pattern = re.compile(r'\bswitch\s*\((.*?)\)\s*{(.*?)}', re.DOTALL)
    for match in switch_pattern.finditer(content):
        condition = match.group(1).strip()
        body = match.group(2)
        case_entries = []
        case_pattern = re.compile(r'(case\s+.*?:|default\s*:)(.*?)(?=case\s+|default\s*:|$)', re.DOTALL)
        for case_match in case_pattern.finditer(body):
            case_label = case_match.group(1).strip().rstrip(":")
            case_body = case_match.group(2).strip()
            case_entries.append({
                "pattern": case_label,
                "statements": case_body
            })

        lineno = content[:match.start()].count('\n') + 1
        control_flows["switch"].append({
            "condition": condition,
            "lineno": lineno,
            "description": f"Switch statement with {len(case_entries)} case(s)",
            "cases": case_entries
        })

    for match in re.finditer(r'\btry\s*{', content):
        lineno = content[:match.start()].count('\n') + 1
        catch_match = re.search(r'catch\s*\(\s*(\w+)\s*\)', content[match.end():])
        caught_error = catch_match.group(1) if catch_match else "Unknown"
        control_flows["try"].append({
            "condition": caught_error,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append("try { ... } catch(" + caught_error + ")")
        types_to_describe.append("try block")
        description_targets.append(("try", len(control_flows["try"]) - 1))

    # ✨ Ask Gemini in batches with cooldown and progress
    if snippets_to_describe:
        descriptions = []
        cooldown = 5
        total = len(snippets_to_describe)

        for i in range(0, total, batch_size):
            batch_snippets = snippets_to_describe[i:i + batch_size]
            batch_types = types_to_describe[i:i + batch_size]

            try:
                batch_result = describe_snippet(batch_snippets, batch_types, generation_id=generation_id, status=status, flags=flags)
            except Exception as e:
                print(f"💥 Gemini failed on batch {i}: {e}")
                batch_result = ["Failed to generate description"] * len(batch_snippets)

            descriptions.extend(batch_result)

            completed = min(i + batch_size, total)
            progress = int((completed / total) * 100)
            status[generation_id] = f"generating:{progress}"
            
            # 🛑 Check for cancellation right here!
            if flags and flags.get(generation_id) == "cancelled":
                status[generation_id] = "cancelled"
                print(f"🛑 Generation {generation_id} was cancelled.")
                return {"cancelled": True}

            if completed < total:
                time.sleep(cooldown)

        # 🌟 Slice responses
        placeholder_len = len(placeholders)
        placeholder_descriptions = descriptions[:placeholder_len]
        control_descriptions = descriptions[placeholder_len:]

        # 📚 Fill docstrings for functions and classes
        for (_, entry), desc in zip(placeholders, placeholder_descriptions):
            entry["docstring"] = desc

        # 🔮 Fill control flow descriptions
        for (section, index), desc in zip(description_targets, control_descriptions):
            control_flows[section][index]["description"] = desc

    # 🗂️ Cache output
    result = {
        "classes": classes,
        "functions": function_list,
        "control_flows": control_flows
    }

    with open(path + ".docjson", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result
    
def extract_condition_block(content, start_index):
    parens = 0
    condition = ""
    for i in range(start_index, len(content)):
        char = content[i]
        if char == '(':
            parens += 1
        elif char == ')':
            parens -= 1
        condition += char
        if parens == 0:
            break
    return condition.strip('()')

def java_parser(path, generation_id=None, status=None, flags=None, batch_size=5):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    snippets_to_describe = []
    types_to_describe = []
    placeholders = []
    description_targets = []

    # 📦 Classes
    class_matches = re.findall(r'\bclass\s+(\w+)\s*{(.*?)}', content, re.DOTALL)
    classes = []
    for cls_name, cls_body in class_matches:
        method_matches = re.findall(r'(?:public|private|protected)?\s*(?:static\s+)?(?:[\w<>\[\]]+\s+)+(\w+)\s*\(([^)]*)\)\s*{', cls_body)
        methods = []
        for method_name, params in method_matches:
            param_list = [p.strip() for p in params.split(",") if p.strip()]
            methods.append({
                "name": method_name,
                "params": param_list,
                "docstring": None,
                "returns": "Unknown"
            })

        entry = {
            "name": cls_name,
            "docstring": None,
            "methods": methods
        }
        classes.append(entry)
        snippets_to_describe.append(f"class {cls_name} {{ {cls_body} }}")
        types_to_describe.append("class")
        placeholders.append(("class", entry))

    # 🌐 Global functions – Java typically doesn't have them
    function_list = []

    # 🔄 Control Flow Statements
    control_flows = {
        "if": [], "for": [], "while": [], "switch": [], "try": []
    }

    # If
    for match in re.finditer(r'\bif\s*\(', content):
        start = match.end() - 1
        condition = extract_condition_block(content, start)
        lineno = content[:match.start()].count('\n') + 1
        control_flows["if"].append({
            "condition": condition,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append("if(" + condition + ") { ... }")
        types_to_describe.append("if statement")
        description_targets.append(("if", len(control_flows["if"]) - 1))

    # For
    for match in re.finditer(r'\bfor\s*\(', content):
        start = match.end() - 1
        condition = extract_condition_block(content, start)
        lineno = content[:match.start()].count('\n') + 1
        control_flows["for"].append({
            "condition": condition,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append("for(" + condition + ") { ... }")
        types_to_describe.append("for loop")
        description_targets.append(("for", len(control_flows["for"]) - 1))

    # While
    for match in re.finditer(r'\bwhile\s*\(', content):
        start = match.end() - 1
        condition = extract_condition_block(content, start)
        lineno = content[:match.start()].count('\n') + 1
        control_flows["while"].append({
            "condition": condition,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append("while(" + condition + ") { ... }")
        types_to_describe.append("while loop")
        description_targets.append(("while", len(control_flows["while"]) - 1))

    # Switch
    switch_pattern = re.compile(r'\bswitch\s*\((.*?)\)\s*{(.*?)}', re.DOTALL)
    for match in switch_pattern.finditer(content):
        condition = match.group(1).strip()
        body = match.group(2)

        case_entries = []
        case_pattern = re.compile(r'(case\s+.*?:|default\s*:)(.*?)(?=case\s+|default\s*:|$)', re.DOTALL)
        for case_match in case_pattern.finditer(body):
            case_label = case_match.group(1).strip().rstrip(":")
            case_body = case_match.group(2).strip()
            case_entries.append({
                "pattern": case_label,
                "statements": case_body
            })

        lineno = content[:match.start()].count('\n') + 1
        control_flows["switch"].append({
            "condition": condition,
            "lineno": lineno,
            "description": f"Switch statement with {len(case_entries)} case(s)",
            "cases": case_entries
        })

    # Try-Catch
    for match in re.finditer(r'\btry\s*{', content):
        lineno = content[:match.start()].count('\n') + 1
        catch_match = re.search(r'catch\s*\(\s*\w+\s+(\w+)\s*\)', content[match.end():])
        caught_error = catch_match.group(1) if catch_match else "Unknown"
        control_flows["try"].append({
            "condition": caught_error,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append("try { ... } catch(" + caught_error + ")")
        types_to_describe.append("try block")
        description_targets.append(("try", len(control_flows["try"]) - 1))

    # ✨ Ask Gemini in batches with progress
    if snippets_to_describe:
        descriptions = []
        cooldown = 5
        total = len(snippets_to_describe)

        for i in range(0, total, batch_size):
            batch_snippets = snippets_to_describe[i:i + batch_size]
            batch_types = types_to_describe[i:i + batch_size]

            try:
                batch_result = describe_snippet(batch_snippets, batch_types, generation_id=generation_id, status=status, flags=flags)
            except Exception as e:
                print(f"💥 Gemini failed on batch {i}: {e}")
                batch_result = ["Failed to generate description"] * len(batch_snippets)

            descriptions.extend(batch_result)

            completed = min(i + batch_size, total)
            progress = int((completed / total) * 100)
            status[generation_id] = f"generating:{progress}"
            
            # 🛑 Check for cancellation right here!
            if flags and flags.get(generation_id) == "cancelled":
                status[generation_id] = "cancelled"
                print(f"🛑 Generation {generation_id} was cancelled.")
                return {"cancelled": True}

            if completed < total:
                time.sleep(cooldown)

        # 🧠 Split responses for placeholders and control flow
        placeholder_len = len(placeholders)
        placeholder_descriptions = descriptions[:placeholder_len]
        control_descriptions = descriptions[placeholder_len:]

        # 🪄 Assign docstrings to classes
        for (_, entry), desc in zip(placeholders, placeholder_descriptions):
            entry["docstring"] = desc

        # 🔮 Assign descriptions to control flows
        for (section, index), desc in zip(description_targets, control_descriptions):
            control_flows[section][index]["description"] = desc

    result = {
        "classes": classes,
        "functions": function_list,
        "control_flows": control_flows
    }

    with open(path + ".docjson", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result
    
def extract_condition_block(text, start_pos):
    """Extracts a condition from a starting '(' position, handling nested parentheses."""
    count = 0
    end_pos = start_pos
    for i in range(start_pos, len(text)):
        if text[i] == '(':
            count += 1
        elif text[i] == ')':
            count -= 1
            if count == 0:
                end_pos = i
                break
    return text[start_pos + 1:end_pos].strip()

def extract_brace_block(text, start_index):
    """Extracts text within matching braces from start_index (which should be '{')"""
    if text[start_index] != '{':
        return None, -1
    stack = 1
    i = start_index + 1
    while i < len(text) and stack > 0:
        if text[i] == '{':
            stack += 1
        elif text[i] == '}':
            stack -= 1
        i += 1
    return text[start_index:i], i  # block text, next index
    
def cpp_parser(path, generation_id=None, status=None, flags=None, batch_size=5):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    snippets_to_describe = []
    types_to_describe = []
    description_targets = []
    placeholders = []

    # 📦 Classes
    class_matches = re.findall(r'\bclass\s+(\w+)\s*{(.*?)};', content, re.DOTALL)
    classes = []
    for cls_name, cls_body in class_matches:
        method_matches = re.findall(
            r'(?:public|private|protected)?\s*(?:static\s+)?(?:[\w:<>\[\]]+\s+)+(\w+)\s*\(([^)]*)\)\s*{', cls_body)
        methods = []
        for method_name, params in method_matches:
            param_list = [p.strip() for p in params.split(",") if p.strip()]
            methods.append({
                "name": method_name,
                "params": param_list,
                "docstring": None,
                "returns": "Unknown"
            })

        entry = {
            "name": cls_name,
            "docstring": None,
            "methods": methods
        }
        classes.append(entry)
        snippets_to_describe.append(f"class {cls_name} {{ {cls_body} }}")
        types_to_describe.append("class")
        placeholders.append(("class", entry))

    # 🌐 Global Functions
    function_list = []
    seen_names = set()
    func_matches = re.finditer(r'(?:[\w:<>\[\]]+\s+)+(\w+)\s*\(([^)]*)\)\s*{', content)

    for match in func_matches:
        name = match.group(1)
        params = match.group(2)

        if name in seen_names:
            continue

        param_list = [p.strip() for p in params.split(",") if p.strip()]
        entry = {
            "name": name,
            "params": param_list,
            "docstring": None,
            "returns": "Unknown"
        }

        function_list.append(entry)
        snippets_to_describe.append(f"{name}({', '.join(param_list)}) {{ ... }}")
        types_to_describe.append("function")
        placeholders.append(("function", entry))
        seen_names.add(name)

    # 🔄 Control Flows
    control_flows = {
        "if": [],
        "for": [],
        "while": [],
        "switch": [],
        "try": []
    }

    def extract_condition_block(content, start_index):
        open_parens = 0
        condition = ""
        i = start_index
        while i < len(content):
            ch = content[i]
            condition += ch
            if ch == '(':
                open_parens += 1
            elif ch == ')':
                open_parens -= 1
                if open_parens == 0:
                    break
            i += 1
        return condition.strip("()")

    for match in re.finditer(r'\bif\s*\(', content):
        start = match.end() - 1
        condition = extract_condition_block(content, start)
        lineno = content[:match.start()].count('\n') + 1
        control_flows["if"].append({
            "condition": condition,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append(f"if ({condition}) {{ ... }}")
        types_to_describe.append("if statement")
        description_targets.append(("if", len(control_flows["if"]) - 1))

    for match in re.finditer(r'\bfor\s*\((.*?)\)', content):
        condition = match.group(1)
        lineno = content[:match.start()].count('\n') + 1
        control_flows["for"].append({
            "condition": condition,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append(f"for ({condition}) {{ ... }}")
        types_to_describe.append("for loop")
        description_targets.append(("for", len(control_flows["for"]) - 1))

    for match in re.finditer(r'\bwhile\s*\(', content):
        start = match.end() - 1
        condition = extract_condition_block(content, start)
        lineno = content[:match.start()].count('\n') + 1
        control_flows["while"].append({
            "condition": condition,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append(f"while ({condition}) {{ ... }}")
        types_to_describe.append("while loop")
        description_targets.append(("while", len(control_flows["while"]) - 1))

    # Switch
    switch_pattern = re.compile(r'\bswitch\s*\((.*?)\)\s*{(.*?)}', re.DOTALL)
    for match in switch_pattern.finditer(content):
        condition = match.group(1).strip()
        body = match.group(2)

        case_entries = []
        case_pattern = re.compile(r'(case\s+.*?:|default\s*:)(.*?)(?=case\s+.*?:|default\s*:|$)', re.DOTALL)
        for case_match in case_pattern.finditer(body):
            case_label = case_match.group(1).strip().rstrip(":")
            case_body = case_match.group(2).strip()
            case_entries.append({
                "pattern": case_label,
                "statements": case_body
            })

        lineno = content[:match.start()].count('\n') + 1
        control_flows["switch"].append({
            "condition": condition,
            "lineno": lineno,
            "description": f"Switch statement with {len(case_entries)} case(s)",
            "cases": case_entries
        })

    # Try-Catch
    for match in re.finditer(r'\btry\s*{', content):
        try_start = match.end() - 1
        lineno = content[:match.start()].count('\n') + 1

        def extract_brace_block(content, start_index):
            open_braces = 0
            i = start_index
            while i < len(content):
                if content[i] == '{':
                    open_braces += 1
                elif content[i] == '}':
                    open_braces -= 1
                    if open_braces == 0:
                        break
                i += 1
            return content[start_index:i+1], i+1

        _, next_index = extract_brace_block(content, try_start)

        catch_match = re.search(
            r'catch\s*\(\s*(?:const\s+)?[\w:<>]+(?:\s*&)?\s+(\w+)\s*\)',
            content[next_index:]
        )

        caught_error = catch_match.group(1) if catch_match else "Unknown"
        control_flows["try"].append({
            "condition": caught_error,
            "lineno": lineno,
            "description": None
        })
        snippets_to_describe.append(f"try {{ ... }} catch({caught_error}) {{ ... }}")
        types_to_describe.append("try block")
        description_targets.append(("try", len(control_flows["try"]) - 1))

    # 🔮 Fetch descriptions in spaced-out batches
    if snippets_to_describe:
        descriptions = []
        cooldown = 5
        total = len(snippets_to_describe)

        for i in range(0, total, batch_size):
            batch_snippets = snippets_to_describe[i:i + batch_size]
            batch_types = types_to_describe[i:i + batch_size]

            try:
                batch_result = describe_snippet(batch_snippets, batch_types, generation_id=generation_id, status=status, flags=flags)
            except Exception as e:
                print(f"💥 Gemini failed on batch {i}: {e}")
                batch_result = ["Failed to generate description"] * len(batch_snippets)

            descriptions.extend(batch_result)

            # 🌟 Update progress
            completed = min(i + batch_size, total)
            progress = int((completed / total) * 100)
            status[generation_id] = f"generating:{progress}"

            # 🛑 Check for cancellation right here!
            if flags and flags.get(generation_id) == "cancelled":
                status[generation_id] = "cancelled"
                print(f"🛑 Generation {generation_id} was cancelled.")
                return {"cancelled": True}

            if completed < total:
                time.sleep(cooldown)

        # 🌟 Split AI responses
        placeholder_len = len(placeholders)
        placeholder_descriptions = descriptions[:placeholder_len]
        control_descriptions = descriptions[placeholder_len:]

        # 🧠 Apply descriptions to placeholders
        for (_, entry), desc in zip(placeholders, placeholder_descriptions):
            entry["docstring"] = desc

        # 🌩️ Apply control flow descriptions
        for (section, index), desc in zip(description_targets, control_descriptions):
            control_flows[section][index]["description"] = desc

    result = {
        "classes": classes,
        "functions": function_list,
        "control_flows": control_flows
    }

    with open(path + ".docjson", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result

def html_parser(path, generation_id=None, status=None, flags=None, batch_size=5):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")
    tag_data = defaultdict(list)
    target_tags = ["div", "p", "a", "ul", "li", "img", "section", "script", "link"]

    snippets_to_describe = []
    types_to_describe = []
    description_targets = []

    for tag in soup.find_all(target_tags):
        tag_str = str(tag)
        tag_name = tag.name
        lineno = content[:content.find(tag_str)].count('\n') + 1

        tag_id = tag.get("id", "")
        tag_class = " ".join(tag.get("class", []))

        other_attrs = []
        for attr, val in tag.attrs.items():
            if attr not in ["id", "class"]:
                val_str = val if isinstance(val, str) else " ".join(val)
                other_attrs.append(f'{attr}="{val_str}"')

        attr_string = " ".join(other_attrs) if other_attrs else "—"

        tag_data[tag_name].append({
            "lineno": lineno,
            "id": tag_id,
            "class": tag_class,
            "attrs": attr_string,
            "description": None
        })

        snippets_to_describe.append(tag_str)
        types_to_describe.append("HTML tag")
        description_targets.append((tag_name, len(tag_data[tag_name]) - 1))

    # 🌟 Describe in safe spaced-out batches
    if snippets_to_describe:
        descriptions = []
        cooldown = 5
        total = len(snippets_to_describe)

        for i in range(0, len(snippets_to_describe), batch_size):
            batch_snippets = snippets_to_describe[i:i + batch_size]
            batch_types = types_to_describe[i:i + batch_size]

            try:
                batch_result = describe_snippet(batch_snippets, batch_types, generation_id=generation_id, status=status, flags=flags)
            except Exception as e:
                print(f"💥 Gemini failed on batch {i}: {e}")
                batch_result = ["Failed to generate description"] * len(batch_snippets)

            # Fix potential "invalid syntax" junk responses
            for j, desc in enumerate(batch_result):
                if isinstance(desc, str) and "invalid syntax" in desc.lower():
                    batch_result[j] = "Could not generate a valid description for this tag."

            descriptions.extend(batch_result)
            
            # After batch_result:
            completed = min(i + batch_size, total)
            progress = int((completed / total) * 100)
            status[generation_id] = f"generating:{progress}"
            
            # 🛑 Check for cancellation right here!
            if flags and flags.get(generation_id) == "cancelled":
                status[generation_id] = "cancelled"
                print(f"🛑 Generation {generation_id} was cancelled.")
                return {"cancelled": True}

            # 💤 Respect Gemini's cooldown if needed
            if i + batch_size < len(snippets_to_describe):
                time.sleep(cooldown)

        for (tag_name, index), desc in zip(description_targets, descriptions):
            tag_data[tag_name][index]["description"] = desc

    result = {
        "html_tags": tag_data
    }

    with open(path + ".docjson", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result

def css_parser(path, generation_id=None, status=None, flags=None, batch_size=5):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    class_rules = []
    id_rules = []
    tag_rules = []
    media_rules = []

    snippets_to_describe = []
    types_to_describe = []
    description_targets = []
    all_rules_flat = []

    media_pattern = re.compile(r'@media\s*([^{]+)\{([\s\S]+?\})\s*\}', re.MULTILINE)
    rule_pattern = re.compile(r'([^{]+)\s*{([^}]*)}', re.MULTILINE)

    # 🌀 Parse @media queries
    for match in media_pattern.finditer(content):
        full_match = match.group(0)
        condition = match.group(1).strip()
        body = match.group(2).strip()
        lineno = content[:match.start()].count('\n') + 1

        nested_elements = []
        for sel, props in rule_pattern.findall(body):
            sel = sel.strip()
            props = props.strip()
            prop_lines = [line.strip() + ";" for line in props.split(";") if line.strip()]
            nested_elements.append({
                "selector": sel,
                "properties": prop_lines
            })

        rule = {
            "selector": f"@media {condition}",
            "lineno": lineno,
            "name": None,
            "description": None,
            "size": condition,
            "elements": nested_elements  # A list of dicts
        }

        media_rules.append(rule)
        snippets_to_describe.append(full_match)
        types_to_describe.append("CSS media query")
        description_targets.append(len(all_rules_flat))
        all_rules_flat.append(rule)

    # 🌟 Parse non-media CSS rules
    non_media_content = media_pattern.sub('', content)
    for match in rule_pattern.finditer(non_media_content):
        selector = match.group(1).strip()
        body = match.group(2).strip()
        lineno = content[:match.start()].count('\n') + 1

        elements = [line.strip() + ";" for line in body.split(";") if line.strip()]

        rule = {
            "selector": selector,
            "lineno": lineno,
            "name": selector[1:] if selector.startswith((".", "#")) else selector,
            "description": None,
            "elements": elements
        }

        if selector.startswith("."):
            class_rules.append(rule)
        elif selector.startswith("#"):
            id_rules.append(rule)
        else:
            tag_rules.append(rule)

        snippets_to_describe.append(f"{selector} {{ {body} }}")
        types_to_describe.append("CSS rule")
        description_targets.append(len(all_rules_flat))
        all_rules_flat.append(rule)

    # ✨ Describe in batches
    if snippets_to_describe:
        descriptions = []
        cooldown = 5
        total = len(snippets_to_describe)

        for i in range(0, total, batch_size):
            batch_snippets = snippets_to_describe[i:i + batch_size]
            batch_types = types_to_describe[i:i + batch_size]

            try:
                batch_result = describe_snippet(batch_snippets, batch_types, generation_id=generation_id, status=status, flags=flags)
            except Exception as e:
                print(f"💥 Gemini failed on batch {i}: {e}")
                batch_result = ["Failed to generate description"] * len(batch_snippets)

            for j, desc in enumerate(batch_result):
                if isinstance(desc, str) and "invalid syntax" in desc.lower():
                    batch_result[j] = "Could not generate a valid description."

            descriptions.extend(batch_result)

            completed = min(i + batch_size, total)
            if status is not None and generation_id is not None:
                status[generation_id] = f"generating:{int((completed / total) * 100)}"
                
            # 🛑 Check for cancellation right here!
            if flags and flags.get(generation_id) == "cancelled":
                status[generation_id] = "cancelled"
                print(f"🛑 Generation {generation_id} was cancelled.")
                return {"cancelled": True}

            if i + batch_size < total:
                time.sleep(cooldown)

        for index, desc in zip(description_targets, descriptions):
            all_rules_flat[index]["description"] = desc

    # 🎁 Final grouped result
    result = {
        "classes": class_rules,
        "ids": id_rules,
        "tags": tag_rules,
        "media": media_rules
    }

    with open(path + ".docjson", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result

def parse_file_by_type(file_path, generation_id=None, status=None, flags=None, batch_size=5):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".py":
        return parse_python_file(file_path, generation_id=generation_id, status=status, flags=flags, batch_size=batch_size)
    elif ext == ".java":
        return java_parser(file_path, generation_id=generation_id, status=status, flags=flags, batch_size=batch_size)
    elif ext == ".cpp":
        return cpp_parser(file_path, generation_id=generation_id, status=status, flags=flags, batch_size=batch_size)
    elif ext == ".js":
        return js_parser(file_path, generation_id=generation_id, status=status, flags=flags, batch_size=batch_size)
    elif ext in [".html", ".htm"]:
        return html_parser(file_path, generation_id=generation_id, status=status, flags=flags, batch_size=batch_size)
    elif ext == ".css":
        return css_parser(file_path, generation_id=generation_id, status=status, flags=flags, batch_size=batch_size)
    else:
        return None

def remove_comments(text):
    if not isinstance(text, str):
        return text

    # Remove all block comments
    cleaned = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    # Split into parts if it's a list of statements (e.g., CSS properties)
    parts = [p.strip() for p in cleaned.split(';') if p.strip()]  # removes empty parts

    # Rejoin only the valid non-empty parts with semicolons
    return '; '.join(parts)

def generate_html(parsed_data, output_path, hide_buttons=False):
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
    env = Environment(loader=FileSystemLoader(template_path))
    template = env.get_template("doc_template.html")

    # Check if we're dealing with HTML tags only
    is_html = any("html_tags" in data for _, data, _ in parsed_data)
    # Check if we're dealing with HTML tags only
    is_css = all("classes" in data and "ids" in data and "media" in data for _, data, _ in parsed_data)

    if is_html:
        # 🧚 Handle HTML-specific rendering
        tag_data = defaultdict(list)
        for filename, data, ext in parsed_data:
            for tag, entries in data.get("html_tags", {}).items():
                tag_data[tag].extend(entries)

        tabs = sorted(tag_data.keys())  # Tab names are tag names like div, p, etc.
        # Just take the first file for now since you're assuming single upload
        filename = parsed_data[0][0] if parsed_data else ""
        ext = parsed_data[0][2] if parsed_data else ""

        clean_ext = ext.lstrip(".").upper()
        rendered = template.render(html_mode=True, css_mode=False, tag_data=tag_data, tabs=tabs, filename=filename, ext=clean_ext)

    elif is_css:
        grouped_data = {
            "Classes": [],
            "IDs": [],
            "Media Queries": []
        }

        for filename, data, ext in parsed_data:
            grouped_data["Classes"].extend(data.get("classes", []))
            grouped_data["IDs"].extend(data.get("ids", []))
            grouped_data["Media Queries"].extend(data.get("media", []))
            
        for group_name, group in grouped_data.items():
            for item in group:
                if "selector" in item:
                    item["selector"] = remove_comments(item["selector"])
                if "name" in item and item["name"]:
                    item["name"] = remove_comments(item["name"])
                if "description" in item:
                    item["description"] = remove_comments(item["description"])
                if "elements" in item:
                    # Media Queries have nested element dictionaries
                    if group_name == "Media Queries" and isinstance(item["elements"], list):
                        for sub_item in item["elements"]:
                            if isinstance(sub_item, dict) and "properties" in sub_item:
                                sub_item["properties"] = [
                                    p_cleaned for p_cleaned in (remove_comments(p) for p in sub_item["properties"])
                                    if p_cleaned and p_cleaned.strip()
                                ]
                    else:
                        if isinstance(item["elements"], list):
                            item["elements"] = [
                                el_cleaned for el_cleaned in (remove_comments(el) for el in item["elements"])
                                if el_cleaned and el_cleaned.strip()
                        ]

        tabs = list(grouped_data.keys())  # "Classes", "IDs", "Media Queries"
        filename = parsed_data[0][0] if parsed_data else ""
        ext = parsed_data[0][2] if parsed_data else ""
        extFullForm = ext.lstrip(".").upper()

        rendered = template.render(
            css_mode=True,
            grouped_data=grouped_data,
            tabs=tabs,
            html_mode=False,
            filename=filename,
            ext=extFullForm,
            ext_raw=ext,
            hide_buttons=hide_buttons
        )
    
    else:
        # 🧑‍💻 Handle regular code parsing
        control_keywords = []
        control_flows = {}

        for filename, data, ext in parsed_data:
            if "control_flows" in data:
                for keyword, entries in data["control_flows"].items():
                    if keyword in ["with",]:
                        continue
                    if keyword not in control_flows:
                        control_flows[keyword] = []
                    control_flows[keyword].extend(entries)

        if control_flows:
            control_keywords = sorted(control_flows.keys())
        
        filename = parsed_data[0][0] if parsed_data else ""    
        ext = parsed_data[0][2] if parsed_data else ""  # 💡 Ensure ext is safely set

        all_tabs = ["Classes", "Functions"] + [kw.capitalize() for kw in control_keywords]

        all_data = {
            "classes": [],
            "functions": [],
            "control_flows": control_flows
        }

        for filename, data, ext in parsed_data:
            all_data["classes"].extend(data.get("classes", []))
            all_data["functions"].extend(data.get("functions", []))

        ext_map = {
            ".html": "HTML",
            ".py": "Python",
            ".java": "Java",
            ".cpp": "C++",
            ".js": "JavaScript",
            ".css": "CSS"
        }
        extFullForm = ext_map.get(ext, ext.lstrip(".").title())
        rendered = template.render(
            data=all_data,
            tabs=all_tabs,
            html_mode=False,
            css_mode=False,
            filename=filename,
            ext=extFullForm,
            ext_raw=ext,
            hide_buttons=hide_buttons  # 🪄 pass it to the template
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered)
        
