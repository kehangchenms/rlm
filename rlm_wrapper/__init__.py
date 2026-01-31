"""
RLM Wrapper for Mountainseed Appraisal Review System

This package provides modular prompt construction and RLM-based processing
for appraisal document review with optimized token usage.

Usage:
    # Python API
    from rlm_wrapper import AppraisalProcessor, load_markdown_document, load_questions

    document = load_markdown_document("appraisal.md")
    questions = load_questions("questions.json")
    processor = AppraisalProcessor(backend="anthropic")
    result = processor.process(document, questions)

    # Command Line
    python -m rlm_wrapper.cli -d appraisal.md -q questions.json -o results.json
"""

from .prompt_builder import PromptBuilder, build_prompt_for_category, CATEGORY_NAMES
from .appraisal_processor import AppraisalProcessor, Question, Answer, ProcessingResult
from .file_loader import (
    load_markdown_document,
    load_questions,
    load_questions_from_csv,
    load_questions_from_json,
    save_results_to_json,
    save_results_to_csv,
    create_sample_files,
    QuestionData,
)

__all__ = [
    # Prompt building
    "PromptBuilder",
    "build_prompt_for_category",
    "CATEGORY_NAMES",
    # Processing
    "AppraisalProcessor",
    "Question",
    "Answer",
    "ProcessingResult",
    # File loading
    "load_markdown_document",
    "load_questions",
    "load_questions_from_csv",
    "load_questions_from_json",
    "save_results_to_json",
    "save_results_to_csv",
    "create_sample_files",
    "QuestionData",
]

__version__ = "0.1.0"
