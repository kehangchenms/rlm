"""
Appraisal Processor using RLM

This module provides the main interface for processing appraisal documents
using RLM (Recursive Language Models) with modular prompts.
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from .prompt_builder import (
    PromptBuilder,
    build_prompt_for_category,
    format_questions_for_prompt,
    CATEGORY_NAMES,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token-based rate limiter for API calls.

    Tracks token usage and calculates required wait times to stay
    within the specified tokens-per-minute limit.
    """

    def __init__(self, tokens_per_minute: int = 30000):
        """
        Initialize the rate limiter.

        Args:
            tokens_per_minute: Maximum tokens allowed per minute
        """
        self.tokens_per_minute = tokens_per_minute
        self.token_history: List[Tuple[float, int]] = []  # (timestamp, tokens)

    def _clean_old_entries(self):
        """Remove entries older than 60 seconds."""
        cutoff = time.time() - 60
        self.token_history = [(t, tokens) for t, tokens in self.token_history if t > cutoff]

    def get_tokens_used_last_minute(self) -> int:
        """Get total tokens used in the last 60 seconds."""
        self._clean_old_entries()
        return sum(tokens for _, tokens in self.token_history)

    def calculate_wait_time(self, tokens_needed: int) -> float:
        """
        Calculate how long to wait before making a request with the given token count.

        Args:
            tokens_needed: Number of tokens the next request will use

        Returns:
            Seconds to wait (0 if no wait needed)
        """
        self._clean_old_entries()

        tokens_used = self.get_tokens_used_last_minute()
        tokens_available = self.tokens_per_minute - tokens_used

        if tokens_needed <= tokens_available:
            return 0.0

        # Need to wait for some tokens to "expire" from the window
        # Find when enough tokens will be freed
        if not self.token_history:
            return 0.0

        # Sort by timestamp
        sorted_history = sorted(self.token_history, key=lambda x: x[0])

        tokens_to_free = tokens_needed - tokens_available
        freed = 0
        wait_until = time.time()

        for timestamp, tokens in sorted_history:
            freed += tokens
            if freed >= tokens_to_free:
                # This entry expiring will free enough tokens
                wait_until = timestamp + 60
                break

        wait_time = max(0, wait_until - time.time())
        return wait_time

    def record_request(self, tokens: int):
        """Record a request with the given token count."""
        self.token_history.append((time.time(), tokens))

    def wait_if_needed(self, tokens_needed: int) -> float:
        """
        Wait if necessary before making a request.

        Args:
            tokens_needed: Number of tokens the next request will use

        Returns:
            Actual seconds waited
        """
        wait_time = self.calculate_wait_time(tokens_needed)

        if wait_time > 0:
            logger.info(f"Rate limit: waiting {wait_time:.1f}s before next request "
                       f"({self.get_tokens_used_last_minute():,} tokens used in last minute, "
                       f"limit: {self.tokens_per_minute:,})")
            time.sleep(wait_time)

        return wait_time


@dataclass
class Question:
    """Represents a question to be answered."""
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
        }


@dataclass
class Answer:
    """Represents an answer to a question."""
    question_id: int
    answer: str
    transcription: str
    traffic_light_rating: Optional[str] = None
    self_assessment_grade: Optional[str] = None
    self_assessment_confidence: Optional[float] = None
    self_assessment_reasoning: Optional[str] = None


@dataclass
class ProcessingResult:
    """Result of processing an appraisal document."""
    answers: Dict[int, Answer] = field(default_factory=dict)
    category_results: Dict[int, List[Answer]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)


class AppraisalProcessor:
    """
    Main processor for appraisal document review using RLM.

    This class orchestrates the processing of appraisal documents by:
    1. Grouping questions by category
    2. Building optimized prompts for each category
    3. Using RLM to process each category with full response token capacity
    4. Aggregating results

    Example:
        >>> processor = AppraisalProcessor(
        ...     backend="anthropic",
        ...     model_name="claude-sonnet-4-20250514"
        ... )
        >>> result = processor.process(document, questions)
        >>> print(result.answers)
    """

    def __init__(
        self,
        backend: str = "anthropic",
        model_name: str = "claude-sonnet-4-20250514",
        max_tokens: int = 32768,
        api_key: Optional[str] = None,
        verbose: bool = True,
        use_rlm: bool = True,
        tokens_per_minute: int = 30000,
        use_prompt_caching: bool = True,
    ):
        """
        Initialize the AppraisalProcessor.

        Args:
            backend: LLM backend to use ("anthropic", "openai", etc.)
            model_name: Model name/ID
            max_tokens: Maximum tokens for responses
            api_key: API key (if not set in environment)
            verbose: Enable verbose logging
            use_rlm: Use RLM for processing (if False, use direct LLM calls)
            tokens_per_minute: Rate limit (tokens per minute)
            use_prompt_caching: Use Anthropic prompt caching to reduce token usage
        """
        self.backend = backend
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.verbose = verbose
        self.use_rlm = use_rlm
        self.tokens_per_minute = tokens_per_minute
        self.use_prompt_caching = use_prompt_caching
        self.prompt_builder = PromptBuilder()

        # Initialize rate limiter
        self.rate_limiter = RateLimiter(tokens_per_minute)

        # Cache for the document (used with prompt caching)
        self._cached_document: Optional[str] = None
        self._cache_id: Optional[str] = None

        # Initialize RLM or direct client
        self._client = None

    def _get_client(self):
        """Get or create the LLM client."""
        if self._client is None:
            if self.use_rlm:
                try:
                    from rlm import RLM
                    backend_kwargs = {"model_name": self.model_name, "max_tokens": self.max_tokens}
                    if self.api_key:
                        backend_kwargs["api_key"] = self.api_key
                    self._client = RLM(
                        backend=self.backend,
                        backend_kwargs=backend_kwargs,
                        verbose=self.verbose,
                    )
                except ImportError:
                    logger.warning("RLM not available, falling back to direct client")
                    self.use_rlm = False

            if not self.use_rlm:
                # Fallback to direct Anthropic client
                self._client = self._create_direct_client()

        return self._client

    def _create_direct_client(self):
        """Create a direct LLM client (non-RLM)."""
        if self.backend == "anthropic":
            try:
                import anthropic
                api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
                return anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("anthropic package required for direct Anthropic calls")
        else:
            raise ValueError(f"Direct client not implemented for backend: {self.backend}")

    def group_questions_by_category(
        self,
        questions: List[Question]
    ) -> Dict[int, List[Question]]:
        """
        Group questions by their category ID.

        Args:
            questions: List of Question objects

        Returns:
            Dictionary mapping category_id to list of questions
        """
        groups = {}
        for q in questions:
            if q.category_id not in groups:
                groups[q.category_id] = []
            groups[q.category_id].append(q)

        logger.info(f"Grouped {len(questions)} questions into {len(groups)} categories")
        for cat_id, cat_questions in groups.items():
            cat_name = CATEGORY_NAMES.get(cat_id, f"Category {cat_id}")
            logger.info(f"  - {cat_name}: {len(cat_questions)} questions")

        return groups

    def process_category(
        self,
        document: str,
        category_id: int,
        questions: List[Question]
    ) -> Tuple[List[Answer], Optional[str]]:
        """
        Process a single category of questions.

        Args:
            document: The full appraisal document text
            category_id: The category ID being processed
            questions: List of questions in this category

        Returns:
            Tuple of (list of answers, error message if any)
        """
        cat_name = CATEGORY_NAMES.get(category_id, f"Category {category_id}")
        logger.info(f"Processing category {category_id}: {cat_name} ({len(questions)} questions)")

        # Build the optimized prompt for this category
        question_dicts = [q.to_dict() for q in questions]
        prompt = self.prompt_builder.build_prompt(category_id, question_dicts)

        # Format questions
        questions_text = format_questions_for_prompt(question_dicts)

        # Estimate tokens
        prompt_tokens = self.prompt_builder.estimate_tokens(prompt)
        doc_tokens = self.prompt_builder.estimate_tokens(document)
        logger.info(f"  Prompt tokens: ~{prompt_tokens}, Document tokens: ~{doc_tokens}")

        try:
            if self.use_rlm:
                answers = self._process_with_rlm(document, prompt, questions_text, questions)
            else:
                answers = self._process_direct(document, prompt, questions_text, questions)

            return answers, None

        except Exception as e:
            error_msg = f"Error processing category {category_id}: {str(e)}"
            logger.error(error_msg)
            return [], error_msg

    def _process_with_rlm(
        self,
        document: str,
        prompt: str,
        questions_text: str,
        questions: List[Question]
    ) -> List[Answer]:
        """
        Process questions using TRUE RLM approach.

        The document is stored LOCALLY in the REPL environment as `context`.
        The LLM generates Python code that searches through the document.
        Only the prompt and code results are sent to the API - NOT the document!

        This solves rate limit issues because:
        - Document (~72k tokens) is NEVER sent to the API
        - Only prompts (~2-5k tokens) + code results are sent
        - Sub-LLM calls can be batched for efficiency

        Args:
            document: The full document text (stored locally, not sent to API)
            prompt: The category-specific prompt
            questions_text: Formatted questions
            questions: List of Question objects

        Returns:
            List of Answer objects
        """
        try:
            from rlm import RLM
        except ImportError:
            raise ImportError("RLM package required. Install with: pip install -e .")

        # Create RLM instance
        # The document is passed as context - it stays LOCAL, never sent to API!
        rlm = RLM(
            backend=self.backend,
            backend_kwargs={
                "model_name": self.model_name,
                "max_tokens": self.max_tokens,
                **({"api_key": self.api_key} if self.api_key else {})
            },
            environment="local",  # Local REPL environment
            max_iterations=15,    # Allow multiple code iterations
            verbose=True,
        )

        # Build the root prompt (this is what the LLM sees - NOT the document!)
        # Get question IDs for the prompt
        question_ids = [q.id for q in questions]

        root_prompt = f"""
You are an expert appraisal reviewer analyzing a commercial real estate appraisal document.

The document is stored in the `context` variable (a string with ~{len(document):,} characters).

YOUR TASK: Answer these {len(questions)} questions about the appraisal document:
Question IDs: {question_ids}

{questions_text}

INSTRUCTIONS:
{prompt}

STRATEGY:
1. First, explore `context` to understand its structure (print first/last 2000 chars)
2. Use Python string operations or regex to find relevant sections
3. For complex analysis, use `llm_query()` on specific chunks (it can handle ~500K chars)
4. Build your answers in a Python list of dictionaries

CRITICAL - OUTPUT FORMAT:
Build a Python list called `answers` with this exact structure:
```repl
answers = []
# For each question, add an answer dict:
answers.append({{
    "question_id": 123,  # The actual question ID number
    "answer": "Your detailed answer here",
    "transcription": "Direct quote or summary from document",
    "traffic_light_rating": "Green"  # Green/Yellow/Red
}})
# After adding all answers:
print(f"Built {{len(answers)}} answers")
```

When done, use FINAL_VAR(answers) to return the list.

START NOW: First, print the first 2000 characters of context to understand the document structure.
"""

        logger.info("  Using TRUE RLM: Document stored locally, LLM generates search code")
        logger.info(f"  Document size: {len(document):,} chars (NOT sent to API)")
        logger.info(f"  Questions: {len(questions)}")

        # Execute RLM completion
        # - `document` is passed as context (stored in local REPL, NOT sent to API)
        # - `root_prompt` is the query (sent to API, only ~2-5k tokens)
        result = rlm.completion(
            prompt=document,        # This becomes `context` in REPL - stored locally!
            root_prompt=root_prompt  # This is what LLM sees - sent to API
        )

        response_text = result.response
        logger.info(f"  RLM execution time: {result.execution_time:.1f}s")
        if result.usage_summary:
            # UsageSummary contains model_usage_summaries dict
            total_input = sum(m.total_input_tokens for m in result.usage_summary.model_usage_summaries.values())
            total_output = sum(m.total_output_tokens for m in result.usage_summary.model_usage_summaries.values())
            logger.info(f"  Total tokens used: input={total_input:,}, output={total_output:,}")

        # Parse the response
        return self._parse_response(response_text, questions)

    def _process_direct(
        self,
        document: str,
        prompt: str,
        questions_text: str,
        questions: List[Question]
    ) -> List[Answer]:
        """
        Process questions using direct LLM call with streaming and rate limiting.

        Uses streaming API to handle large context operations that may take
        longer than 10 minutes (required by Anthropic for large documents).

        Supports Anthropic prompt caching to reduce effective token usage
        when processing multiple categories with the same document.

        Args:
            document: The full document text
            prompt: The category-specific prompt
            questions_text: Formatted questions
            questions: List of Question objects

        Returns:
            List of Answer objects
        """
        client = self._get_client()

        # Estimate tokens for rate limiting
        prompt_tokens = self.prompt_builder.estimate_tokens(prompt)
        doc_tokens = self.prompt_builder.estimate_tokens(document)
        questions_tokens = self.prompt_builder.estimate_tokens(questions_text)
        total_input_tokens = prompt_tokens + doc_tokens + questions_tokens

        # Apply rate limiting (wait if necessary)
        wait_time = self.rate_limiter.wait_if_needed(total_input_tokens)
        if wait_time > 0:
            logger.info(f"  Waited {wait_time:.1f}s for rate limit")

        # Build message content with optional prompt caching
        if self.use_prompt_caching and self.backend == "anthropic":
            # Use prompt caching: document is marked as cacheable
            # This significantly reduces effective token usage for subsequent requests
            message_content = [
                {
                    "type": "text",
                    "text": f"Here is the appraisal document to analyze:\n\n<document>\n{document}\n</document>",
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": f"{prompt}\n\nNow, please answer ALL of the following questions:\n\n{questions_text}"
                }
            ]
        else:
            # Standard message without caching
            full_prompt = prompt.replace("{document}", document)
            message_content = f"{full_prompt}\n\nNow, please answer ALL of the following questions:\n\n{questions_text}"

        # Use streaming for large context operations
        # Anthropic requires streaming for operations > 10 minutes
        try:
            with client.messages.stream(
                model=self.model_name,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": message_content
                    }
                ]
            ) as stream:
                response_text = stream.get_final_text()
                # Get actual usage from the final message
                final_message = stream.get_final_message()
                if final_message and hasattr(final_message, 'usage'):
                    actual_input = final_message.usage.input_tokens
                    cache_read = getattr(final_message.usage, 'cache_read_input_tokens', 0) or 0
                    cache_creation = getattr(final_message.usage, 'cache_creation_input_tokens', 0) or 0
                    # Only count non-cached tokens against rate limit
                    effective_tokens = actual_input - cache_read
                    logger.info(f"  Tokens - Input: {actual_input:,}, Cache read: {cache_read:,}, "
                               f"Cache creation: {cache_creation:,}, Effective: {effective_tokens:,}")
                    self.rate_limiter.record_request(effective_tokens)
                else:
                    # Fallback to estimated tokens
                    self.rate_limiter.record_request(total_input_tokens)

        except Exception as e:
            # Record the attempted tokens anyway for rate limiting purposes
            self.rate_limiter.record_request(total_input_tokens)
            raise

        return self._parse_response(response_text, questions)

    def _parse_response(
        self,
        response_text: str,
        questions: List[Question]
    ) -> List[Answer]:
        """
        Parse the LLM response into Answer objects.

        Args:
            response_text: Raw response from LLM
            questions: List of Question objects for validation

        Returns:
            List of Answer objects
        """
        answers = []
        valid_ids = {q.id for q in questions}

        # Log the response for debugging
        if self.verbose:
            logger.debug(f"Response text (first 500 chars): {response_text[:500]}...")
            logger.debug(f"Response text (last 500 chars): ...{response_text[-500:]}")

        # Try to parse as JSON
        try:
            # Find JSON array in response - try multiple patterns
            json_text = None

            # Pattern 1: Standard JSON array
            json_start = response_text.find('[')
            json_end = response_text.rfind(']')

            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end + 1]

            # Pattern 2: JSON might be wrapped in markdown code block
            if not json_text or len(json_text) < 10:
                import re
                json_block = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
                if json_block:
                    json_text = json_block.group(1)

            # Pattern 3: The response might be a dict with an "answers" key
            if not json_text:
                dict_start = response_text.find('{')
                dict_end = response_text.rfind('}')
                if dict_start != -1 and dict_end != -1:
                    try:
                        wrapped = json.loads(response_text[dict_start:dict_end + 1])
                        if isinstance(wrapped, dict) and "answers" in wrapped:
                            if isinstance(wrapped["answers"], list):
                                json_text = json.dumps(wrapped["answers"])
                    except json.JSONDecodeError:
                        pass

            if json_text:
                parsed = json.loads(json_text)

                if isinstance(parsed, list):
                    for item in parsed:
                        # Support multiple key names for question_id
                        q_id = item.get("question_id") or item.get("id") or item.get("qid")
                        if isinstance(q_id, str) and q_id.isdigit():
                            q_id = int(q_id)
                        if q_id in valid_ids:
                            answers.append(Answer(
                                question_id=q_id,
                                answer=item.get("answer", ""),
                                transcription=item.get("transcription", ""),
                                traffic_light_rating=item.get("traffic_light_rating"),
                            ))
                        elif q_id is not None:
                            logger.warning(f"  Question ID {q_id} not in valid IDs: {valid_ids}")
            else:
                logger.warning("No JSON array found in response")
                logger.warning(f"  Response preview: {response_text[:200]}...")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            logger.warning(f"  Response preview: {response_text[:300]}...")

        if not answers and questions:
            logger.warning(f"  No answers parsed. Expected {len(questions)} answers for questions: {[q.id for q in questions]}")

        logger.info(f"  Parsed {len(answers)} answers from response")
        return answers

    def process(
        self,
        document: str,
        questions: List[Question],
        parallel: bool = False,
        batch_all: bool = False,
        incremental_save_path: Optional[str] = None
    ) -> ProcessingResult:
        """
        Process an appraisal document with all questions.

        Args:
            document: The full appraisal document text
            questions: List of Question objects
            parallel: Whether to process categories in parallel (future feature)
            batch_all: If True, send ALL questions in a single API request
                      (recommended for low rate limits)
            incremental_save_path: If provided, save results after each category

        Returns:
            ProcessingResult with all answers
        """
        if batch_all:
            return self._process_batch_all(document, questions)

        result = ProcessingResult()

        # Group questions by category
        category_groups = self.group_questions_by_category(questions)
        total_categories = len(category_groups)

        # Process each category
        for idx, (category_id, cat_questions) in enumerate(category_groups.items(), 1):
            logger.info(f"Processing category {idx}/{total_categories}")
            answers, error = self.process_category(document, category_id, cat_questions)

            if error:
                result.errors.append(error)
            else:
                result.category_results[category_id] = answers
                for answer in answers:
                    result.answers[answer.question_id] = answer

            # Incremental save after each category
            if incremental_save_path and result.answers:
                self._save_incremental(result, incremental_save_path)
                logger.info(f"  Saved {len(result.answers)} answers incrementally to {incremental_save_path}")

        logger.info(f"Processing complete: {len(result.answers)} answers, {len(result.errors)} errors")
        return result

    def _save_incremental(self, result: ProcessingResult, output_path: str):
        """Save current results incrementally."""
        import json
        output_data = []
        for q_id, answer in sorted(result.answers.items()):
            output_data.append({
                "question_id": q_id,
                "answer": answer.answer,
                "transcription": answer.transcription,
                "traffic_light_rating": answer.traffic_light_rating,
            })
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

    def _process_batch_all(
        self,
        document: str,
        questions: List[Question]
    ) -> ProcessingResult:
        """
        Process ALL questions in a single API request.

        This is ideal for accounts with low rate limits, as it:
        - Sends the document only once
        - Processes all questions in one request
        - Avoids rate limit issues between requests

        Args:
            document: The full appraisal document text
            questions: List of Question objects

        Returns:
            ProcessingResult with all answers
        """
        result = ProcessingResult()
        logger.info(f"Processing ALL {len(questions)} questions in a single batch request")

        # Build a combined prompt with all universal sections
        from .prompts.universal import (
            INTRODUCTION,
            CRITICAL_FORMATTING,
            SECTION_A_STANDARD,
            SECTION_A1_EVALUATIVE,
            CRITICAL_INSTRUCTIONS,
        )

        # Use a comprehensive prompt that covers all question types
        combined_prompt = f"""{INTRODUCTION}

{CRITICAL_FORMATTING}

{SECTION_A_STANDARD}

{SECTION_A1_EVALUATIVE}

{CRITICAL_INSTRUCTIONS}

IMPORTANT: You are processing ALL questions in a single batch. Answer each question thoroughly based on the document provided.
"""

        # Format all questions
        questions_text = self._format_all_questions(questions)

        # Estimate tokens
        prompt_tokens = self.prompt_builder.estimate_tokens(combined_prompt)
        doc_tokens = self.prompt_builder.estimate_tokens(document)
        questions_tokens = self.prompt_builder.estimate_tokens(questions_text)
        total_tokens = prompt_tokens + doc_tokens + questions_tokens
        logger.info(f"  Batch request: ~{total_tokens:,} total tokens "
                   f"(prompt: {prompt_tokens:,}, doc: {doc_tokens:,}, questions: {questions_tokens:,})")

        try:
            answers = self._process_direct_batch(document, combined_prompt, questions_text, questions)
            for answer in answers:
                result.answers[answer.question_id] = answer
            logger.info(f"  Batch processing complete: {len(answers)} answers")
        except Exception as e:
            error_msg = f"Error in batch processing: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

        logger.info(f"Processing complete: {len(result.answers)} answers, {len(result.errors)} errors")
        return result

    def _format_all_questions(self, questions: List[Question]) -> str:
        """Format all questions for batch processing."""
        lines = []
        for q in questions:
            cat_name = CATEGORY_NAMES.get(q.category_id, f"Category {q.category_id}")
            lines.append(f"Q{q.id} [{cat_name}]: {q.text}")
        return "\n\n".join(lines)

    def _process_direct_batch(
        self,
        document: str,
        prompt: str,
        questions_text: str,
        questions: List[Question]
    ) -> List[Answer]:
        """
        Process ALL questions in a single batch using direct LLM call.

        Args:
            document: The full document text
            prompt: The combined prompt
            questions_text: All formatted questions
            questions: List of Question objects

        Returns:
            List of Answer objects
        """
        client = self._get_client()

        # Build message content with prompt caching for the document
        if self.use_prompt_caching and self.backend == "anthropic":
            message_content = [
                {
                    "type": "text",
                    "text": f"Here is the appraisal document to analyze:\n\n<document>\n{document}\n</document>",
                    "cache_control": {"type": "ephemeral"}
                },
                {
                    "type": "text",
                    "text": f"""{prompt}

Now, please answer ALL of the following questions based on the provided document.

Return your answers as a JSON array with objects containing:
- "question_id": The question ID (the number after Q)
- "answer": Your detailed answer with page references where applicable
- "transcription": A concise summary or direct quote
- "traffic_light_rating": "Green" (well supported), "Yellow" (partially supported), or "Red" (not found/unsupported)

QUESTIONS:

{questions_text}

IMPORTANT: Answer ALL {len(questions)} questions. Return ONLY the JSON array, no other text."""
                }
            ]
        else:
            message_content = f"""{prompt}

Here is the appraisal document to analyze:

<document>
{document}
</document>

Now, please answer ALL of the following questions based on the provided document.

Return your answers as a JSON array with objects containing:
- "question_id": The question ID (the number after Q)
- "answer": Your detailed answer with page references where applicable
- "transcription": A concise summary or direct quote
- "traffic_light_rating": "Green" (well supported), "Yellow" (partially supported), or "Red" (not found/unsupported)

QUESTIONS:

{questions_text}

IMPORTANT: Answer ALL {len(questions)} questions. Return ONLY the JSON array, no other text."""

        logger.info("  Sending batch request to API (this may take several minutes)...")

        # Use streaming for large context operations
        with client.messages.stream(
            model=self.model_name,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": message_content
                }
            ]
        ) as stream:
            response_text = stream.get_final_text()
            # Log usage
            final_message = stream.get_final_message()
            if final_message and hasattr(final_message, 'usage'):
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens
                cache_read = getattr(final_message.usage, 'cache_read_input_tokens', 0) or 0
                cache_creation = getattr(final_message.usage, 'cache_creation_input_tokens', 0) or 0
                logger.info(f"  Usage - Input: {input_tokens:,}, Output: {output_tokens:,}, "
                           f"Cache read: {cache_read:,}, Cache creation: {cache_creation:,}")

        return self._parse_response(response_text, questions)

    def process_from_tuples(
        self,
        document: str,
        question_tuples: List[Tuple]
    ) -> ProcessingResult:
        """
        Process questions provided as tuples (compatible with existing DB format).

        Expected tuple format: (id, text, use_llm, default, category_name, category_id, ...)

        Args:
            document: The full appraisal document text
            question_tuples: List of question tuples

        Returns:
            ProcessingResult with all answers
        """
        questions = []
        for q_tuple in question_tuples:
            q_id = q_tuple[0]
            q_text = q_tuple[1]
            use_llm = q_tuple[2] if len(q_tuple) > 2 else True
            category_name = q_tuple[4] if len(q_tuple) > 4 else ""
            category_id = q_tuple[5] if len(q_tuple) > 5 else 0

            if use_llm:
                questions.append(Question(
                    id=q_id,
                    text=q_text,
                    category_id=category_id,
                    category_name=category_name,
                    use_llm=use_llm,
                ))

        return self.process(document, questions)
