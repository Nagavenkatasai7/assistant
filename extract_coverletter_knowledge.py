"""
Extract cover letter knowledge from PDF files
"""
import os
from pypdf import PdfReader
from pathlib import Path
import json

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file"""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def main():
    knowledge_dir = Path("coverletter-knowledge")
    pdf_files = list(knowledge_dir.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files in coverletter-knowledge folder")

    all_knowledge = {}

    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file.name}")
        text = extract_text_from_pdf(pdf_file)

        if text:
            # Store the extracted text
            all_knowledge[pdf_file.name] = {
                "filename": pdf_file.name,
                "text_length": len(text),
                "preview": text[:500] + "..." if len(text) > 500 else text
            }

            # Save full text to a separate file for later use
            output_file = Path("coverletter_knowledge_extracted") / f"{pdf_file.stem}.txt"
            output_file.parent.mkdir(exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"  ✓ Extracted {len(text)} characters")
            print(f"  ✓ Saved to {output_file}")

    # Save summary
    with open("coverletter_knowledge_summary.json", 'w') as f:
        json.dump(all_knowledge, f, indent=2)

    print(f"\n✓ Successfully processed {len(all_knowledge)} PDFs")
    print(f"✓ Extracted knowledge saved to coverletter_knowledge_extracted/ folder")
    print(f"✓ Summary saved to coverletter_knowledge_summary.json")

if __name__ == "__main__":
    main()
