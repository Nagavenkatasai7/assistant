"""
Resume Validator - Enforces Microsoft Recruiter Requirements
Validates STAR format compliance and forbidden verb usage
"""
import re
from typing import Dict, List, Tuple


class ResumeValidator:
    """Validates resume against Microsoft recruiter standards"""

    # Forbidden verbs that make resumes blend in
    FORBIDDEN_VERBS = [
        "led", "managed", "handled", "worked on", "developed",
        "responsible for", "helped with", "assisted with",
        "involved in", "participated in", "contributed to",
        "achieved", "built", "applied", "analyzed", "designed"
    ]

    # STAR format situation openers
    STAR_OPENERS = [
        "when ", "faced with ", "motivated by ", "diagnosed ",
        "identified ", "inherited ", "discovered "
    ]

    def __init__(self, min_star_percentage: float = 60.0):
        """
        Initialize validator

        Args:
            min_star_percentage: Minimum required percentage of STAR format bullets (default 60%)
        """
        self.min_star_percentage = min_star_percentage

    def validate_resume(self, resume_content: str, company_name: str = None) -> Dict:
        """
        Validate complete resume against all requirements

        Args:
            resume_content: Full resume markdown text
            company_name: Company name to check for customization

        Returns:
            Dict with validation results and detailed feedback
        """
        # Count bullets
        total_bullets = self._count_bullets(resume_content)

        # Check STAR format
        star_bullets = self._count_star_bullets(resume_content)
        star_percentage = (star_bullets / total_bullets * 100) if total_bullets > 0 else 0

        # Check forbidden verbs
        forbidden_found = self._find_forbidden_verbs(resume_content)

        # Check company customization
        has_company_name = self._check_company_mention(resume_content, company_name) if company_name else True

        # Check personal section
        has_personal_section = self._check_personal_section(resume_content)

        # Calculate pass/fail
        passes_star = star_percentage >= self.min_star_percentage
        passes_verbs = len(forbidden_found) == 0
        passes_company = has_company_name
        passes_personal = has_personal_section

        overall_pass = passes_star and passes_verbs and passes_company and passes_personal

        return {
            "overall_pass": overall_pass,
            "total_bullets": total_bullets,
            "star_bullets": star_bullets,
            "star_percentage": round(star_percentage, 1),
            "passes_star_requirement": passes_star,
            "forbidden_verbs_found": forbidden_found,
            "forbidden_verb_count": len(forbidden_found),
            "passes_verb_requirement": passes_verbs,
            "has_company_mention": has_company_name,
            "passes_company_requirement": passes_company,
            "has_personal_section": has_personal_section,
            "passes_personal_requirement": passes_personal,
            "feedback": self._generate_feedback(
                total_bullets, star_bullets, star_percentage,
                forbidden_found, has_company_name, has_personal_section
            )
        }

    def _count_bullets(self, text: str) -> int:
        """Count all bullet points in experience/projects/publications sections"""
        # Match lines starting with "- " (markdown bullet)
        # Exclude education bullets and personal section
        lines = text.split('\n')

        in_experience_section = False
        bullet_count = 0

        for line in lines:
            line_lower = line.lower().strip()

            # Start counting after education, in experience/projects/publications
            if any(marker in line_lower for marker in ['## professional experience', '## research', '## projects', '## publications', '## research & professional']):
                in_experience_section = True
                continue

            # Stop counting at personal section or additional sections
            if '## what drives me' in line_lower or '## additional' in line_lower:
                in_experience_section = False
                continue

            # Count bullets in experience sections
            if in_experience_section and line.strip().startswith('- '):
                bullet_count += 1

        return bullet_count

    def _count_star_bullets(self, text: str) -> int:
        """Count bullets that use STAR format (start with situation context)"""
        lines = text.split('\n')

        in_experience_section = False
        star_count = 0

        for line in lines:
            line_lower = line.lower().strip()

            # Track sections
            if any(marker in line_lower for marker in ['## professional experience', '## research', '## projects', '## publications', '## research & professional']):
                in_experience_section = True
                continue

            if '## what drives me' in line_lower or '## additional' in line_lower:
                in_experience_section = False
                continue

            # Check if bullet starts with STAR opener
            if in_experience_section and line.strip().startswith('- '):
                bullet_text = line.strip()[2:].lower()  # Remove "- " prefix
                if any(bullet_text.startswith(opener) for opener in self.STAR_OPENERS):
                    star_count += 1

        return star_count

    def _find_forbidden_verbs(self, text: str) -> List[Dict[str, str]]:
        """
        Find all instances of forbidden verbs in resume

        Returns:
            List of dicts with {verb, context, line_number}
        """
        forbidden_instances = []
        lines = text.split('\n')

        in_experience_section = False

        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower().strip()

            # Track sections
            if any(marker in line_lower for marker in ['## professional experience', '## research', '## projects', '## publications', '## research & professional']):
                in_experience_section = True
                continue

            if '## what drives me' in line_lower or '## additional' in line_lower:
                in_experience_section = False
                continue

            # Check bullets for forbidden verbs
            if in_experience_section and line.strip().startswith('- '):
                for verb in self.FORBIDDEN_VERBS:
                    # Use word boundary regex to avoid false positives
                    pattern = r'\b' + re.escape(verb) + r'\b'
                    if re.search(pattern, line_lower):
                        # Extract context (up to 60 chars around the verb)
                        match = re.search(pattern, line_lower)
                        start = max(0, match.start() - 30)
                        end = min(len(line), match.end() + 30)
                        context = line[start:end]

                        forbidden_instances.append({
                            "verb": verb,
                            "line_number": line_num,
                            "context": context.strip()
                        })

        return forbidden_instances

    def _check_company_mention(self, text: str, company_name: str) -> bool:
        """Check if company name is mentioned in professional summary"""
        if not company_name:
            return True

        # Get professional summary section
        lines = text.split('\n')
        in_summary = False
        summary_text = []

        for line in lines:
            if '## professional summary' in line.lower():
                in_summary = True
                continue
            if line.startswith('##') and in_summary:
                break
            if in_summary:
                summary_text.append(line)

        summary = ' '.join(summary_text).lower()
        return company_name.lower() in summary

    def _check_personal_section(self, text: str) -> bool:
        """Check if resume has 'What Drives Me' or personal section"""
        text_lower = text.lower()
        return '## what drives me' in text_lower or '## beyond work' in text_lower

    def _generate_feedback(
        self,
        total_bullets: int,
        star_bullets: int,
        star_percentage: float,
        forbidden_verbs: List[Dict],
        has_company: bool,
        has_personal: bool
    ) -> List[str]:
        """Generate actionable feedback for improving resume"""
        feedback = []

        # STAR format feedback
        if star_percentage < 60:
            needed = int(total_bullets * 0.6) - star_bullets
            feedback.append(
                f"❌ STAR format: {star_percentage:.1f}% ({star_bullets}/{total_bullets} bullets). "
                f"Need {needed} more bullets with situation context (start with 'When...', 'Motivated by...', etc.)"
            )
        else:
            feedback.append(f"✅ STAR format: {star_percentage:.1f}% ({star_bullets}/{total_bullets} bullets) - PASSED")

        # Forbidden verbs feedback
        if len(forbidden_verbs) > 0:
            verb_list = [f"'{v['verb']}' (line {v['line_number']})" for v in forbidden_verbs[:5]]
            feedback.append(
                f"❌ Forbidden verbs: {len(forbidden_verbs)} instances found - {', '.join(verb_list)}"
            )
        else:
            feedback.append("✅ Forbidden verbs: None found - PASSED")

        # Company mention feedback
        if not has_company:
            feedback.append("⚠️ Company customization: Company name not found in professional summary")
        else:
            feedback.append("✅ Company customization: Company mentioned in summary - PASSED")

        # Personal section feedback
        if not has_personal:
            feedback.append("❌ Personal section: 'What Drives Me' section missing")
        else:
            feedback.append("✅ Personal section: 'What Drives Me' included - PASSED")

        return feedback

    def auto_fix_forbidden_verbs(self, resume_content: str) -> str:
        """
        Automatically replace forbidden verbs with approved alternatives

        Args:
            resume_content: Resume markdown text

        Returns:
            Fixed resume content with forbidden verbs replaced
        """
        # Verb replacement mapping (forbidden → preferred alternatives)
        VERB_REPLACEMENTS = {
            "achieved": "delivered",
            "built": "engineered",
            "applied": "deployed",
            "analyzed": "investigated",
            "designed": "architected",
            "led": "spearheaded",
            "managed": "orchestrated",
            "handled": "executed",
            "worked on": "contributed to",
            "developed": "engineered"
        }

        fixed_content = resume_content
        lines = resume_content.split('\n')
        in_experience_section = False

        for line_num, line in enumerate(lines):
            line_lower = line.lower().strip()

            # Track sections
            if any(marker in line_lower for marker in ['## professional experience', '## research', '## projects', '## publications', '## research & professional']):
                in_experience_section = True
                continue

            if '## what drives me' in line_lower or '## additional' in line_lower:
                in_experience_section = False
                continue

            # Fix bullets in experience sections
            if in_experience_section and line.strip().startswith('- '):
                original_line = line
                fixed_line = line

                for forbidden_verb, replacement in VERB_REPLACEMENTS.items():
                    # Use word boundary regex for precise matching
                    pattern = r'\b' + re.escape(forbidden_verb) + r'\b'

                    # Case-insensitive replacement preserving original case
                    if re.search(pattern, fixed_line, re.IGNORECASE):
                        # Find the match to preserve case
                        match = re.search(pattern, fixed_line, re.IGNORECASE)
                        if match:
                            original_verb = match.group()
                            # Preserve capitalization
                            if original_verb[0].isupper():
                                replacement_verb = replacement.capitalize()
                            else:
                                replacement_verb = replacement

                            fixed_line = re.sub(pattern, replacement_verb, fixed_line, flags=re.IGNORECASE)

                # Replace in full content if changed
                if fixed_line != original_line:
                    fixed_content = fixed_content.replace(original_line, fixed_line)

        return fixed_content

    def print_validation_report(self, validation_result: Dict) -> None:
        """Print formatted validation report"""
        print("\n" + "="*80)
        print("RESUME VALIDATION REPORT")
        print("="*80)

        print(f"\n{'OVERALL STATUS:':<30} {'✅ PASS' if validation_result['overall_pass'] else '❌ FAIL'}")
        print(f"{'Total Bullets:':<30} {validation_result['total_bullets']}")
        print(f"{'STAR Format Bullets:':<30} {validation_result['star_bullets']} ({validation_result['star_percentage']:.1f}%)")
        print(f"{'Forbidden Verbs Found:':<30} {validation_result['forbidden_verb_count']}")

        print("\nDETAILED FEEDBACK:")
        for item in validation_result['feedback']:
            print(f"  {item}")

        if not validation_result['overall_pass']:
            print("\n⚠️ Resume does NOT meet Microsoft recruiter requirements")
            print("   Regeneration recommended")
        else:
            print("\n✅ Resume PASSES all Microsoft recruiter requirements")

        print("="*80 + "\n")
