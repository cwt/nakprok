"""
Walrus operator (:=) examples for nakprok.

The walrus operator requires pre-declared types, just like
match-case patterns. Declare the variable first, then use :=
to assign and test in a single expression.
"""

import re
from typing import TextIO


def find_all_matches(text: str, pattern: str) -> list[str]:
    """Extract regex matches - check result and use it in one step."""
    matches: list[str]
    if matches := re.findall(pattern, text):
        return matches
    return []


def process_chunks(data: str) -> None:
    """Process data in chunks until empty."""
    chunk: str
    idx: int = 0
    chunk_size: int = 10

    while chunk := data[idx : idx + chunk_size]:
        print(f"Chunk: {chunk}")
        idx += chunk_size


def filter_valid_numbers(numbers: list[str]) -> list[int]:
    """Parse and filter numbers in one pass."""
    result: list[int] = []
    num: int
    s: str

    for s in numbers:
        if (num := int(s)) > 0:
            result.append(num)

    return result


def read_file_lines(filepath: str) -> list[str]:
    """Read file line by line until EOF."""
    lines: list[str] = []
    line: str
    f: TextIO

    with open(filepath, "r") as f:
        while line := f.readline():
            lines.append(line.strip())

    return lines


def main() -> None:
    """Demonstrate walrus operator use cases."""
    # Regex matching
    text: str = "Hello 42 world 123 test 7"
    numbers: list[str] = find_all_matches(text, r"\d+")
    print(f"Found numbers: {numbers}")

    # Filter and parse in one pass
    raw: list[str] = ["10", "-5", "0", "42", "-1"]
    valid: list[int] = filter_valid_numbers(raw)
    print(f"Valid positive: {valid}")

    # Chunk processing
    data: str = "abcdefghij1234567890"
    process_chunks(data)


if __name__ == "__main__":
    main()
