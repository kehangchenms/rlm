# RLM Modular Prompt Design for Appraisal Review System

**Date:** 2026-01-29
**Author:** Claude Code
**Project:** Mountainseed Appraisal Review - RLM Integration

---

## Problem Statement

The current appraisal review system sends:
- Full document + complex system prompt + all 60-100 questions at once
- This fills up the context window, leaving little room for response tokens
- Results in truncated/incomplete answers
- Sending document multiple times is expensive

## Solution: RLM with Modular Prompts (Option B)

Use RLM (Recursive Language Models) to:
1. Store the document in a REPL context variable (sent once)
2. Group questions by their existing categories (16 categories)
3. For each category, build a minimal prompt (universal + category-specific sections)
4. Make parallel sub-calls with full response token capacity
5. Aggregate all answers

---

## Prompt Structure Analysis

### UNIVERSAL SECTIONS (apply to ALL categories)

| Section | Description | Source Lines |
|---------|-------------|--------------|
| **Introduction/Role** | Mountainseed SME role, context setup | 352-361 |
| **CRITICAL FORMATTING** | JSON format, plain text only, no markdown | 362-381 |
| **SECTION A: Standard Approach** | Default for most questions, polar questions, transcription rules | 386-470 |
| **SECTION A.1: Evaluative/Meta** | Professional judgment questions | 437-470 |
| **SECTION I: Property Info** | Property name/address extraction | 2051-2065 |
| **CRITICAL INSTRUCTIONS** | Must answer ALL, completion check, format | 2067-2104 |

### CATEGORY-SPECIFIC SECTIONS

| Category | Category Name | Specific Section |
|----------|---------------|------------------|
| **3** | Appraisal Information | Standard (A) only |
| **5** | Value Conclusion(s) in the Report Under Review | SECTION B |
| **6** | Appraisal Report Extraordinary Assumptions and/or Hypothetical Conditions | Standard (A) only |
| **7** | Review Report Extraordinary Assumptions and/or Hypothetical Conditions | Standard (A) only |
| **8** | Risk Assessment | SECTION F (SWOT Analysis) |
| **9** | Reviewer Findings, Opinions and Conclusions | SECTION E (Data Extraction) |
| **10** | Regional, Neighborhood, and Market Analysis | Standard (A) only |
| **11** | Subject Site and Improvements | Standard (A) only |
| **12** | Highest and Best Use | Standard (A) only |
| **13** | Site Valuation | SECTION D (2-dimensional evaluation) |
| **14** | Cost Approach | Standard (A) only |
| **15** | Sales Approach | Standard (A) only |
| **16** | Income Approach | Standard (A) + SECTION H (DCF) when applicable |
| **17** | Reconciliation | SECTION C |
| **18** | USPAP Compliance | Standard (A) only |
| **19** | FIRREA Compliance | Standard (A) only |
| **20** | Expanded Appraisal Insights | SECTION G (21 specialized questions Q1-Q21) |

### Section Details

#### SECTION B: Value Conclusions (Category 5)
- Specialized handling for "Value Conclusion(s) in the Report Under Review"
- Covers 17 value types (Market Value As Is, Prospective, Hypothetical, etc.)
- Property Rights Checklist (Fee Simple, Leased Fee, Leasehold, Other, N/A)
- Specific format for value extraction and transcription

#### SECTION C: Reconciliation (Category 17)
- SWOT-style evaluation of reconciliation
- Checks consistency between approaches (Sales, Income, Cost)
- Evaluates weighting reasonableness

#### SECTION D: Site Valuation (Category 13)
- 2-dimensional evaluation:
  1. Site Value Support
  2. Excess/Surplus Land
- Decision logic for Yes/No/N/A

#### SECTION E: Reviewer Findings (Category 9)
- 4 questions with data extraction + narrative:
  - Q1: Sales Comparison Approach
  - Q2: Income Approach
  - Q3: Cost Approach
  - Q4: Reconciliation (8-point criteria)

#### SECTION F: Risk Assessment (Category 8)
- Full SWOT Analysis format
- Property Risk Factors (Internal)
- Market Risk Factors (External)
- Overall Risk Assessment (Low/Moderate/High)

#### SECTION G: Expanded Appraisal Insights (Category 20)
- 21 specialized questions:
  - Q1: Non-Mathematical Narrative Consistency
  - Q2: Math Issues (Non-Metric)
  - Q3-Q17: 15 Metric QA Questions (GIM, GRM, EGIM, etc.)
  - Q18: Business Value / EBITDA Multiplier
  - Q19: Year of Construction & Remaining Economic Life
  - Q20: Discounted Cash Flow (DCF)
  - Q21: SBA Use, REL, and Approaches Review

#### SECTION H: DCF Analysis (Category 16 when applicable)
- DCF component extraction
- Mathematical verification
- Reasonableness analysis
- Market support evaluation

#### SECTION I: Property Information
- Property name extraction (with address fallback)
- Property address extraction (street number and name only)

---

## RLM Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           RLM ROOT CALL                                  │
│  Context Variable: Full appraisal document stored in REPL               │
│  Input: All questions grouped by category                                │
│                                                                          │
│  For each category group:                                                │
│    prompt = UNIVERSAL_SECTIONS + get_category_specific_section(category) │
│    answers[category] = llm_query(prompt + document + questions)          │
│                                                                          │
│  FINAL(aggregated_answers)                                               │
└─────────────────────────────────────────────────────────────────────────┘
```

### Per-Category Prompt Composition

```python
def build_prompt_for_category(category_id: int, questions: List[dict]) -> str:
    """
    Build a minimal prompt for a specific category.

    Args:
        category_id: The category ID (3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20)
        questions: List of questions in this category

    Returns:
        Composed prompt string with only relevant sections
    """
    # Start with universal sections
    prompt = UNIVERSAL_INTRO + UNIVERSAL_FORMATTING + SECTION_A_STANDARD

    # Add category-specific sections
    if category_id == 5:  # Value Conclusions
        prompt += SECTION_B
    elif category_id == 8:  # Risk Assessment
        prompt += SECTION_F_SWOT
    elif category_id == 9:  # Reviewer Findings
        prompt += SECTION_E_DATA_EXTRACTION
    elif category_id == 13:  # Site Valuation
        prompt += SECTION_D
    elif category_id == 17:  # Reconciliation
        prompt += SECTION_C
    elif category_id == 20:  # Expanded Insights
        # Could further optimize by including only relevant Q1-Q21 subsections
        prompt += SECTION_G
    elif category_id == 16:  # Income Approach
        # Check if any questions involve DCF
        if any_dcf_questions(questions):
            prompt += SECTION_H_DCF

    # Always include property info and critical instructions
    prompt += SECTION_I_PROPERTY_INFO + CRITICAL_INSTRUCTIONS

    return prompt
```

### RLM Wrapper Implementation

```python
from rlm import RLM

def process_appraisal_with_rlm(
    document: str,
    questions: List[dict],
    backend: str = "anthropic",
    model_name: str = "claude-sonnet-4-20250514"
) -> dict:
    """
    Process appraisal document using RLM with modular prompts.

    Args:
        document: Full appraisal document content
        questions: All questions with category metadata
        backend: LLM backend to use
        model_name: Model name

    Returns:
        Dictionary of all answers keyed by question_id
    """
    rlm = RLM(
        backend=backend,
        backend_kwargs={
            "model_name": model_name,
            "max_tokens": 32768
        },
        verbose=True,
    )

    # Group questions by category
    categories = group_questions_by_category(questions)

    # RLM system prompt to guide the processing
    system_prompt = f"""
You have access to a full appraisal document stored in the `context` variable.
You need to answer questions grouped by category.

For each category, I will provide:
1. A specialized prompt for that category
2. The questions to answer

Use llm_query_batched() to process categories in parallel for efficiency.

The document is: {{context}}

Process all {len(categories)} categories and return all answers in JSON format.
"""

    result = rlm.completion(system_prompt)
    return result.response
```

---

## Benefits of This Approach

| Aspect | Traditional | RLM Modular |
|--------|-------------|-------------|
| Document sent | 1x with all questions | Stored once in REPL, referenced per category |
| Response room | Very limited | Full response token limit per sub-call |
| Prompt size | ~50k+ tokens | ~5-15k tokens per category |
| Parallelism | None | Categories processed concurrently |
| Flexibility | Fixed | Can optimize per-category prompts |

---

## Next Steps

1. **Extract prompt sections** from `full_document_processor.py` into separate modules
2. **Implement prompt builder** function with category-to-section mapping
3. **Create RLM wrapper** script for appraisal processing
4. **Test with sample documents** and validate answer quality
5. **Integrate with existing system** (daemon/API)

---

## Files Reference

- **Source prompt:** `/Users/kehangchen/Documents/mountainseed/projects/review-manager/backend/shared/full_document_processor.py`
- **RLM project:** `/Users/kehangchen/Documents/mountainseed/projects/ai/rlm/`
- **Previous conversation:** `/Users/kehangchen/Documents/mountainseed/projects/ai/rlm/claude-code-history.md`
