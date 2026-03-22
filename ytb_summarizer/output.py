"""Save summary markdown to file."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime

from .utils import sanitize_filename


def save_summary(
    content: str,
    title: str,
    output_dir: str | Path,
) -> Path:
    """Write markdown content to a file and return the path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = sanitize_filename(title)
    filename = f"{date_str}_{safe_title}.md"
    path = output_dir / filename

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return path
