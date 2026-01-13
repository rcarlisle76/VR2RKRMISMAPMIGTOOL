"""
AI-enhanced mapping service.

Uses semantic embeddings and optional LLM integration for intelligent field mapping.
"""

import json
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ..core.logging_config import get_logger
from ..models.mapping_models import SourceFile, FieldMapping
from ..models.salesforce_metadata import SalesforceObject, SalesforceField
from .mapping_service import MappingService

logger = get_logger(__name__)


@dataclass
class MappingScore:
    """Represents a field mapping with confidence score."""
    source_column: str
    target_field: SalesforceField
    score: float
    method: str  # 'fuzzy', 'semantic', 'llm'
    reasoning: Optional[str] = None


class AIEnhancedMappingService(MappingService):
    """
    Enhanced mapping service with AI capabilities.

    Combines:
    - Fuzzy string matching (original)
    - Semantic embeddings (local, offline)
    - Optional LLM integration (Claude/GPT)
    """

    def __init__(
        self,
        use_semantic: bool = True,
        use_llm: bool = False,
        llm_provider: str = "claude",
        llm_model: str = "claude-3-5-sonnet-20241022",
        api_key: str = ""
    ):
        """
        Initialize AI-enhanced mapping service.

        Args:
            use_semantic: Enable semantic embedding matching
            use_llm: Enable LLM-based matching (requires API key)
            llm_provider: LLM provider ('claude' or 'openai')
            llm_model: Model name to use
            api_key: API key for LLM provider
        """
        super().__init__()
        self.use_semantic = use_semantic
        self.use_llm = use_llm
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.api_key = api_key

        # Lazy-load models to avoid startup delay
        self._embedder = None
        self._llm_client = None

        logger.info(
            f"AI Mapping Service initialized (semantic: {use_semantic}, llm: {use_llm})"
        )

    @property
    def embedder(self):
        """Lazy-load embedding model."""
        if self._embedder is None and self.use_semantic:
            try:
                # Add torch DLL directory to PATH (Windows fix for DLL loading)
                import os
                import sys
                if sys.platform == 'win32':
                    torch_lib_path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'torch', 'lib')
                    if os.path.exists(torch_lib_path):
                        os.environ['PATH'] = torch_lib_path + os.pathsep + os.environ.get('PATH', '')
                        # Also add to DLL search path for Python 3.8+
                        if hasattr(os, 'add_dll_directory'):
                            os.add_dll_directory(torch_lib_path)

                from sentence_transformers import SentenceTransformer
                logger.info("Loading semantic embedding model...")
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Semantic embedding model loaded successfully")
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
                self.use_semantic = False
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self.use_semantic = False
        return self._embedder

    @property
    def llm_client(self):
        """Lazy-load LLM client."""
        if self._llm_client is None and self.use_llm:
            try:
                if self.llm_provider == "claude":
                    import anthropic
                    self._llm_client = anthropic.Anthropic(api_key=self.api_key)
                    logger.info("Claude API client initialized")
                elif self.llm_provider == "openai":
                    import openai
                    self._llm_client = openai.OpenAI(api_key=self.api_key)
                    logger.info("OpenAI API client initialized")
                else:
                    logger.error(f"Unknown LLM provider: {self.llm_provider}")
                    self.use_llm = False
            except ImportError as e:
                logger.warning(
                    f"{self.llm_provider} library not installed. "
                    f"Run: pip install {self.llm_provider}"
                )
                self.use_llm = False
            except Exception as e:
                logger.error(f"Failed to initialize LLM client: {e}")
                self.use_llm = False
        return self._llm_client

    def auto_suggest_mappings(
        self,
        source_file: SourceFile,
        salesforce_object: SalesforceObject,
        threshold: float = 0.6
    ) -> List[FieldMapping]:
        """
        Auto-suggest field mappings using hybrid approach.

        Args:
            source_file: Source file with columns
            salesforce_object: Target Salesforce object
            threshold: Minimum confidence threshold

        Returns:
            List of suggested FieldMapping objects
        """
        logger.info(
            f"AI-enhanced auto-mapping: {len(source_file.columns)} columns "
            f"(semantic: {self.use_semantic}, llm: {self.use_llm})"
        )

        all_scores: Dict[str, List[MappingScore]] = {}

        # Step 1: Fuzzy matching for all columns
        fuzzy_threshold = 0.7 if (self.use_semantic or self.use_llm) else threshold
        for source_col in source_file.columns:
            scores = self._fuzzy_match_column(
                source_col.name,
                salesforce_object.fields,
                fuzzy_threshold
            )
            all_scores[source_col.name] = scores

        # Step 2: Semantic matching for low-confidence fuzzy matches
        if self.use_semantic:
            for source_col in source_file.columns:
                fuzzy_best = all_scores[source_col.name][0] if all_scores[source_col.name] else None

                # Use semantic matching if fuzzy match is weak or missing
                if not fuzzy_best or fuzzy_best.score < 0.85:
                    semantic_scores = self._semantic_match_column(
                        source_col.name,
                        salesforce_object.fields,
                        threshold
                    )
                    all_scores[source_col.name].extend(semantic_scores)

        # Step 3: LLM matching for remaining unmapped columns (batched)
        if self.use_llm and self.api_key:
            unmapped_columns = [
                col for col in source_file.columns
                if not all_scores.get(col.name) or
                all_scores[col.name][0].score < 0.75
            ]

            if unmapped_columns:
                logger.info(f"Using LLM for {len(unmapped_columns)} difficult mappings")

                # Process in batches to avoid token limits and JSON parsing errors
                batch_size = 50  # Process 50 columns at a time
                for i in range(0, len(unmapped_columns), batch_size):
                    batch = unmapped_columns[i:i + batch_size]
                    batch_num = i//batch_size + 1
                    logger.info(f"Processing LLM batch {batch_num}: {len(batch)} columns")

                    try:
                        llm_scores = self._llm_match_columns(
                            batch,
                            salesforce_object,
                            threshold
                        )
                        for col_name, scores in llm_scores.items():
                            all_scores[col_name].extend(scores)
                        logger.info(f"Batch {batch_num} completed successfully")
                    except Exception as e:
                        logger.error(f"Batch {batch_num} failed: {e}")
                        # Continue with next batch instead of crashing

        # Step 4: Select best mapping for each column
        suggestions = []
        for source_col in source_file.columns:
            scores = all_scores.get(source_col.name, [])
            if not scores:
                continue

            # Sort by score (highest first)
            scores.sort(key=lambda s: s.score, reverse=True)
            best = scores[0]

            # Only suggest if above threshold
            if best.score >= threshold:
                mapping = FieldMapping(
                    source_column=source_col.name,
                    target_field=best.target_field.name,
                    mapping_type='direct',
                    is_required=best.target_field.required,
                    confidence=best.score,  # Include confidence score
                    method=best.method  # Include mapping method (fuzzy/semantic/llm)
                )
                suggestions.append(mapping)

                logger.info(
                    f"Mapped: {source_col.name} → {best.target_field.name} "
                    f"(score: {best.score:.2f}, method: {best.method})"
                )

        logger.info(f"Generated {len(suggestions)} AI-enhanced mapping suggestions")
        return suggestions

    def _fuzzy_match_column(
        self,
        source_column: str,
        sf_fields: List[SalesforceField],
        threshold: float
    ) -> List[MappingScore]:
        """Fuzzy string matching (original algorithm)."""
        scores = []

        for sf_field in sf_fields:
            # Calculate similarity against API name and label
            name_score = self._calculate_similarity(source_column, sf_field.name)
            label_score = self._calculate_similarity(source_column, sf_field.label)
            score = max(name_score, label_score)

            if score >= threshold:
                scores.append(MappingScore(
                    source_column=source_column,
                    target_field=sf_field,
                    score=score,
                    method='fuzzy'
                ))

        return scores

    def _semantic_match_column(
        self,
        source_column: str,
        sf_fields: List[SalesforceField],
        threshold: float
    ) -> List[MappingScore]:
        """Semantic embedding-based matching."""
        if not self.embedder:
            return []

        scores = []

        try:
            from sklearn.metrics.pairwise import cosine_similarity

            # Generate embeddings
            source_embedding = self.embedder.encode([source_column])[0]

            # Compare against each field
            for sf_field in sf_fields:
                # Create rich field description for better matching
                field_text = f"{sf_field.name} {sf_field.label}"
                target_embedding = self.embedder.encode([field_text])[0]

                # Calculate cosine similarity
                similarity = cosine_similarity(
                    [source_embedding],
                    [target_embedding]
                )[0][0]

                if similarity >= threshold:
                    scores.append(MappingScore(
                        source_column=source_column,
                        target_field=sf_field,
                        score=float(similarity),
                        method='semantic'
                    ))

        except Exception as e:
            logger.error(f"Error in semantic matching: {e}")

        return scores

    def _llm_match_columns(
        self,
        source_columns: List,
        salesforce_object: SalesforceObject,
        threshold: float
    ) -> Dict[str, List[MappingScore]]:
        """LLM-based intelligent mapping."""
        if not self.llm_client:
            return {}

        try:
            # Build prompt
            prompt = self._build_llm_prompt(source_columns, salesforce_object)

            # Call LLM
            if self.llm_provider == "claude":
                response = self._call_claude(prompt)
            else:
                response = self._call_openai(prompt)

            # Parse response
            return self._parse_llm_response(
                response,
                source_columns,
                salesforce_object,
                threshold
            )

        except Exception as e:
            logger.error(f"Error in LLM matching: {e}")
            return {}

    def _build_llm_prompt(
        self,
        source_columns: List,
        salesforce_object: SalesforceObject
    ) -> str:
        """Build prompt for LLM mapping."""
        csv_columns = "\n".join([
            f"- {col.name} (type: {col.inferred_type})"
            for col in source_columns
        ])

        sf_fields = "\n".join([
            f"- {f.name} ({f.label}) - {f.type}, required: {f.required}"
            for f in salesforce_object.fields[:100]  # Limit to avoid token limits
        ])

        return f"""Map CSV columns to Salesforce fields.

CSV columns:
{csv_columns}

Salesforce {salesforce_object.label} fields:
{sf_fields}

For each CSV column, find the best matching Salesforce field. Consider:
- Semantic meaning (email vs e-mail, phone vs telephone)
- Data types (date columns → date fields)
- Common abbreviations (amt=amount, num=number, qty=quantity)
- Business context (BillingStreet vs ShippingStreet)

Respond with ONLY a JSON array, no other text. Format:
[
  {{"source": "csv_column_name", "target": "SalesforceField__c", "confidence": 0.95, "reasoning": "why this matches"}},
  {{"source": "another_column", "target": "AnotherField__c", "confidence": 0.85, "reasoning": "semantic similarity"}}
]

If no good matches, return: []"""

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API."""
        response = self.llm_client.messages.create(
            model=self.llm_model,
            max_tokens=4096,  # Increased to handle larger responses
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = self.llm_client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096  # Increased to handle larger responses
        )
        return response.choices[0].message.content

    def _parse_llm_response(
        self,
        response: str,
        source_columns: List,
        salesforce_object: SalesforceObject,
        threshold: float
    ) -> Dict[str, List[MappingScore]]:
        """Parse LLM JSON response into MappingScore objects."""
        scores_by_column: Dict[str, List[MappingScore]] = {}

        try:
            # Extract JSON from response (handle markdown code blocks and extra text)
            json_text = response.strip()

            # Handle markdown code blocks
            if "```json" in json_text:
                start = json_text.find("```json") + 7
                end = json_text.find("```", start)
                json_text = json_text[start:end].strip()
            elif "```" in json_text:
                start = json_text.find("```") + 3
                end = json_text.find("```", start)
                json_text = json_text[start:end].strip()

            # Find JSON array in response (look for [ ... ])
            if not json_text.startswith("["):
                start = json_text.find("[")
                end = json_text.rfind("]") + 1
                if start != -1 and end > start:
                    json_text = json_text[start:end]
                else:
                    logger.warning("No JSON array found in LLM response")
                    logger.debug(f"LLM response: {response[:500]}")
                    return {}

            # Clean up common JSON syntax errors (simple approach to avoid hanging)
            # Remove trailing commas before closing brackets/braces
            json_text = json_text.replace(',}', '}')
            json_text = json_text.replace(', }', '}')
            json_text = json_text.replace(',]', ']')
            json_text = json_text.replace(', ]', ']')

            try:
                mappings = json.loads(json_text)
            except json.JSONDecodeError as e:
                # If parsing fails, try removing ALL trailing commas more aggressively
                logger.warning(f"First parse attempt failed: {e}. Trying cleanup...")
                import re
                json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
                mappings = json.loads(json_text)

            # Build field lookup
            field_lookup = {f.name: f for f in salesforce_object.fields}

            for mapping in mappings:
                source = mapping.get("source")
                target = mapping.get("target")
                confidence = mapping.get("confidence", 0.0)
                reasoning = mapping.get("reasoning", "")

                if confidence < threshold:
                    continue

                target_field = field_lookup.get(target)
                if not target_field:
                    logger.warning(f"LLM suggested unknown field: {target}")
                    continue

                if source not in scores_by_column:
                    scores_by_column[source] = []

                scores_by_column[source].append(MappingScore(
                    source_column=source,
                    target_field=target_field,
                    score=confidence,
                    method='llm',
                    reasoning=reasoning
                ))

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Cleaned JSON text (first 1000 chars): {json_text[:1000]}")
            logger.debug(f"Full LLM response: {response}")
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.debug(f"Full LLM response: {response}")

        return scores_by_column
