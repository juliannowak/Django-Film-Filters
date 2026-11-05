#!/usr/bin/env python3
import os
import re
from pathlib import Path


def update_todos_in_readme():
    readme_path = Path("README.md")
    current_dir = Path(".")
    
    # Target marker for our TODO section
    header_marker = "## Automated TODO List"

    # Regex to catch '# todo' or '# TODO' with any surrounding spaces
    todo_pattern = re.compile(r"#\s*TODO\b(.*)", re.IGNORECASE)
    found_todos = []

    # 1. Scan for Python files recursively
    for py_file in current_dir.rglob("*.py"):
        # Skip files inside virtual environments or hidden directories
        if any(part.startswith(".") or part in ["venv", "env", "node_modules"] for part in py_file.parts):
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    match = todo_pattern.search(line)
                    if match:
                        todo_text = match.group(1).strip()
                        # Clean up any leading colons or hyphens commonly typed after TODO
                        todo_text = todo_text.lstrip(":- ").strip()
                        
                        if todo_text:
                            found_todos.append((py_file, line_num, todo_text))
        except (UnicodeDecodeError, PermissionError):
            continue

    if not found_todos:
        print("No TODOs found in Python files.")
        return

    # 2. Prepare the new Markdown content
    markdown_lines = [f"\n{header_marker}\n"]
    for file, line_no, text in found_todos:
        markdown_lines.append(f"- **{file}** (Line {line_no}): {text}\n")

    # 3. Read existing README content and strip old section if present
    readme_content = ""
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as readme:
            readme_content = readme.read()

    # If the marker already exists, slice the file up to that point
    if header_marker in readme_content:
        # Split by the header and keep everything before it, stripping trailing whitespaces
        readme_content = readme_content.split(header_marker)[0].rstrip()

    # 4. Overwrite/Append back to README.md
    with open(readme_path, "w", encoding="utf-8") as readme:
        if readme_content:
            readme.write(readme_content + "\n")
        readme.writelines(markdown_lines)

    print(f"Successfully updated {len(found_todos)} TODOs under '{header_marker}' in {readme_path}")


if __name__ == "__main__":
    update_todos_in_readme()