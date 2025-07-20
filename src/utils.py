import re
import difflib
from typing import List, Dict, Optional, Any

def fuzzy_match(query: str, choices: List[str], cutoff: float = 0.6) -> List[str]:
    """Return a list of choices that best match the query (fuzzy, case-insensitive)."""
    return difflib.get_close_matches(query, choices, n=5, cutoff=cutoff)

def filter_documents(
    docs: List[Dict[str, Any]], 
    file_type: Optional[str] = None, 
    date_range: Optional[List[str]] = None, 
    size_range: Optional[List[int]] = None,
    tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Filter documents by type, date, size, or tags."""
    filtered = docs
    if file_type:
        filtered = [d for d in filtered if d.get("type") == file_type]
    if date_range:
        start, end = date_range
        filtered = [d for d in filtered if start <= d.get("date", "") <= end]
    if size_range:
        min_size, max_size = size_range
        filtered = [d for d in filtered if min_size <= d.get("size", 0) <= max_size]
    if tags:
        filtered = [d for d in filtered if set(tags) & set(d.get("tags", []))]
    return filtered

def syntax_highlight(text: str, filetype: str = "txt") -> str:
    """Dummy syntax highlighter (real logic should use Pygments or Rich in CLI)."""
    # For CLI, delegate to Rich's Syntax class
    return text

def format_error(msg: str) -> str:
    return f"[bold red]Error:[/bold red] {msg}"

def format_success(msg: str) -> str:
    return f"[bold green]Success:[/bold green] {msg}"

def async_sleep(secs: float):
    import anyio
    return anyio.sleep(secs)
