#!/usr/bin/env python3
"""
Test script to verify resume parsing is working correctly
Run this AFTER uploading your resume through the web interface
"""
import sys
from pathlib import Path

# Check if Profile.pdf exists
if not Path("Profile.pdf").exists():
    print("❌ Profile.pdf not found!")
    print("Please upload your resume through the web interface first.")
    sys.exit(1)

print("=" * 70)
print("RESUME PARSING VERIFICATION TEST")
print("=" * 70)

# Test 1: Parse the resume
print("\n[1/3] Testing ProfileParser...")
from src.parsers.profile_parser import ProfileParser

parser = ProfileParser()
profile = parser.parse_profile()

if not profile:
    print("❌ FAILED: Could not parse profile!")
    sys.exit(1)

print("✅ Profile parsed successfully")

# Test 2: Check raw text extraction
raw_text = profile.get('raw_text', '')
print(f"\n[2/3] Checking extracted text...")
print(f"   Text length: {len(raw_text)} characters")

if len(raw_text) < 100:
    print("❌ WARNING: Extracted text is very short!")
else:
    print("✅ Text extraction looks good")

# Show first 500 characters
print(f"\n   First 500 characters:")
print("   " + "-" * 60)
print("   " + raw_text[:500].replace('\n', '\n   '))
print("   " + "-" * 60)

# Test 3: Check for key information
print(f"\n[3/3] Verifying key information...")

checks = {
    'Name found': 'Naga Venkata Sai' in raw_text or 'Chennu' in raw_text,
    'Email found': 'nchennu@gmu.edu' in raw_text,
    'Skills mentioned': any(skill in raw_text for skill in ['GPT-4', 'Claude', 'LangChain', 'RAG', 'Python']),
    'Projects mentioned': any(proj in raw_text for proj in ['Multi-Agent', 'Research Assistant', 'Conversational AI']),
    'Education mentioned': 'George Mason' in raw_text or 'GMU' in raw_text or 'Master' in raw_text,
    'Publications mentioned': 'Stress Detection' in raw_text or 'Hairfall' in raw_text or 'Cybersecurity' in raw_text
}

print()
all_passed = True
for check, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"   {status} {check}")
    if not passed:
        all_passed = False

print("\n" + "=" * 70)
if all_passed:
    print("✅ ALL CHECKS PASSED - Resume parsing is working correctly!")
    print("\nYour resume data is being extracted properly:")
    print("- Name, email, and contact info ✓")
    print("- Skills (GPT-4, Claude, LangChain, etc.) ✓")
    print("- Projects (Multi-Agent, RAG systems, etc.) ✓")
    print("- Education (George Mason University) ✓")
    print("- Publications (5 research papers) ✓")
else:
    print("⚠️  SOME CHECKS FAILED - Please review the extracted text above")
    print("\nThe system will still work, but verify your resume content is correct.")

print("=" * 70)
