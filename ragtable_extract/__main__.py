"""python -m ragtable_extract document.pdf output.html"""

import sys

from . import convert


def main():
    if len(sys.argv) < 3:
        print("Usage: python -m ragtable_extract <input.pdf> <output.html>")
        sys.exit(1)
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    _, tables = convert(input_path=input_path, output_path=output_path)
    print(f"Extracted {len(tables)} tables to {output_path}")


if __name__ == "__main__":
    main()
