"""
File Loader for RLM Appraisal Wrapper

This module provides functions to load documents and questions from files.
Supports:
- Markdown files (.md) for documents
- CSV files (.csv) for questions
- JSON files (.json) for questions
"""

import os
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QuestionData:
    """Represents a question loaded from file."""
    id: int
    text: str
    category_id: int
    category_name: str = ""
    use_llm: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "use_llm": self.use_llm,
        }


def load_markdown_document(file_path: Union[str, Path]) -> str:
    """
    Load a markdown document from file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Document content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not a markdown file
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Document file not found: {file_path}")

    if file_path.suffix.lower() not in ['.md', '.markdown', '.txt']:
        logger.warning(f"File {file_path} is not a .md file, loading anyway")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    logger.info(f"Loaded document from {file_path}: {len(content):,} characters")
    return content


def load_questions_from_csv(
    file_path: Union[str, Path],
    id_column: str = "id",
    text_column: str = "text",
    category_id_column: str = "category_id",
    category_name_column: Optional[str] = "category_name",
    use_llm_column: Optional[str] = "use_llm",
    delimiter: str = ",",
) -> List[QuestionData]:
    """
    Load questions from a CSV file.

    Expected CSV format:
    id,text,category_id[,category_name][,use_llm]
    1,"What is the property name?",3,"Appraisal Information",true
    2,"What is the property address?",3,"Appraisal Information",true
    ...

    Args:
        file_path: Path to the CSV file
        id_column: Column name for question ID
        text_column: Column name for question text
        category_id_column: Column name for category ID
        category_name_column: Optional column name for category name
        use_llm_column: Optional column name for use_llm flag
        delimiter: CSV delimiter (default: comma)

    Returns:
        List of QuestionData objects

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required columns are missing
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Questions file not found: {file_path}")

    questions = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        # Validate required columns
        fieldnames = reader.fieldnames or []
        required = [id_column, text_column, category_id_column]
        missing = [col for col in required if col not in fieldnames]
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Found: {fieldnames}")

        for row in reader:
            try:
                q_id = int(row[id_column])
                q_text = row[text_column].strip()
                cat_id = int(row[category_id_column])

                cat_name = ""
                if category_name_column and category_name_column in row:
                    cat_name = row[category_name_column].strip()

                use_llm = True
                if use_llm_column and use_llm_column in row:
                    use_llm_val = row[use_llm_column].strip().lower()
                    use_llm = use_llm_val in ['true', '1', 'yes', 'y', 't']  # 't' for PostgreSQL boolean

                questions.append(QuestionData(
                    id=q_id,
                    text=q_text,
                    category_id=cat_id,
                    category_name=cat_name,
                    use_llm=use_llm,
                ))
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid row: {row} - {e}")
                continue

    logger.info(f"Loaded {len(questions)} questions from {file_path}")
    return questions


def load_questions_from_json(
    file_path: Union[str, Path],
) -> List[QuestionData]:
    """
    Load questions from a JSON file.

    Expected JSON format:
    [
        {"id": 1, "text": "What is the property name?", "category_id": 3, "category_name": "Appraisal Information"},
        {"id": 2, "text": "What is the property address?", "category_id": 3},
        ...
    ]

    Or with a wrapper:
    {
        "questions": [
            {"id": 1, "text": "...", "category_id": 3},
            ...
        ]
    }

    Args:
        file_path: Path to the JSON file

    Returns:
        List of QuestionData objects

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON format is invalid
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Questions file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle both formats: direct list or wrapped in object
    if isinstance(data, dict):
        if "questions" in data:
            data = data["questions"]
        else:
            raise ValueError("JSON object must contain 'questions' key")

    if not isinstance(data, list):
        raise ValueError("JSON must be a list of questions or object with 'questions' key")

    questions = []
    for item in data:
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item: {item}")
            continue

        try:
            q_id = int(item.get("id") or item.get("question_id"))
            q_text = str(item.get("text") or item.get("question_text", "")).strip()
            cat_id = int(item.get("category_id", 0))

            if not q_text:
                logger.warning(f"Skipping question {q_id} with empty text")
                continue

            questions.append(QuestionData(
                id=q_id,
                text=q_text,
                category_id=cat_id,
                category_name=str(item.get("category_name", "")),
                use_llm=bool(item.get("use_llm", True)),
            ))
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping invalid item: {item} - {e}")
            continue

    logger.info(f"Loaded {len(questions)} questions from {file_path}")
    return questions


def load_questions(file_path: Union[str, Path]) -> List[QuestionData]:
    """
    Load questions from a file, auto-detecting format.

    Supports:
    - .csv files
    - .json files

    Args:
        file_path: Path to the questions file

    Returns:
        List of QuestionData objects

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == '.csv':
        return load_questions_from_csv(file_path)
    elif suffix == '.json':
        return load_questions_from_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .json")


def save_results_to_json(
    results: Dict[int, Dict[str, Any]],
    output_path: Union[str, Path],
    pretty: bool = True,
) -> None:
    """
    Save processing results to a JSON file.

    Args:
        results: Dictionary mapping question_id to answer data
        output_path: Path for output file
        pretty: Whether to format JSON with indentation
    """
    output_path = Path(output_path)

    # Convert to list format
    output_data = []
    for q_id, answer_data in sorted(results.items()):
        output_data.append({
            "question_id": q_id,
            **answer_data
        })

    with open(output_path, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(output_data, f, ensure_ascii=False)

    logger.info(f"Saved {len(output_data)} results to {output_path}")


def save_results_to_csv(
    results: Dict[int, Dict[str, Any]],
    output_path: Union[str, Path],
) -> None:
    """
    Save processing results to a CSV file.

    Args:
        results: Dictionary mapping question_id to answer data
        output_path: Path for output file
    """
    output_path = Path(output_path)

    if not results:
        logger.warning("No results to save")
        return

    # Determine fieldnames from first result
    sample = next(iter(results.values()))
    fieldnames = ["question_id"] + list(sample.keys())

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for q_id, answer_data in sorted(results.items()):
            row = {"question_id": q_id, **answer_data}
            writer.writerow(row)

    logger.info(f"Saved {len(results)} results to {output_path}")


# Convenience function for creating sample files
def create_sample_files(output_dir: Union[str, Path] = ".") -> Tuple[str, str]:
    """
    Create sample document and questions files for testing.

    Args:
        output_dir: Directory to create files in

    Returns:
        Tuple of (document_path, questions_path)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sample document
    doc_path = output_dir / "sample_document.md"
    doc_content = """# APPRAISAL REPORT

## Property Information

**Property Name:** Sample Commercial Property
**Property Address:** 123 Main Street
**City:** Anytown
**State:** CA
**Zip Code:** 90210

## Property Description

**Property Type:** Office Building
**Year Built:** 1995
**Gross Building Area:** 50,000 SF
**Net Rentable Area:** 45,000 SF
**Number of Stories:** 3

## Value Conclusions

### Market Value As Is

**Property Rights:** Fee Simple
**Effective Date:** January 1, 2026
**Market Value As Is:** $5,000,000

### Insurable Replacement Cost

**Property Rights:** N/A
**Effective Date:** January 1, 2026
**Insurable Replacement Cost:** $4,200,000

## Income Approach

The Income Approach was developed using Direct Capitalization.

**Potential Gross Income:** $600,000
**Vacancy & Collection Loss:** 5%
**Effective Gross Income:** $570,000
**Operating Expenses:** $190,000
**Net Operating Income:** $380,000
**Capitalization Rate:** 7.6%
**Indicated Value:** $5,000,000

## Sales Comparison Approach

Five comparable sales were analyzed:

| Sale | Price | Size (SF) | Price/SF |
|------|-------|-----------|----------|
| 1    | $4,500,000 | 48,000 | $93.75 |
| 2    | $5,200,000 | 52,000 | $100.00 |
| 3    | $4,800,000 | 50,000 | $96.00 |
| 4    | $5,500,000 | 55,000 | $100.00 |
| 5    | $4,700,000 | 47,000 | $100.00 |

**Adjusted Range:** $95.00 - $102.00/SF
**Indicated Value:** $5,000,000 ($100/SF x 50,000 SF)

## Reconciliation

The Sales Comparison and Income Approaches were given equal weight.
Final Reconciled Value: $5,000,000
"""

    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)

    # Sample questions (JSON)
    questions_path = output_dir / "sample_questions.json"
    questions_data = [
        {"id": 1, "text": "What is the property name of the subject property being appraised?", "category_id": 3, "category_name": "Appraisal Information"},
        {"id": 2, "text": "What is the property address (street number and street name)?", "category_id": 3, "category_name": "Appraisal Information"},
        {"id": 3, "text": "What is the city?", "category_id": 3, "category_name": "Appraisal Information"},
        {"id": 4, "text": "What is the state?", "category_id": 3, "category_name": "Appraisal Information"},
        {"id": 10, "text": "What are the Value Conclusion(s) in the Report Under Review?", "category_id": 5, "category_name": "Value Conclusions"},
        {"id": 50, "text": "Income Approach - What does the appraisal report state about the Income Approach?", "category_id": 9, "category_name": "Reviewer Findings"},
        {"id": 60, "text": "Sales Comparison Approach - What does the appraisal report state about the Sales Comparison Approach?", "category_id": 9, "category_name": "Reviewer Findings"},
        {"id": 100, "text": "The conclusions are consistent with the preceding individual sections?", "category_id": 17, "category_name": "Reconciliation"},
    ]

    with open(questions_path, 'w', encoding='utf-8') as f:
        json.dump(questions_data, f, indent=2)

    # Also create CSV version
    csv_path = output_dir / "sample_questions.csv"
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "category_id", "category_name"])
        writer.writeheader()
        for q in questions_data:
            writer.writerow(q)

    logger.info(f"Created sample files in {output_dir}")
    return str(doc_path), str(questions_path)
