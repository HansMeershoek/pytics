"""HTML structure for the notebook landing view.

This module assembles escaped text. It does not read an analysis.
"""

from __future__ import annotations

from typing import Sequence
from typing import Tuple

from pytics.presentation.notebook.style import NOTEBOOK_CSS
from pytics.presentation.notebook.text import FindingLine
from pytics.presentation.notebook.text import html_text


def shell(kind: str, title: str, policy: str, body: str) -> str:
    """One self-contained report fragment."""
    return (
        f'<div class="pytics-report pytics-{kind}" data-pytics-kind="{kind}"'
        f' data-findings-policy="{html_text(policy)}">'
        f"<style>{NOTEBOOK_CSS}</style>"
        '<header class="pytics-header">'
        '<p class="pytics-mark">Pytics</p>'
        f"<h1>{html_text(title)}</h1>"
        "</header>"
        f"{body}"
        "</div>"
    )


def section(name: str, title: str, body: str) -> str:
    """A landing section. ``name`` is a renderer class token."""
    return (
        f'<section class="pytics-{name}" aria-label="{html_text(title)}">'
        f"<h2>{html_text(title)}</h2>"
        f"{body}"
        "</section>"
    )


def metrics(items: Sequence[Tuple[str, str]]) -> str:
    """A wrapping row of labeled counts."""
    parts = ['<dl class="pytics-metrics">']
    for label, value in items:
        parts.append(
            '<div class="pytics-metric">'
            f"<dt>{html_text(label)}</dt>"
            f"<dd>{html_text(value)}</dd>"
            "</div>"
        )
    parts.append("</dl>")
    return "".join(parts)


def facts(rows: Sequence[Tuple[str, str]]) -> str:
    """A two-column table of labels and values."""
    parts = [
        '<table class="pytics-facts">',
        "<colgroup>",
        '<col class="pytics-col-label">',
        '<col class="pytics-col-value">',
        "</colgroup>",
        "<tbody>",
    ]
    for label, value in rows:
        parts.append(
            "<tr>"
            f'<th scope="row">{html_text(label)}</th>'
            f"<td>{html_text(value)}</td>"
            "</tr>"
        )
    parts.append("</tbody></table>")
    return "".join(parts)


def sides(
    headers: Tuple[str, str, str],
    rows: Sequence[Tuple[str, str, str]],
) -> str:
    """A three-column table: measure, reference, comparison."""
    parts = [
        '<table class="pytics-sides">',
        "<colgroup>",
        '<col class="pytics-col-label">',
        '<col class="pytics-col-value">',
        '<col class="pytics-col-value">',
        "</colgroup>",
        "<thead><tr>",
    ]
    for header in headers:
        parts.append(f'<th scope="col">{html_text(header)}</th>')
    parts.append("</tr></thead><tbody>")
    for label, reference, comparison in rows:
        parts.append(
            "<tr>"
            f'<th scope="row">{html_text(label)}</th>'
            f"<td>{html_text(reference)}</td>"
            f"<td>{html_text(comparison)}</td>"
            "</tr>"
        )
    parts.append("</tbody></table>")
    return "".join(parts)


def findings_block(
    summary: str,
    lines: Sequence[FindingLine],
    notes: Sequence[str],
) -> str:
    """Findings summary, the landing rows, and the notes under them."""
    parts = []
    if summary:
        css = "pytics-counts" if lines else "pytics-note"
        parts.append(f'<p class="{css}">{html_text(summary)}</p>')
    if lines:
        parts.append('<ol class="pytics-finding-list">')
        for line in lines:
            parts.append(_finding_item(line))
        parts.append("</ol>")
    for note in notes:
        parts.append(f'<p class="pytics-note">{html_text(note)}</p>')
    return "".join(parts)


def notes(lines: Sequence[str]) -> str:
    """Muted paragraphs of renderer text."""
    return "".join(f'<p class="pytics-note">{html_text(line)}</p>' for line in lines)


def subhead(title: str) -> str:
    """A label under a section heading."""
    return f'<p class="pytics-subhead">{html_text(title)}</p>'


def _finding_item(line: FindingLine) -> str:
    attributes = " ".join(
        f'{name}="{html_text(value)}"' for name, value in line.attributes
    )
    css = f"pytics-severity pytics-severity-{line.severity}"
    detail = ""
    if line.detail:
        detail = f'<span class="pytics-finding-detail">{html_text(line.detail)}</span>'
    return (
        f'<li class="pytics-finding" {attributes}>'
        f'<span class="{css}">{html_text(line.severity_label)}</span>'
        '<span class="pytics-finding-body">'
        f'<span class="pytics-finding-title">{html_text(line.title)}</span>'
        f'<span class="pytics-finding-subject">{html_text(line.subject)}</span>'
        f"{detail}"
        "</span>"
        "</li>"
    )
