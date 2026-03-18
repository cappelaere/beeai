"""
/diagram command handler - View system diagrams
"""

from pathlib import Path


def handle_diagram(request, args, session_key):
    """
    Handle diagram viewing commands.

    Commands:
        /diagram list - List all available diagrams
        /diagram <name> - View a specific diagram

    Args:
        request: Django HTTP request
        args: Command arguments
        session_key: User session key

    Returns:
        Dictionary with content and metadata
    """
    # Path: agent_ui/agent_app/commands/diagram.py -> go up to beeai root, then to diagrams
    diagrams_path = Path(__file__).resolve().parent.parent.parent.parent / "diagrams"

    if not args:
        return {
            "content": (
                "Usage: /diagram <command>\n\n"
                "Commands:\n"
                "  list - List all available diagrams\n"
                "  <name> - View a specific diagram"
            ),
            "metadata": {"error": True, "command": "diagram"},
        }

    subcommand = args[0].lower()

    # List available diagrams
    if subcommand == "list":
        if not diagrams_path.exists():
            return {
                "content": f"No diagrams directory found.\n\nExpected location: {diagrams_path}",
                "metadata": {"command": "diagram list", "count": 0},
            }

        # Look for HTML files instead of .drawio files
        diagram_files = list(diagrams_path.glob("*.html"))

        if not diagram_files:
            return {
                "content": f"No HTML diagrams found in diagrams directory.\n\nFolder: {diagrams_path}\n\nAdd .html files to this folder.",
                "metadata": {"command": "diagram list", "count": 0},
            }

        lines = [
            f"📊 Available Diagrams ({len(diagram_files)} total)",
            f"Folder: {diagrams_path.relative_to(diagrams_path.parent)}",
            "",
        ]
        for diagram_file in sorted(diagram_files):
            name = diagram_file.stem
            size_kb = diagram_file.stat().st_size / 1024
            lines.append(f"  • {name} ({size_kb:.1f} KB)")

        lines.append("")
        lines.append("Use '/diagram <name>' to view a diagram")
        lines.append("URL: /diagrams/<name>.html")

        return {
            "content": "\n".join(lines),
            "metadata": {
                "command": "diagram list",
                "count": len(diagram_files),
                "folder": str(diagrams_path),
            },
        }

    # View a specific diagram
    diagram_name = subcommand
    diagram_file = diagrams_path / f"{diagram_name}.html"

    if not diagram_file.exists():
        available = [f.stem for f in diagrams_path.glob("*.html")] if diagrams_path.exists() else []
        return {
            "content": (
                f"Error: Diagram '{diagram_name}' not found\n\n"
                + (
                    "Available diagrams:\n" + "\n".join(f"  • {name}" for name in available)
                    if available
                    else "No HTML diagrams available."
                )
            ),
            "metadata": {"error": True},
        }

    # Return metadata to open diagram HTML file directly from static files
    return {
        "content": f"Opening diagram: {diagram_name}",
        "metadata": {"command": "diagram view", "diagram_name": diagram_name, "open_diagram": True},
        "diagram_url": f"/static/{diagram_name}.html",
    }
