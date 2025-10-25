"""
Analyze and synthesize ATS knowledge using Claude
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic
import json

load_dotenv()

def read_extracted_texts():
    """Read all extracted text files"""
    knowledge_dir = Path("knowledge_extracted")
    texts = {}

    for txt_file in knowledge_dir.glob("*.txt"):
        with open(txt_file, 'r', encoding='utf-8') as f:
            texts[txt_file.stem] = f.read()

    return texts

def synthesize_ats_knowledge(texts):
    """Use Claude to synthesize ATS knowledge"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Combine all texts with clear separators
    combined_text = ""
    for filename, text in texts.items():
        combined_text += f"\n\n{'='*80}\n"
        combined_text += f"SOURCE: {filename}\n"
        combined_text += f"{'='*80}\n\n"
        combined_text += text

    prompt = f"""Analyze the following ATS (Applicant Tracking System) knowledge from multiple sources and create a comprehensive, structured knowledge base that will be used to generate ATS-optimized resumes.

{combined_text}

Please provide a structured synthesis covering:

1. **ATS Fundamentals**
   - What ATS systems are and how they work
   - Common ATS platforms and their characteristics
   - Key parsing and ranking mechanisms

2. **Resume Formatting Best Practices**
   - File format recommendations
   - Font and layout guidelines
   - Section organization
   - What to avoid (tables, graphics, columns, etc.)

3. **Keyword Optimization**
   - How to identify and use keywords
   - Where to place keywords strategically
   - Industry-specific vs. general keywords
   - Skills matching strategies

4. **Content Optimization**
   - How to write ATS-friendly descriptions
   - Quantifiable achievements formatting
   - Action verbs and power words
   - Tailoring content to job descriptions

5. **Common ATS Mistakes to Avoid**
   - Formatting errors that break parsing
   - Content mistakes that lower scores
   - File naming conventions

6. **ATS Scoring Factors**
   - What contributes to a high ATS score
   - How to maximize match percentage
   - Role-specific optimization strategies

Please be specific, actionable, and comprehensive. This will be used as the foundation for generating highly optimized resumes."""

    print("Sending request to Claude to analyze ATS knowledge...")

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=16000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text

def main():
    print("Reading extracted texts...")
    texts = read_extracted_texts()
    print(f"Loaded {len(texts)} text files")

    print("\nAnalyzing ATS knowledge with Claude...")
    ats_knowledge = synthesize_ats_knowledge(texts)

    # Save the synthesized knowledge
    output_file = "ats_knowledge_base.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# ATS Resume Knowledge Base\n\n")
        f.write("*Generated from 7 ATS knowledge sources*\n\n")
        f.write(ats_knowledge)

    print(f"\n✓ ATS knowledge base saved to {output_file}")
    print(f"✓ Knowledge base size: {len(ats_knowledge)} characters")

    # Also save as JSON for programmatic use
    knowledge_json = {
        "content": ats_knowledge,
        "sources": list(texts.keys()),
        "total_sources": len(texts)
    }

    with open("ats_knowledge_base.json", 'w', encoding='utf-8') as f:
        json.dump(knowledge_json, f, indent=2)

    print(f"✓ JSON version saved to ats_knowledge_base.json")

if __name__ == "__main__":
    main()
