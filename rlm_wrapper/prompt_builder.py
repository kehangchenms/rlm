"""
Prompt Builder for Appraisal Review

This module provides functions to build optimized prompts for each category
by combining universal sections with category-specific sections.
"""

from typing import List, Dict, Any, Optional
from .prompts import (
    INTRODUCTION,
    CRITICAL_FORMATTING,
    SECTION_A_STANDARD,
    SECTION_A1_EVALUATIVE,
    CRITICAL_INSTRUCTIONS,
    SECTION_B_VALUE_CONCLUSIONS,
    SECTION_C_RECONCILIATION,
    SECTION_D_SITE_VALUATION,
    SECTION_E_REVIEWER_FINDINGS,
    SECTION_F_RISK_ASSESSMENT,
    SECTION_G_EXPANDED_INSIGHTS,
    SECTION_H_DCF_ANALYSIS,
    SECTION_I_PROPERTY_INFO,
)
from .prompts.section_g_expanded import get_section_g_for_questions


# Category ID to name mapping (from database review-manager-poc)
CATEGORY_NAMES = {
    1: "1. Transaction Details",
    2: "2. Property Information",
    3: "3. Appraisal Information",
    4: "4. Review Information",
    11: "5. Value Conclusion(s) in the Report Under Review (2-2(a)(v), 2-2(a)(vi), 2-2(a)(vii))",
    12: "6. Appraisal Report Extraordinary Assumptions and/or Hypothetical Conditions (2-2(a)(xiii))",
    13: "8. Risk Assessment",
    14: "9. Reviewer Findings, Opinions and Conclusions – Appraisal Report Compliance with (2-2(a)(x))",
    15: "10. Regional, Neighborhood, and Market Analysis",
    16: "11. Subject Site and Improvements",
    17: "12. Highest and Best Use",
    18: "13. Site Valuation",
    19: "18. USPAP Compliance",
    20: "19. FIRREA Compliance",
    21: "20. Expanded Appraisal Insights",
    22: "7. Review Report Extraordinary Assumptions and/or Hypothetical Conditions (4-2(f))",
    23: "14. Cost Approach",
    24: "15. Sales Approach",
    25: "16. Income Approach",
    26: "17. Reconciliation",
    27: "5. Value Conclusions",
}

# Categories that use only standard approach (Section A)
# Categories NOT in this set have specialized sections
STANDARD_ONLY_CATEGORIES = {1, 2, 3, 4, 12, 15, 16, 17, 19, 20, 22, 23, 24}


class PromptBuilder:
    """
    Builder class for constructing category-specific prompts.

    This class provides methods to build optimized prompts that include
    only the necessary sections for each question category.
    """

    def __init__(self, include_property_info: bool = True):
        """
        Initialize the PromptBuilder.

        Args:
            include_property_info: Whether to include Section I (property info)
                                   in all prompts. Default True.
        """
        self.include_property_info = include_property_info

    def get_universal_sections(self) -> str:
        """
        Get the universal sections that apply to all categories.

        Returns:
            Combined universal prompt sections
        """
        return (
            INTRODUCTION +
            CRITICAL_FORMATTING +
            SECTION_A_STANDARD +
            SECTION_A1_EVALUATIVE
        )

    def get_category_specific_section(
        self,
        category_id: int,
        questions: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Get the category-specific section for a given category.

        Args:
            category_id: The category ID from database (1, 2, 3, ..., 27)
            questions: Optional list of questions for context-aware selection

        Returns:
            Category-specific prompt section, or empty string if none needed

        Category ID to Section Mapping (from review-manager-poc database):
            11, 27: Value Conclusions -> Section B
            13: Risk Assessment -> Section F (SWOT)
            14: Reviewer Findings -> Section E (Data Extraction)
            18: Site Valuation -> Section D
            25: Income Approach -> Section H (DCF) if applicable
            26: Reconciliation -> Section C
            21: Expanded Appraisal Insights -> Section G
        """
        if category_id in STANDARD_ONLY_CATEGORIES:
            return ""

        # Category 11 & 27: Value Conclusions
        if category_id in (11, 27):
            return SECTION_B_VALUE_CONCLUSIONS

        # Category 13: Risk Assessment
        elif category_id == 13:
            return SECTION_F_RISK_ASSESSMENT

        # Category 14: Reviewer Findings
        elif category_id == 14:
            return SECTION_E_REVIEWER_FINDINGS

        # Category 18: Site Valuation
        elif category_id == 18:
            return SECTION_D_SITE_VALUATION

        # Category 25: Income Approach (may include DCF)
        elif category_id == 25:
            # Check if questions involve DCF
            if questions and self._has_dcf_questions(questions):
                return SECTION_H_DCF_ANALYSIS
            return ""

        # Category 26: Reconciliation
        elif category_id == 26:
            return SECTION_C_RECONCILIATION

        # Category 21: Expanded Appraisal Insights
        elif category_id == 21:
            # For expanded insights, can optionally filter to relevant Q1-Q21
            if questions:
                q_numbers = self._extract_group20_question_numbers(questions)
                if q_numbers:
                    return get_section_g_for_questions(q_numbers)
            return SECTION_G_EXPANDED_INSIGHTS

        return ""

    def build_prompt(
        self,
        category_id: int,
        questions: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Build a complete prompt for a specific category.

        Args:
            category_id: The category ID
            questions: Optional list of questions for context-aware selection

        Returns:
            Complete prompt string with all relevant sections
        """
        # Start with universal sections
        prompt = self.get_universal_sections()

        # Add category-specific section
        category_section = self.get_category_specific_section(category_id, questions)
        if category_section:
            prompt += "\n" + category_section

        # Optionally add property info section
        if self.include_property_info:
            prompt += "\n" + SECTION_I_PROPERTY_INFO

        # Always end with critical instructions
        prompt += "\n" + CRITICAL_INSTRUCTIONS

        return prompt

    def _has_dcf_questions(self, questions: List[Dict[str, Any]]) -> bool:
        """
        Check if any questions involve DCF analysis.

        Args:
            questions: List of question dictionaries

        Returns:
            True if DCF-related questions are present
        """
        dcf_keywords = ["dcf", "discounted cash flow", "discount rate", "terminal"]
        for q in questions:
            q_text = q.get("text", "").lower()
            if any(kw in q_text for kw in dcf_keywords):
                return True
        return False

    def _extract_group20_question_numbers(
        self,
        questions: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Extract Q1-Q21 numbers from Group 20 questions.

        Args:
            questions: List of question dictionaries

        Returns:
            List of question numbers (1-21) found
        """
        # This would need to map question IDs to Q1-Q21 numbers
        # based on the actual question content or metadata
        # For now, return empty to use full Section G
        return []

    def estimate_tokens(self, prompt: str) -> int:
        """
        Estimate token count for a prompt.

        Uses rough estimate of 1 token per 4 characters.

        Args:
            prompt: The prompt string

        Returns:
            Estimated token count
        """
        return len(prompt) // 4


def build_prompt_for_category(
    category_id: int,
    questions: Optional[List[Dict[str, Any]]] = None,
    include_property_info: bool = True
) -> str:
    """
    Convenience function to build a prompt for a specific category.

    Args:
        category_id: The category ID (3, 5, 6, ..., 20)
        questions: Optional list of questions for context-aware selection
        include_property_info: Whether to include property info section

    Returns:
        Complete prompt string

    Example:
        >>> prompt = build_prompt_for_category(8)  # Risk Assessment
        >>> print(len(prompt))  # Much smaller than full monolithic prompt
    """
    builder = PromptBuilder(include_property_info=include_property_info)
    return builder.build_prompt(category_id, questions)


def get_prompt_size_comparison() -> Dict[str, int]:
    """
    Get a comparison of prompt sizes for each category.

    Returns:
        Dictionary mapping category names to estimated token counts
    """
    builder = PromptBuilder()
    result = {}

    for cat_id, cat_name in CATEGORY_NAMES.items():
        prompt = builder.build_prompt(cat_id)
        tokens = builder.estimate_tokens(prompt)
        result[f"{cat_id}. {cat_name}"] = tokens

    return result


def format_questions_for_prompt(questions: List[Dict[str, Any]]) -> str:
    """
    Format questions for inclusion in a prompt.

    Args:
        questions: List of question dictionaries with 'id' and 'text' keys

    Returns:
        Formatted questions string
    """
    formatted = []
    for q in questions:
        q_id = q.get("id") or q.get("question_id")
        q_text = q.get("text") or q.get("question_text")
        if q_id and q_text:
            formatted.append(f"Question {q_id}: {q_text}")

    return "\n\n".join(formatted)
