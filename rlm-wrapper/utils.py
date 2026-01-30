"""
Utility functions for the RLM Appraisal Wrapper.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def estimate_token_count(text: str, use_tiktoken: bool = False) -> int:
    """
    Estimate token count for a text.

    Args:
        text: The text to estimate tokens for
        use_tiktoken: Whether to use tiktoken for more accurate counting

    Returns:
        Estimated token count
    """
    if use_tiktoken:
        try:
            import tiktoken
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except ImportError:
            logger.warning("tiktoken not installed, using character-based estimation")
        except Exception as e:
            logger.warning(f"Error using tiktoken: {e}")

    # Fallback: ~4 characters per token for English text
    return len(text) // 4


def remove_page_references(text: str) -> str:
    """
    Remove page references from transcription text.

    Removes patterns like [Page 1], (Page 1-2), page 1, etc.

    Args:
        text: The text to clean

    Returns:
        Text with page references removed
    """
    if not text:
        return text

    patterns = [
        r'\[Pages?\s*[\d,\s\-]+\]',
        r'\(Pages?\s*[\d,\s\-]+\)',
        r'\[pp?\.?\s*[\d,\s\-]+\]',
        r'\(pp?\.?\s*[\d,\s\-]+\)',
        r'(?<![\w])pages?\s+[\d,\s\-]+(?![\w])',
        r'(?<![\w])pp?\.?\s*[\d,\s\-]+(?![\w])',
    ]

    result = text
    for pattern in patterns:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)

    # Clean up extra whitespace
    result = re.sub(r'\s{2,}', ' ', result).strip()

    return result


def clean_markdown(text: str) -> str:
    """
    Remove Markdown formatting from text.

    Args:
        text: Text potentially containing Markdown

    Returns:
        Clean plain text
    """
    if not text:
        return text

    # Remove bold, italic, headers
    text = re.sub(r"\*\*|\*|__|_|##|#", "", text)
    return text.strip()


def normalize_traffic_light(rating: Optional[str]) -> Optional[str]:
    """
    Normalize traffic light rating to standard format.

    Args:
        rating: Raw traffic light rating

    Returns:
        Normalized rating (Green, Yellow, Red, or N/A)
    """
    if not rating:
        return None

    rating_lower = rating.lower().strip()

    if rating_lower in ['n/a', 'na', 'not applicable']:
        return 'N/A'
    elif rating_lower == 'red':
        return 'Red'
    elif rating_lower == 'yellow':
        return 'Yellow'
    elif rating_lower == 'green':
        return 'Green'

    return rating


def parse_json_response(
    response_text: str,
    valid_question_ids: Optional[set] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Parse a JSON array response from LLM.

    Attempts to repair truncated JSON if needed.

    Args:
        response_text: Raw response text
        valid_question_ids: Optional set of valid question IDs

    Returns:
        List of parsed answer dictionaries, or None if parsing fails
    """
    # Find JSON array
    json_start = response_text.find('[')
    if json_start == -1:
        return None

    json_end = response_text.rfind(']')

    # Extract JSON text
    json_text = response_text[json_start:] if json_end == -1 else response_text[json_start:json_end + 1]

    # Try to parse
    parsed_data = None
    try:
        parsed_data = json.loads(json_text)
    except json.JSONDecodeError:
        # Try to repair truncated JSON
        logger.debug("Initial JSON parse failed, attempting repair")

        last_brace = json_text.rfind('}')
        last_bracket = json_text.rfind(']')

        if last_brace != -1 and last_brace > last_bracket:
            # Try completing the array
            repaired = json_text[:last_brace + 1] + ']'
            try:
                parsed_data = json.loads(repaired)
                logger.info("Successfully repaired truncated JSON")
            except json.JSONDecodeError:
                return None
        elif last_bracket != -1:
            repaired = json_text[:last_bracket + 1]
            try:
                parsed_data = json.loads(repaired)
            except json.JSONDecodeError:
                return None

    if not isinstance(parsed_data, list):
        return None

    # Validate and filter
    result = []
    for item in parsed_data:
        if not isinstance(item, dict):
            continue

        q_id = item.get('question_id')
        if q_id is None:
            continue

        if valid_question_ids and q_id not in valid_question_ids:
            logger.warning(f"Unexpected question_id {q_id}, skipping")
            continue

        # Clean transcription
        if 'transcription' in item:
            item['transcription'] = clean_markdown(item['transcription'])
            item['transcription'] = remove_page_references(item['transcription'])

        # Normalize traffic light
        if 'traffic_light_rating' in item:
            item['traffic_light_rating'] = normalize_traffic_light(item['traffic_light_rating'])

        result.append(item)

    return result if result else None


def group_questions_by_category(
    questions: List[Tuple]
) -> Dict[int, List[Tuple]]:
    """
    Group question tuples by category ID.

    Expected tuple format: (id, text, use_llm, default, category_name, category_id, ...)

    Args:
        questions: List of question tuples

    Returns:
        Dictionary mapping category_id to list of questions
    """
    groups = {}

    for q in questions:
        if len(q) < 6:
            continue

        category_id = q[5]
        use_llm = q[2] if len(q) > 2 else True

        if not use_llm:
            continue

        if category_id not in groups:
            groups[category_id] = []
        groups[category_id].append(q)

    return groups


def format_questions_batch(questions: List[Tuple]) -> str:
    """
    Format question tuples for batch processing.

    Args:
        questions: List of question tuples

    Returns:
        Formatted questions string
    """
    formatted = []

    for q in questions:
        q_id = q[0]
        q_text = q[1]
        use_llm = q[2] if len(q) > 2 else True

        if use_llm:
            formatted.append(f"Question {q_id}: {q_text}")

    return "\n\n".join(formatted)


def calculate_prompt_savings(
    full_prompt_tokens: int,
    category_tokens: Dict[int, int]
) -> Dict[str, Any]:
    """
    Calculate token savings from using modular prompts.

    Args:
        full_prompt_tokens: Token count for full monolithic prompt
        category_tokens: Dict of category_id -> token count

    Returns:
        Dictionary with savings statistics
    """
    total_modular = sum(category_tokens.values())
    num_categories = len(category_tokens)

    # If processing N categories with monolithic, it's N * full_prompt_tokens
    monolithic_total = num_categories * full_prompt_tokens

    savings = monolithic_total - total_modular
    savings_pct = (savings / monolithic_total * 100) if monolithic_total > 0 else 0

    return {
        "full_prompt_tokens": full_prompt_tokens,
        "num_categories": num_categories,
        "monolithic_total_tokens": monolithic_total,
        "modular_total_tokens": total_modular,
        "tokens_saved": savings,
        "savings_percentage": round(savings_pct, 1),
        "category_breakdown": category_tokens,
    }
