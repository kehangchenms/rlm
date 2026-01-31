# RLM Appraisal Wrapper

A modular prompt system for processing appraisal documents using RLM (Recursive Language Models) with optimized token usage.

## Overview

This wrapper solves the **response token limit problem** when processing appraisal documents with many questions. Instead of sending one massive prompt with all questions, it:

1. **Groups questions by category** (16 predefined categories)
2. **Builds optimized prompts** with only relevant sections per category
3. **Processes each category separately** with full response token capacity
4. **Aggregates results** into a unified output

### Token Savings

| Approach | Tokens per Category | Total for 16 Categories |
|----------|--------------------:|------------------------:|
| Monolithic (all sections) | ~12,000 | ~192,000 |
| Modular (relevant only) | ~3,000-8,000 | ~80,000 |
| **Savings** | | **~58%** |

## Installation

### Prerequisites

- Python 3.10 or higher
- Conda or pip for package management

### Step 1: Clone/Navigate to the Project

```bash
cd /path/to/rlm
```

### Step 2: Create Environment (Conda)

```bash
conda create -n rlm_wrapper python=3.12 -y
conda activate rlm_wrapper
```

Or with venv:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Install the base rlm package
pip install -e .

# Install additional dependencies for the wrapper
pip install anthropic  # For Anthropic/Claude API
pip install openai     # For OpenAI API (optional)
```

### Step 4: Set API Keys

```bash
# For Anthropic (default)
export ANTHROPIC_API_KEY=your_anthropic_api_key

# For OpenAI (optional)
export OPENAI_API_KEY=your_openai_api_key
```

On Windows:
```cmd
set ANTHROPIC_API_KEY=your_anthropic_api_key
```

## Quick Start

### 1. Create Sample Files

```bash
python -m rlm_wrapper.cli --create-samples
```

This creates:
- `samples/sample_document.md` - A sample appraisal document
- `samples/sample_questions.json` - Sample questions in JSON format
- `samples/sample_questions.csv` - Sample questions in CSV format

### 2. Dry Run (No LLM Calls)

```bash
python -m rlm_wrapper.cli \
  -d samples/sample_document.md \
  -q samples/sample_questions.json \
  --dry-run
```

### 3. Process with LLM

```bash
python -m rlm_wrapper.cli \
  -d samples/sample_document.md \
  -q samples/sample_questions.json \
  -o results.json
```

## File Formats

### Document (Markdown)

Any `.md`, `.markdown`, or `.txt` file containing the appraisal document text.

```markdown
# APPRAISAL REPORT

## Property Information
**Property Name:** Sample Commercial Property
**Property Address:** 123 Main Street
...
```

### Questions (JSON)

```json
[
  {
    "id": 1,
    "text": "What is the property name of the subject property being appraised?",
    "category_id": 3,
    "category_name": "Appraisal Information"
  },
  {
    "id": 10,
    "text": "What are the Value Conclusion(s) in the Report Under Review?",
    "category_id": 5,
    "category_name": "Value Conclusions"
  }
]
```

Required fields:
- `id` (or `question_id`): Unique question identifier
- `text` (or `question_text`): The question text
- `category_id`: Category ID (see Categories below)

Optional fields:
- `category_name`: Human-readable category name
- `use_llm`: Boolean, whether to process with LLM (default: true)

### Questions (CSV)

```csv
id,text,category_id,category_name
1,"What is the property name?",3,"Appraisal Information"
2,"What is the property address?",3,"Appraisal Information"
10,"What are the Value Conclusions?",5,"Value Conclusions"
```

## CLI Reference

```bash
python -m rlm_wrapper.cli [OPTIONS]
```

### Input/Output Options

| Option | Description |
|--------|-------------|
| `-d, --document FILE` | Path to markdown document file |
| `-q, --questions FILE` | Path to questions file (.json or .csv) |
| `-o, --output FILE` | Output file path (default: results.json) |
| `--output-format {json,csv}` | Output format (default: json) |

### LLM Options

| Option | Description |
|--------|-------------|
| `--backend {anthropic,openai}` | LLM backend (default: anthropic) |
| `--model NAME` | Model name (default: claude-sonnet-4-20250514) |
| `--max-tokens N` | Max response tokens (default: 32768) |
| `--api-key KEY` | API key (or use environment variable) |
| `--use-rlm` | Use RLM for processing (requires rlm package) |

### Utility Options

| Option | Description |
|--------|-------------|
| `--create-samples` | Create sample document and questions files |
| `--samples-dir DIR` | Directory for samples (default: ./samples) |
| `--show-prompts` | Show prompt sizes for each category |
| `--show-categories` | List all available categories |
| `--dry-run` | Show what would be processed without LLM calls |
| `-v, --verbose` | Enable verbose output |

### Examples

```bash
# Process with Anthropic Claude
python -m rlm_wrapper.cli -d doc.md -q questions.json -o results.json

# Process with OpenAI GPT-4
python -m rlm_wrapper.cli -d doc.md -q questions.csv \
  --backend openai --model gpt-4-turbo-preview

# Output as CSV
python -m rlm_wrapper.cli -d doc.md -q questions.json \
  -o results.csv --output-format csv

# Verbose mode with custom max tokens
python -m rlm_wrapper.cli -d doc.md -q questions.json \
  --max-tokens 16384 --verbose
```

## Python API

### Basic Usage

```python
from rlm_wrapper import (
    AppraisalProcessor,
    Question,
    load_markdown_document,
    load_questions,
)

# Load from files
document = load_markdown_document("appraisal.md")
questions_data = load_questions("questions.json")

# Convert to Question objects
questions = [
    Question(
        id=q.id,
        text=q.text,
        category_id=q.category_id,
        category_name=q.category_name,
    )
    for q in questions_data
]

# Create processor
processor = AppraisalProcessor(
    backend="anthropic",
    model_name="claude-sonnet-4-20250514",
    max_tokens=32768,
    verbose=True,
)

# Process
result = processor.process(document, questions)

# Access results
for q_id, answer in result.answers.items():
    print(f"Q{q_id}: {answer.transcription}")
    print(f"  Traffic Light: {answer.traffic_light_rating}")
```

### Using the Prompt Builder Directly

```python
from rlm_wrapper import PromptBuilder, build_prompt_for_category

# Build prompt for a specific category
prompt = build_prompt_for_category(category_id=8)  # Risk Assessment
print(f"Prompt size: {len(prompt)} characters")

# Or use the builder class
builder = PromptBuilder()
prompt = builder.build_prompt(category_id=5)  # Value Conclusions
tokens = builder.estimate_tokens(prompt)
print(f"Estimated tokens: {tokens}")
```

### Saving Results

```python
from rlm_wrapper import save_results_to_json, save_results_to_csv

# Convert answers to dict format
results_dict = {
    q_id: {
        "answer": ans.answer,
        "transcription": ans.transcription,
        "traffic_light_rating": ans.traffic_light_rating,
    }
    for q_id, ans in result.answers.items()
}

# Save as JSON
save_results_to_json(results_dict, "results.json")

# Save as CSV
save_results_to_csv(results_dict, "results.csv")
```

## Categories

The system supports 16 question categories:

| ID | Category Name | Specific Prompt Section |
|----|---------------|------------------------|
| 3 | Appraisal Information | Standard (A) |
| 5 | Value Conclusion(s) in the Report Under Review | Section B |
| 6 | Appraisal Report Extraordinary Assumptions/Hypothetical Conditions | Standard (A) |
| 7 | Review Report Extraordinary Assumptions/Hypothetical Conditions | Standard (A) |
| 8 | Risk Assessment | Section F (SWOT) |
| 9 | Reviewer Findings, Opinions and Conclusions | Section E |
| 10 | Regional, Neighborhood, and Market Analysis | Standard (A) |
| 11 | Subject Site and Improvements | Standard (A) |
| 12 | Highest and Best Use | Standard (A) |
| 13 | Site Valuation | Section D |
| 14 | Cost Approach | Standard (A) |
| 15 | Sales Approach | Standard (A) |
| 16 | Income Approach | Standard (A) + Section H (DCF) |
| 17 | Reconciliation | Section C |
| 18 | USPAP Compliance | Standard (A) |
| 19 | FIRREA Compliance | Standard (A) |
| 20 | Expanded Appraisal Insights | Section G (Q1-Q21) |

## Project Structure

```
rlm_wrapper/
├── __init__.py                    # Package exports
├── appraisal_processor.py         # Main processor class
├── prompt_builder.py              # Builds category-specific prompts
├── file_loader.py                 # Load documents & questions from files
├── cli.py                         # Command-line interface
├── utils.py                       # Utility functions
├── example_usage.py               # Demo script
├── README.md                      # This file
└── prompts/
    ├── __init__.py                # Prompt exports
    ├── universal.py               # Universal sections (all categories)
    ├── section_b_value.py         # Category 5 - Value Conclusions
    ├── section_c_reconciliation.py # Category 17 - Reconciliation
    ├── section_d_site.py          # Category 13 - Site Valuation
    ├── section_e_findings.py      # Category 9 - Reviewer Findings
    ├── section_f_risk.py          # Category 8 - Risk Assessment (SWOT)
    ├── section_g_expanded.py      # Category 20 - Expanded Insights
    ├── section_h_dcf.py           # Category 16 - DCF Analysis
    └── section_i_property.py      # Property Information
```

## Output Format

### JSON Output

```json
[
  {
    "question_id": 1,
    "answer": "The property name is Sample Commercial Property, as stated on page 1...",
    "transcription": "Sample Commercial Property",
    "traffic_light_rating": "Green"
  },
  {
    "question_id": 2,
    "answer": "The property address is 123 Main Street [Page 1]...",
    "transcription": "123 Main Street",
    "traffic_light_rating": "Green"
  }
]
```

### CSV Output

```csv
question_id,answer,transcription,traffic_light_rating
1,"The property name is...",Sample Commercial Property,Green
2,"The property address is...",123 Main Street,Green
```

## Running the Demo

```bash
# Run all demos
python -m rlm_wrapper.example_usage

# Or from the rlm_wrapper directory
cd rlm_wrapper
python example_usage.py
```

The demo will show:
1. Prompt sizes for each category
2. Sample question grouping
3. File loading examples
4. CLI usage examples

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running from the correct directory:

```bash
cd /path/to/rlm
python -m rlm_wrapper.cli --help
```

### API Key Issues

Ensure your API key is set:

```bash
# Check if set
echo $ANTHROPIC_API_KEY

# Set it
export ANTHROPIC_API_KEY=sk-ant-...
```

### Missing Dependencies

```bash
pip install anthropic openai
```

### RLM Not Found

The `--use-rlm` flag requires the rlm package:

```bash
pip install -e .  # From the rlm project root
```

## License

See the main project LICENSE file.

## Related Documentation

- [Design Document](../kc-design/2026-01-29_rlm-modular-prompt-design.md) - Detailed design and architecture
- [RLM Project README](../README.md) - Main RLM project documentation
