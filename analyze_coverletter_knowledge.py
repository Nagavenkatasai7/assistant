"""
Analyze and synthesize cover letter knowledge using Claude
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import anthropic
import json

load_dotenv()

def read_extracted_texts():
    """Read all extracted text files"""
    knowledge_dir = Path("coverletter_knowledge_extracted")
    texts = {}

    for txt_file in knowledge_dir.glob("*.txt"):
        with open(txt_file, 'r', encoding='utf-8') as f:
            texts[txt_file.stem] = f.read()

    return texts

def synthesize_coverletter_knowledge(texts):
    """Use Claude to synthesize cover letter knowledge"""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Combine all texts with clear separators
    combined_text = ""
    for filename, text in texts.items():
        combined_text += f"\n\n{'='*80}\n"
        combined_text += f"SOURCE: {filename}\n"
        combined_text += f"{'='*80}\n\n"
        combined_text += text

    prompt = f"""Analyze the following cover letter knowledge from multiple sources and create a comprehensive, structured knowledge base for generating professional cover letters.

{combined_text}

Please provide a structured synthesis covering:

1. **Cover Letter Fundamentals**
   - Purpose and importance
   - When to include a cover letter
   - Key components and structure

2. **Format and Structure Best Practices**
   - Standard format (header, greeting, body, closing)
   - Length guidelines
   - Professional formatting rules
   - Font and layout recommendations

3. **Content Strategy**
   - Opening paragraph techniques
   - Body paragraph structure
   - Closing paragraph best practices
   - Storytelling and personality
   - Quantifiable achievements

4. **Customization Techniques**
   - Researching the company
   - Tailoring to job description
   - Addressing specific requirements
   - Using keywords effectively

5. **Common Mistakes to Avoid**
   - Generic/template language
   - Repeating the resume
   - Length issues
   - Tone problems
   - Formatting errors

6. **Power Strategies**
   - Attention-grabbing openings
   - Demonstrating value
   - Showing cultural fit
   - Creating urgency
   - Strong call-to-action

7. **Modern Cover Letter Trends (2025)**
   - ATS optimization
   - AI-assisted writing tips
   - Digital vs traditional formats
   - Industry-specific approaches

Please be specific, actionable, and comprehensive. This will be used as the foundation for generating compelling cover letters that complement resumes."""

    print("Sending request to Claude to analyze cover letter knowledge...")

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

    print("\nAnalyzing cover letter knowledge with Claude...")
    coverletter_knowledge = synthesize_coverletter_knowledge(texts)

    # Save the synthesized knowledge
    output_file = "coverletter_knowledge_base.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Cover Letter Knowledge Base\n\n")
        f.write("*Generated from 5 cover letter knowledge sources*\n\n")
        f.write(coverletter_knowledge)

    print(f"\n✓ Cover letter knowledge base saved to {output_file}")
    print(f"✓ Knowledge base size: {len(coverletter_knowledge)} characters")

    # Also save as JSON for programmatic use
    knowledge_json = {
        "content": coverletter_knowledge,
        "sources": list(texts.keys()),
        "total_sources": len(texts)
    }

    with open("coverletter_knowledge_base.json", 'w', encoding='utf-8') as f:
        json.dump(knowledge_json, f, indent=2)

    print(f"✓ JSON version saved to coverletter_knowledge_base.json")

if __name__ == "__main__":
    main()
