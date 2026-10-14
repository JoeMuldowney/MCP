from pathlib import Path

from fastmcp import FastMCP

import os
from dotenv import load_dotenv

load_dotenv()


mcp = FastMCP("My MCP Server")

BACKEND_ROOT = Path(os.environ["BACKEND"]).resolve()
FRONTEND_ROOT = Path(os.environ["FRONTEND"]).resolve()

def get_safe_path(project_root: str, filename: str) -> Path:
    roots = {
        "backend": BACKEND_ROOT,
        "frontend": FRONTEND_ROOT,
    }

    if project_root not in roots:
        raise ValueError("project_root must be 'backend' or 'frontend'.")

    root = roots[project_root]

    # Resolve the path using the actual Path object (root)
    path = (root / filename).resolve()

    if not path.is_relative_to(root):
        raise ValueError("File is outside the project root.")

    return path

@mcp.tool()
def search_all_files(project_root: str) -> str:
    """
    List all available files in the specified project.

    Use this tool to discover the files and directories available
    in a project before reading or editing a specific file.

    :param project_root: The project containing the file. Must be "backend" or "frontend".
    """
    roots = {
        "backend": BACKEND_ROOT,
        "frontend": FRONTEND_ROOT,
    }

    if project_root not in roots:
        raise ValueError("project_root must be 'backend' or 'frontend'.")

    root = roots[project_root]

    excluded_dirs = {
        ".venv",
        ".git",
        "__pycache__",
        "node_modules",
        ".pytest_cache",
    }

    files = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        relative_path = path.relative_to(root)

        if any(
            part in excluded_dirs or part.startswith(".")
            for part in relative_path.parts
        ):
            continue

        files.append(str(relative_path))

    return "\n".join(sorted(files))

@mcp.tool()
def read_file(project_root: str, filename: str) -> str:
    """
    Read the complete contents of a file from the specified project.

    Use this tool when you need to inspect a file's contents before
    making a change or when the user asks about the contents of a file.

    :param project_root: The project containing the file. Must be "backend" or "frontend".
    :param filename: The path to the file relative to the project's root directory.
    """
    path = get_safe_path(project_root, filename)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {filename}")

    return path.read_text()


@mcp.tool()
def edit_file(
    project_root: str,
    filename: str,
    anchor: str,
    new_text: str,
    position: str,
) -> str:

    """
    Make a targeted change to an existing file.

    The file must be read first so the anchor can be taken from its
    current contents. The anchor must be exact and must occur exactly
    once in the file.

    Use "before" or "after" to insert new text around the anchor.
    Use "replace" to replace the anchor with the new text.

    :param project_root: The project containing the file. Must be "backend" or "frontend".
    :param filename: The path to the file relative to the project's root directory.
    :param anchor: Exact existing text identifying the location of the edit.
    :param new_text: Text to insert or use as the replacement.
    :param position: Must be "before", "after", or "replace".
    """
    path = get_safe_path(project_root, filename)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {filename}")

    if not anchor:
        raise ValueError("anchor cannot be empty.")

    if position not in {"before", "after", "replace"}:
        raise ValueError(
            "position must be 'before', 'after', or 'replace'."
        )

    content = path.read_text()

    matches = content.count(anchor)

    if matches == 0:
        raise ValueError(
            "The anchor text was not found in the file."
        )

    if matches > 1:
        raise ValueError(
            f"The anchor text was found {matches} times. "
            "The anchor must be unique."
        )

    if position == "before":
        replacement = new_text + anchor

    elif position == "after":
        replacement = anchor + new_text

    else:
        replacement = new_text

    content = content.replace(anchor, replacement, 1)

    path.write_text(content)

    return f"Successfully edited {filename}"

if __name__ == "__main__":
    mcp.run()