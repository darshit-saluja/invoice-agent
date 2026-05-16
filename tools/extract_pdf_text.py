"""
Extracts raw text from a PDF and writes it to .tmp/<filename>.txt.

Usage:
    python tools/extract_pdf_text.py <pdf_path>

Output:
    Prints the path of the .txt file to stdout.
"""

import os
import sys

import pdfplumber


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/extract_pdf_text.py <pdf_path>", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)

    full_text = "\n\n".join(pages)

    base = os.path.splitext(os.path.basename(pdf_path))[0]
    txt_path = os.path.join(".tmp", f"{base}.txt")
    os.makedirs(".tmp", exist_ok=True)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    print(txt_path)


if __name__ == "__main__":
    main()
