"""Feedback schemas for classification quality tracking."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class FeedbackVerdict(str, Enum):
    """User verdict on classification quality."""
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    CORRECT = "correct"


class FeedbackCategory(str, Enum):
    """Category for false positive / false negative feedback."""
    WRONG_SECTOR = "wrong_sector"
    IRRELEVANT_MODALITY = "irrelevant_modality"
    TOO_SMALL = "too_small"
    TOO_LARGE = "too_large"
    CLOSED = "closed"
    OTHER = "other"


class FeedbackRequest(BaseModel):
    """POST /v1/feedback request body."""
    search_id: str = Field(..., description="UUID of the search session")
    bid_id: str = Field(..., description="ID of the bid being rated")
    user_verdict: FeedbackVerdict
    reason: Optional[str] = Field(None, max_length=500, description="Free-text reason (optional)")
    category: Optional[FeedbackCategory] = None
    # Context fields sent from frontend for enrichment
    setor_id: Optional[str] = None
    bid_objeto: Optional[str] = Field(None, max_length=200)
    bid_valor: Optional[float] = None
    bid_uf: Optional[str] = None
    confidence_score: Optional[int] = None
    relevance_source: Optional[str] = None


class FeedbackResponse(BaseModel):
    """POST /v1/feedback response body."""
    id: str
    received_at: str
    updated: bool = False


class FeedbackDeleteResponse(BaseModel):
    """DELETE /v1/feedback/{id} response body."""
    deleted: bool = True


class FeedbackPatternBreakdown(BaseModel):
    """Breakdown of feedback verdicts."""
    correct: int = 0
    false_positive: int = 0
    false_negative: int = 0


class FPKeywordSuggestion(BaseModel):
    """Keyword appearing frequently in false positives."""
    keyword: str
    count: int
    suggestion: str


class FeedbackPatternsResponse(BaseModel):
    """GET /v1/admin/feedback/patterns response body."""
    total_feedbacks: int
    breakdown: FeedbackPatternBreakdown
    precision_estimate: Optional[float] = None
    fp_categories: Dict[str, int] = Field(default_factory=dict)
    top_fp_keywords: List[FPKeywordSuggestion] = Field(default_factory=list)
    suggested_exclusions: List[str] = Field(default_factory=list)
