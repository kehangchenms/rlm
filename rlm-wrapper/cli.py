#!/usr/bin/env python3
"""
Command Line Interface for RLM Appraisal Processor

Usage:
    python -m rlm_wrapper.cli --document doc.md --questions questions.json --output results.json
    python -m rlm_wrapper.cli -d doc.md -q questions.csv -o results.json --backend anthropic
    python -m rlm_wrapper.cli --create-samples  # Create sample input files
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rlm_wrapper.file_loader import (
    load_markdown_document,
    load_questions,
    save_results_to_json,
    save_results_to_csv,
    create_sample_files,
    QuestionData,
)
from rlm_wrapper.appraisal_processor import AppraisalProcessor, Question
from rlm_wrapper.prompt_builder import get_prompt_size_comparison, CATEGORY_NAMES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="RLM Appraisal Processor - Process appraisal documents with modular prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a document with questions
  python -m rlm_wrapper.cli -d appraisal.md -q questions.json -o results.json

  # Use OpenAI instead of Anthropic
  python -m rlm_wrapper.cli -d doc.md -q questions.csv --backend openai --model gpt-4

  # Create sample input files for testing
  python -m rlm_wrapper.cli --create-samples

  # Show prompt sizes for each category
  python -m rlm_wrapper.cli --show-prompts

  # Dry run (no LLM calls, just show what would be processed)
  python -m rlm_wrapper.cli -d doc.md -q questions.json --dry-run
        """
    )

    # Input/Output options
    parser.add_argument(
        '-d', '--document',
        type=str,
        help='Path to markdown document file (.md)'
    )
    parser.add_argument(
        '-q', '--questions',
        type=str,
        help='Path to questions file (.json or .csv)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='results.json',
        help='Path for output file (default: results.json)'
    )
    parser.add_argument(
        '--output-format',
        choices=['json', 'csv'],
        default='json',
        help='Output format (default: json)'
    )

    # LLM options
    parser.add_argument(
        '--backend',
        type=str,
        default='anthropic',
        choices=['anthropic', 'openai'],
        help='LLM backend to use (default: anthropic)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Model name (default: claude-sonnet-4-20250514 for Anthropic)'
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=32768,
        help='Maximum response tokens (default: 32768)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='API key (or set ANTHROPIC_API_KEY/OPENAI_API_KEY env var)'
    )

    # Processing options
    parser.add_argument(
        '--use-rlm',
        action='store_true',
        default=False,
        help='Use RLM for processing (requires rlm package)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without making LLM calls'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    # Utility options
    parser.add_argument(
        '--create-samples',
        action='store_true',
        help='Create sample document and questions files'
    )
    parser.add_argument(
        '--samples-dir',
        type=str,
        default='./samples',
        help='Directory for sample files (default: ./samples)'
    )
    parser.add_argument(
        '--show-prompts',
        action='store_true',
        help='Show prompt sizes for each category'
    )
    parser.add_argument(
        '--show-categories',
        action='store_true',
        help='Show available categories'
    )

    return parser.parse_args()


def get_default_model(backend: str) -> str:
    """Get default model for a backend."""
    defaults = {
        'anthropic': 'claude-sonnet-4-20250514',
        'openai': 'gpt-4-turbo-preview',
    }
    return defaults.get(backend, 'claude-sonnet-4-20250514')


def show_prompt_sizes():
    """Display prompt sizes for each category."""
    print("\n" + "=" * 60)
    print("PROMPT SIZES BY CATEGORY")
    print("=" * 60)

    sizes = get_prompt_size_comparison()

    total = 0
    for cat_name, tokens in sorted(sizes.items()):
        print(f"  {cat_name}")
        print(f"    -> ~{tokens:,} tokens")
        total += tokens

    print("-" * 60)
    print(f"  Total (all categories): ~{total:,} tokens")
    print(f"  Average per category: ~{total // len(sizes):,} tokens")
    print("=" * 60)


def show_categories():
    """Display available categories."""
    print("\n" + "=" * 60)
    print("AVAILABLE CATEGORIES")
    print("=" * 60)

    for cat_id, cat_name in sorted(CATEGORY_NAMES.items()):
        print(f"  {cat_id:2d}. {cat_name}")

    print("=" * 60)


def do_dry_run(document_path: str, questions_path: str):
    """Perform a dry run showing what would be processed."""
    print("\n" + "=" * 60)
    print("DRY RUN - No LLM calls will be made")
    print("=" * 60)

    # Load document
    print(f"\nDocument: {document_path}")
    try:
        doc = load_markdown_document(document_path)
        doc_tokens = len(doc) // 4
        print(f"  Size: {len(doc):,} characters (~{doc_tokens:,} tokens)")
    except Exception as e:
        print(f"  ERROR: {e}")
        return

    # Load questions
    print(f"\nQuestions: {questions_path}")
    try:
        questions = load_questions(questions_path)
        print(f"  Loaded: {len(questions)} questions")
    except Exception as e:
        print(f"  ERROR: {e}")
        return

    # Group by category
    from rlm_wrapper.prompt_builder import PromptBuilder

    builder = PromptBuilder()
    groups = {}
    for q in questions:
        if q.category_id not in groups:
            groups[q.category_id] = []
        groups[q.category_id].append(q)

    print(f"\nCategories to process: {len(groups)}")
    print("-" * 40)

    total_prompt_tokens = 0
    for cat_id, cat_questions in sorted(groups.items()):
        cat_name = CATEGORY_NAMES.get(cat_id, f"Category {cat_id}")
        prompt = builder.build_prompt(cat_id)
        prompt_tokens = len(prompt) // 4

        print(f"\n  {cat_id}. {cat_name}")
        print(f"     Questions: {len(cat_questions)}")
        print(f"     Prompt tokens: ~{prompt_tokens:,}")

        for q in cat_questions[:3]:  # Show first 3 questions
            print(f"       - Q{q.id}: {q.text[:50]}...")
        if len(cat_questions) > 3:
            print(f"       ... and {len(cat_questions) - 3} more")

        total_prompt_tokens += prompt_tokens

    print("\n" + "-" * 40)
    print(f"Total prompt tokens (all categories): ~{total_prompt_tokens:,}")
    print(f"Document tokens: ~{doc_tokens:,}")
    print(f"Estimated total input: ~{total_prompt_tokens + doc_tokens * len(groups):,} tokens")
    print("=" * 60)


def process_files(args):
    """Process document and questions files."""
    # Validate inputs
    if not args.document:
        print("ERROR: --document is required")
        sys.exit(1)
    if not args.questions:
        print("ERROR: --questions is required")
        sys.exit(1)

    # Dry run mode
    if args.dry_run:
        do_dry_run(args.document, args.questions)
        return

    # Load document
    print(f"\nLoading document: {args.document}")
    try:
        document = load_markdown_document(args.document)
        print(f"  Loaded {len(document):,} characters")
    except Exception as e:
        print(f"ERROR loading document: {e}")
        sys.exit(1)

    # Load questions
    print(f"\nLoading questions: {args.questions}")
    try:
        question_data = load_questions(args.questions)
        print(f"  Loaded {len(question_data)} questions")
    except Exception as e:
        print(f"ERROR loading questions: {e}")
        sys.exit(1)

    # Convert to Question objects
    questions = [
        Question(
            id=q.id,
            text=q.text,
            category_id=q.category_id,
            category_name=q.category_name,
            use_llm=q.use_llm,
        )
        for q in question_data
        if q.use_llm
    ]

    print(f"  {len(questions)} questions will be processed")

    # Get model
    model = args.model or get_default_model(args.backend)

    # Create processor
    print(f"\nInitializing processor...")
    print(f"  Backend: {args.backend}")
    print(f"  Model: {model}")
    print(f"  Max tokens: {args.max_tokens}")
    print(f"  Use RLM: {args.use_rlm}")

    try:
        processor = AppraisalProcessor(
            backend=args.backend,
            model_name=model,
            max_tokens=args.max_tokens,
            api_key=args.api_key,
            verbose=args.verbose,
            use_rlm=args.use_rlm,
        )
    except Exception as e:
        print(f"ERROR initializing processor: {e}")
        sys.exit(1)

    # Process
    print(f"\nProcessing {len(questions)} questions...")
    try:
        result = processor.process(document, questions)
    except Exception as e:
        print(f"ERROR during processing: {e}")
        sys.exit(1)

    # Report results
    print(f"\nProcessing complete!")
    print(f"  Answers: {len(result.answers)}")
    print(f"  Errors: {len(result.errors)}")

    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    # Save results
    output_path = args.output
    print(f"\nSaving results to: {output_path}")

    try:
        # Convert Answer objects to dicts
        results_dict = {}
        for q_id, answer in result.answers.items():
            results_dict[q_id] = {
                "answer": answer.answer,
                "transcription": answer.transcription,
                "traffic_light_rating": answer.traffic_light_rating,
            }

        if args.output_format == 'csv':
            save_results_to_csv(results_dict, output_path)
        else:
            save_results_to_json(results_dict, output_path)

        print(f"  Saved {len(results_dict)} results")
    except Exception as e:
        print(f"ERROR saving results: {e}")
        sys.exit(1)

    print("\nDone!")


def main():
    """Main entry point."""
    args = parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle utility commands
    if args.create_samples:
        print(f"\nCreating sample files in: {args.samples_dir}")
        doc_path, questions_path = create_sample_files(args.samples_dir)
        print(f"\nCreated:")
        print(f"  Document: {doc_path}")
        print(f"  Questions (JSON): {questions_path}")
        print(f"  Questions (CSV): {questions_path.replace('.json', '.csv')}")
        print(f"\nTo process these samples:")
        print(f"  python -m rlm_wrapper.cli -d {doc_path} -q {questions_path} -o results.json")
        return

    if args.show_prompts:
        show_prompt_sizes()
        return

    if args.show_categories:
        show_categories()
        return

    # Process files
    if args.document or args.questions:
        process_files(args)
    else:
        print("No action specified. Use --help for usage information.")
        print("\nQuick start:")
        print("  python -m rlm_wrapper.cli --create-samples  # Create sample files")
        print("  python -m rlm_wrapper.cli -d doc.md -q questions.json -o results.json")


if __name__ == "__main__":
    main()
