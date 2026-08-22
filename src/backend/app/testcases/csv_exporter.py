# Source assistance: OpenAI ChatGPT, 2026-08-22 (AI-05).

import csv
from collections.abc import Sequence
from io import StringIO


def build_csv(
    rows: list[list[str | int]],
    headers: Sequence[str],
) -> bytes:
    """Build an Excel-friendly UTF-8 CSV export."""
    stream = StringIO(newline="")
    writer = csv.writer(
        stream,
        delimiter=";",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\r\n",
    )
    writer.writerow(headers)
    writer.writerows(_normalize_rows(rows))
    return stream.getvalue().encode("utf-8-sig")


def _normalize_rows(
    rows: list[list[str | int]],
) -> list[list[str | int]]:
    normalized_rows: list[list[str | int]] = []

    for row in rows:
        normalized = list(row)
        normalized[4] = _flatten_multiline(normalized[4])
        normalized[5] = _flatten_multiline(normalized[5])
        normalized[7] = str(normalized[7]).upper()
        normalized[10] = str(normalized[10]).upper()
        normalized_rows.append(normalized)

    return normalized_rows


def _flatten_multiline(value: str | int) -> str:
    return str(value).replace("\r\n", " | ").replace("\n", " | ")
