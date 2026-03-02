"""
Pydantic response schemas for every API resource.
These are the shapes the frontend receives — intentionally simpler than the ORM models.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


# ── Client ────────────────────────────────────────────────────────────────────

class ClientSummary(BaseModel):
    id: str
    name: str
    kyc_level: str
    products_held: list[str]
    account_opened_at: datetime
    stated_income: float
    occupation: str
    overall_risk_score: float
    archetype: str
    active_restriction_level: int

    model_config = {"from_attributes": True}


class ClientDetail(ClientSummary):
    date_of_birth: str
    archetype_trajectory: str
    risk_trend: str
    risk_scores: dict[str, float]
    risk_history: list[dict]
    indicators_detected: list[dict]
    known_counterparties: list[dict]
    total_inflow_30d: float
    total_outflow_30d: float
    deposit_frequency_per_week: float


# ── Transaction ───────────────────────────────────────────────────────────────

class TransactionOut(BaseModel):
    id: str
    client_id: str
    type: str
    product: str
    amount: float
    timestamp: datetime
    source: Optional[str]
    destination: Optional[str]
    counterparty_name: Optional[str]
    txn_metadata: Optional[dict]

    model_config = {"from_attributes": True}


# ── Behavioral profile ────────────────────────────────────────────────────────

class BehavioralProfileOut(BaseModel):
    client_id: str
    avg_deposit_amount: float
    avg_withdrawal_amount: float
    deposit_frequency_per_week: float
    total_inflow_30d: float
    total_outflow_30d: float
    known_counterparties: list[dict]
    risk_scores: dict[str, float]
    overall_risk_score: float
    archetype: str
    archetype_trajectory: str
    risk_trend: str
    risk_history: list[dict]
    indicators_detected: list[dict]
    last_updated: datetime

    model_config = {"from_attributes": True}


# ── Restriction ───────────────────────────────────────────────────────────────

class RestrictionOut(BaseModel):
    id: str
    client_id: str
    level: int
    restricted_capabilities: list[str]
    allowed_capabilities: list[str]
    reason: str
    client_message: str
    gemini_reasoning: Optional[str]
    trigger_type: Optional[str]
    is_active: bool
    triggered_at: datetime

    model_config = {"from_attributes": True}


class RestrictionOverride(BaseModel):
    new_level: int
    reason: str
    analyst: str = "human_analyst"


# ── Investigation ─────────────────────────────────────────────────────────────

class InvestigationSummary(BaseModel):
    id: str
    client_id: str
    client_name: str
    status: str
    classification: Optional[str]
    confidence: Optional[float]
    is_coordinated: bool
    correlated_client_ids: list[str]
    response_level: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class STRDraftOut(BaseModel):
    id: str
    investigation_id: str
    subject_profile: str
    activity_description: str
    indicators_present: list[dict]
    behavioral_context: str
    network_analysis: str
    recommendation: str
    key_uncertainties: list[str]
    narrative_full: str
    tagged_transactions: list[dict]
    money_flow: Optional[dict]
    ai_confidence: Optional[float]
    ai_reasoning_chain: Optional[str]
    status: str
    analyst_notes: Optional[str]
    decided_at: Optional[datetime]
    decided_by: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class InvestigationDetail(BaseModel):
    id: str
    client_id: str
    client_name: str
    trigger_event: Optional[dict]
    response_level: int
    status: str
    correlated_client_ids: list[str]
    is_coordinated: bool
    network_graph: Optional[dict]
    classification: Optional[str]
    confidence: Optional[float]
    reasoning: Optional[str]
    str_draft: Optional[STRDraftOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TriggerInvestigationRequest(BaseModel):
    trigger_type: str = "manual"
    notes: Optional[str] = None


class STRDecision(BaseModel):
    decision: str          # "approve" | "dismiss"
    analyst: str = "human_analyst"
    notes: Optional[str] = None


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_clients: int
    clients_by_restriction_level: dict[str, int]
    open_investigations: int
    str_drafts_pending: int
    strs_filed_this_month: int
    recent_activity: list[dict]


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditEntryOut(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    actor: str
    timestamp: datetime
    details: Optional[dict]

    model_config = {"from_attributes": True}
