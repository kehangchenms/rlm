#!/usr/bin/env python3
"""
Example usage of the RLM Appraisal Processor.

This script demonstrates how to use the modular prompt system
for processing appraisal documents.

Examples:
    # Run all demos
    python -m rlm_wrapper.example_usage

    # Or run from the rlm-wrapper directory
    python example_usage.py
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))


def demo_prompt_builder():
    """Demonstrate the prompt builder and show token savings."""
    from prompt_builder import (
        PromptBuilder,
        build_prompt_for_category,
        get_prompt_size_comparison,
        CATEGORY_NAMES,
    )

    print("=" * 70)
    print("PROMPT BUILDER DEMO")
    print("=" * 70)

    # Get prompt sizes for all categories
    sizes = get_prompt_size_comparison()

    print("\nEstimated tokens per category prompt:")
    print("-" * 50)

    total_modular = 0
    for cat_name, tokens in sorted(sizes.items()):
        print(f"  {cat_name}: ~{tokens:,} tokens")
        total_modular += tokens

    # Compare with monolithic
    builder = PromptBuilder()
    full_prompt = builder.get_universal_sections()

    # Add ALL category-specific sections for comparison
    from prompts import (
        SECTION_B_VALUE_CONCLUSIONS,
        SECTION_C_RECONCILIATION,
        SECTION_D_SITE_VALUATION,
        SECTION_E_REVIEWER_FINDINGS,
        SECTION_F_RISK_ASSESSMENT,
        SECTION_G_EXPANDED_INSIGHTS,
        SECTION_H_DCF_ANALYSIS,
        SECTION_I_PROPERTY_INFO,
        CRITICAL_INSTRUCTIONS,
    )

    monolithic = (
        full_prompt +
        SECTION_B_VALUE_CONCLUSIONS +
        SECTION_C_RECONCILIATION +
        SECTION_D_SITE_VALUATION +
        SECTION_E_REVIEWER_FINDINGS +
        SECTION_F_RISK_ASSESSMENT +
        SECTION_G_EXPANDED_INSIGHTS +
        SECTION_H_DCF_ANALYSIS +
        SECTION_I_PROPERTY_INFO +
        CRITICAL_INSTRUCTIONS
    )

    monolithic_tokens = builder.estimate_tokens(monolithic)

    print("\n" + "-" * 50)
    print(f"Monolithic prompt (all sections): ~{monolithic_tokens:,} tokens")
    print(f"Sum of modular prompts: ~{total_modular:,} tokens")
    print(f"Average per category: ~{total_modular // len(sizes):,} tokens")

    # If processing all categories separately with monolithic
    all_with_monolithic = monolithic_tokens * len(sizes)
    savings = all_with_monolithic - total_modular
    savings_pct = (savings / all_with_monolithic * 100) if all_with_monolithic > 0 else 0

    print(f"\nIf processing {len(sizes)} categories:")
    print(f"  With monolithic prompt: ~{all_with_monolithic:,} total tokens")
    print(f"  With modular prompts: ~{total_modular:,} total tokens")
    print(f"  Savings: ~{savings:,} tokens ({savings_pct:.1f}%)")


def demo_sample_questions():
    """Demonstrate processing with sample questions."""
    from appraisal_processor import AppraisalProcessor, Question

    print("\n" + "=" * 70)
    print("SAMPLE QUESTIONS DEMO")
    print("=" * 70)

    # Create sample questions for different categories
    sample_questions = [
        # Category 3: Appraisal Information
        Question(id=1, text="What is the property name of the subject property being appraised?",
                 category_id=3, category_name="Appraisal Information"),
        Question(id=2, text="What is the property address (street number and street name)?",
                 category_id=3, category_name="Appraisal Information"),

        # Category 5: Value Conclusions
        Question(id=10, text="What are the Value Conclusion(s) in the Report Under Review?",
                 category_id=5, category_name="Value Conclusion(s)"),

        # Category 8: Risk Assessment
        Question(id=50, text="Provide comments or observations regarding the overall risk assessment in SWOT analysis format.",
                 category_id=8, category_name="Risk Assessment"),

        # Category 9: Reviewer Findings
        Question(id=60, text="Sales Comparison Approach - What does the appraisal report state about the Sales Comparison Approach?",
                 category_id=9, category_name="Reviewer Findings"),

        # Category 17: Reconciliation
        Question(id=100, text="The conclusions are consistent with the preceding individual sections?",
                 category_id=17, category_name="Reconciliation"),
    ]

    print(f"\nSample questions ({len(sample_questions)} total):")
    for q in sample_questions:
        print(f"  [{q.category_id}] Q{q.id}: {q.text[:60]}...")

    # Create processor (dry run - won't actually call LLM)
    processor = AppraisalProcessor(
        backend="anthropic",
        model_name="claude-sonnet-4-20250514",
        verbose=True,
        use_rlm=False,  # Set to True when you have RLM installed
    )

    # Group questions
    groups = processor.group_questions_by_category(sample_questions)

    print(f"\nGrouped into {len(groups)} categories:")
    for cat_id, questions in groups.items():
        cat_name = CATEGORY_NAMES.get(cat_id, f"Category {cat_id}")
        print(f"  {cat_id}. {cat_name}: {len(questions)} questions")

        # Show the prompt that would be used
        prompt = processor.prompt_builder.build_prompt(cat_id)
        tokens = processor.prompt_builder.estimate_tokens(prompt)
        print(f"     -> Prompt size: ~{tokens:,} tokens")


def demo_full_processing():
    """
    Demonstrate full processing with a sample document.

    Note: This requires API keys and will make actual LLM calls.
    """
    from appraisal_processor import AppraisalProcessor, Question

    print("\n" + "=" * 70)
    print("FULL PROCESSING DEMO (requires API key)")
    print("=" * 70)

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nSkipping: ANTHROPIC_API_KEY not set")
        print("Set the environment variable to run this demo:")
        print("  export ANTHROPIC_API_KEY=your_key_here")
        return

    # Sample document (in real use, this would be the full appraisal)
    sample_document = """
    APPRAISAL REPORT

    Property Name: Sample Commercial Property
    Property Address: 123 Main Street
    City: Anytown
    State: CA
    Zip: 90210

    Property Type: Office Building
    Year Built: 1995
    Gross Building Area: 50,000 SF

    Market Value As Is: $5,000,000
    Effective Date: January 1, 2026

    [This is a sample document for demonstration purposes]
    """

    # Create sample questions
    questions = [
        Question(id=1, text="What is the property name of the subject property being appraised?",
                 category_id=3),
        Question(id=2, text="What is the property address?",
                 category_id=3),
    ]

    # Create processor
    processor = AppraisalProcessor(
        backend="anthropic",
        model_name="claude-sonnet-4-20250514",
        verbose=True,
        use_rlm=False,  # Direct API calls for demo
    )

    print(f"\nProcessing {len(questions)} questions...")

    try:
        result = processor.process(sample_document, questions)

        print(f"\nResults:")
        print(f"  Answers: {len(result.answers)}")
        print(f"  Errors: {len(result.errors)}")

        for q_id, answer in result.answers.items():
            print(f"\n  Question {q_id}:")
            print(f"    Answer: {answer.answer[:100]}...")
            print(f"    Transcription: {answer.transcription}")
            print(f"    Traffic Light: {answer.traffic_light_rating}")

    except Exception as e:
        print(f"\nError during processing: {e}")


# Import CATEGORY_NAMES at module level for use in functions
try:
    from prompt_builder import CATEGORY_NAMES
except ImportError:
    CATEGORY_NAMES = {}


def demo_file_inputs():
    """Demonstrate loading documents and questions from files."""
    from file_loader import (
        create_sample_files,
        load_markdown_document,
        load_questions,
    )
    from appraisal_processor import AppraisalProcessor, Question

    print("\n" + "=" * 70)
    print("FILE INPUT DEMO")
    print("=" * 70)

    # Create sample files
    samples_dir = Path(__file__).parent / "samples"
    print(f"\nCreating sample files in: {samples_dir}")

    doc_path, questions_path = create_sample_files(samples_dir)
    print(f"  Document: {doc_path}")
    print(f"  Questions: {questions_path}")

    # Load document
    print(f"\nLoading document from: {doc_path}")
    document = load_markdown_document(doc_path)
    print(f"  Loaded {len(document):,} characters")

    # Load questions (JSON)
    print(f"\nLoading questions from: {questions_path}")
    questions_data = load_questions(questions_path)
    print(f"  Loaded {len(questions_data)} questions")

    # Show loaded questions
    print("\nQuestions loaded:")
    for q in questions_data:
        print(f"  [{q.category_id}] Q{q.id}: {q.text[:50]}...")

    # Also try CSV
    csv_path = questions_path.replace('.json', '.csv')
    print(f"\nLoading questions from CSV: {csv_path}")
    questions_csv = load_questions(csv_path)
    print(f"  Loaded {len(questions_csv)} questions from CSV")

    # Convert to Question objects for processing
    questions = [
        Question(
            id=q.id,
            text=q.text,
            category_id=q.category_id,
            category_name=q.category_name,
        )
        for q in questions_data
    ]

    # Create processor and group
    processor = AppraisalProcessor(verbose=False, use_rlm=False)
    groups = processor.group_questions_by_category(questions)

    print(f"\nGrouped into {len(groups)} categories:")
    for cat_id, cat_questions in groups.items():
        cat_name = CATEGORY_NAMES.get(cat_id, f"Category {cat_id}")
        prompt = processor.prompt_builder.build_prompt(cat_id)
        tokens = processor.prompt_builder.estimate_tokens(prompt)
        print(f"  {cat_id}. {cat_name}: {len(cat_questions)} questions (~{tokens:,} prompt tokens)")

    print("\nTo process with LLM, run:")
    print(f"  python -m rlm_wrapper.cli -d {doc_path} -q {questions_path} -o results.json")


def demo_cli_usage():
    """Show CLI usage examples."""
    print("\n" + "=" * 70)
    print("CLI USAGE EXAMPLES")
    print("=" * 70)

    print("""
# Create sample input files
python -m rlm_wrapper.cli --create-samples

# Show available categories
python -m rlm_wrapper.cli --show-categories

# Show prompt sizes for each category
python -m rlm_wrapper.cli --show-prompts

# Dry run (no LLM calls, shows what would be processed)
python -m rlm_wrapper.cli -d document.md -q questions.json --dry-run

# Process with Anthropic (default)
python -m rlm_wrapper.cli -d document.md -q questions.json -o results.json

# Process with OpenAI
python -m rlm_wrapper.cli -d document.md -q questions.csv --backend openai --model gpt-4

# Process with RLM enabled
python -m rlm_wrapper.cli -d document.md -q questions.json --use-rlm

# Output as CSV instead of JSON
python -m rlm_wrapper.cli -d document.md -q questions.json -o results.csv --output-format csv
""")


if __name__ == "__main__":
    print("\nRLM Appraisal Wrapper - Example Usage\n")

    # Run demos
    demo_prompt_builder()
    demo_sample_questions()
    demo_file_inputs()
    demo_cli_usage()

    # Uncomment to run full processing demo (requires API key)
    # demo_full_processing()

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)
