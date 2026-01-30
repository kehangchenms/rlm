"""
Appraisal Processor using RLM

This module provides the main interface for processing appraisal documents
using RLM (Recursive Language Models) with modular prompts.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from .prompt_builder import (
    PromptBuilder,
    build_prompt_for_category,
    format_questions_for_prompt,
    CATEGORY_NAMES,
)

logger = logging.getLogger(__name__)


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
        """
        self.backend = backend
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.verbose = verbose
        self.use_rlm = use_rlm
        self.prompt_builder = PromptBuilder()

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
        Process questions using RLM.

        Args:
            document: The full document text
            prompt: The category-specific prompt
            questions_text: Formatted questions
            questions: List of Question objects

        Returns:
            List of Answer objects
        """
        client = self._get_client()

        # Build the RLM completion prompt
        # The document is stored in context, and the model can query it
        rlm_prompt = f"""
{prompt}

Here is the appraisal document to analyze:
<document>
{document}
</document>

Now, please answer ALL of the following questions based on the provided document:

{questions_text}

Return your answers as a JSON array with objects containing:
- "question_id": The question ID
- "answer": Your detailed answer
- "transcription": A concise summary
- "traffic_light_rating": "Green", "Yellow", or "Red"
"""

        # Execute via RLM
        result = client.completion(rlm_prompt)
        response_text = result.response

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
        Process questions using direct LLM call.

        Args:
            document: The full document text
            prompt: The category-specific prompt
            questions_text: Formatted questions
            questions: List of Question objects

        Returns:
            List of Answer objects
        """
        client = self._get_client()

        # Format the full prompt with document
        full_prompt = prompt.replace("{document}", document)

        # Create message
        message = client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": f"{full_prompt}\n\nNow, please answer ALL of the following questions:\n\n{questions_text}"
                }
            ]
        )

        response_text = message.content[0].text
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

        # Try to parse as JSON
        try:
            # Find JSON array in response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']')

            if json_start != -1 and json_end != -1:
                json_text = response_text[json_start:json_end + 1]
                parsed = json.loads(json_text)

                if isinstance(parsed, list):
                    for item in parsed:
                        q_id = item.get("question_id")
                        if q_id in valid_ids:
                            answers.append(Answer(
                                question_id=q_id,
                                answer=item.get("answer", ""),
                                transcription=item.get("transcription", ""),
                                traffic_light_rating=item.get("traffic_light_rating"),
                            ))

        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, attempting text parsing")
            # Could implement text-based parsing as fallback
            pass

        logger.info(f"  Parsed {len(answers)} answers from response")
        return answers

    def process(
        self,
        document: str,
        questions: List[Question],
        parallel: bool = False
    ) -> ProcessingResult:
        """
        Process an appraisal document with all questions.

        Args:
            document: The full appraisal document text
            questions: List of Question objects
            parallel: Whether to process categories in parallel (future feature)

        Returns:
            ProcessingResult with all answers
        """
        result = ProcessingResult()

        # Group questions by category
        category_groups = self.group_questions_by_category(questions)

        # Process each category
        for category_id, cat_questions in category_groups.items():
            answers, error = self.process_category(document, category_id, cat_questions)

            if error:
                result.errors.append(error)
            else:
                result.category_results[category_id] = answers
                for answer in answers:
                    result.answers[answer.question_id] = answer

        logger.info(f"Processing complete: {len(result.answers)} answers, {len(result.errors)} errors")
        return result

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
