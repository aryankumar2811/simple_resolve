"""
Seed script — populates the database with synthetic data for all demo scenarios.

Run with:
    cd backend && python -m app.seed.seed_data

Scenarios seeded:
  A — Alice Normal   : Clean baseline (payroll investor, TFSA)
  B — Bob Struct     : Structuring (3 x near-$10K deposits + crypto conversion)
  C — Carl Layer     : Crypto layering (fiat → BTC → ETH → external in 4 hrs)
  D — Dana Cooper  ┐
  E — Eve Smith    ├─ Coordinated group (all send to wallets in same 0x7a3* cluster)
  F — Frank Wilson ┘
  G — Grace Hill     : Income inconsistency (large deposits vs $32K stated income)
"""

import sys
import os

# Allow running as `python -m app.seed.seed_data` from the backend directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, create_tables
from app.models import (
    AccountRestriction,
    AuditEntry,
    BehavioralProfile,
    Client,
    Investigation,
    STRDraft,
    Transaction,
)
from app.services.layer3_orchestrator import run_investigation

# ── Helpers ──────────────────────────────────────────────────────────────────

# Fixed "today" for reproducible demo data
SEED_DATE = datetime(2026, 2, 28, 18, 0, 0)


def _dt(days_ago: int, hour: int = 10, minute: int = 0) -> datetime:
    """Return a datetime that is `days_ago` days before SEED_DATE."""
    return SEED_DATE - timedelta(days=days_ago) + timedelta(hours=hour - 10, minutes=minute)


def _risk_history(base: float, spike_start_days_ago: int = 0, spike_value: float = 0.0) -> list:
    """
    Generate 30 daily risk score data points for the frontend chart.
    Optionally spike the score in the last `spike_start_days_ago` days.
    """
    history = []
    for i in range(29, -1, -1):  # day 29 (oldest) → day 0 (today)
        date_str = (SEED_DATE - timedelta(days=i)).strftime("%Y-%m-%d")
        if spike_start_days_ago > 0 and i <= spike_start_days_ago:
            # Linear ramp from base toward spike_value
            progress = 1 - (i / spike_start_days_ago)
            score = round(base + (spike_value - base) * progress, 3)
        else:
            # Stable baseline with tiny random-looking wobble
            wobble = 0.01 * ((i * 7 + 3) % 5 - 2)
            score = round(max(0.0, min(1.0, base + wobble)), 3)
        history.append({"date": date_str, "score": score})
    return history


# ── Client creation ───────────────────────────────────────────────────────────

def _create_clients(db: Session) -> dict[str, Client]:
    clients_data = [
        dict(
            id=str(uuid.uuid4()),
            name="Alice Normal",
            date_of_birth="1988-04-12",
            stated_income=65000.0,
            occupation="Software Developer",
            kyc_level="enhanced",
            account_opened_at=_dt(365),
            products_held=["chequing", "tfsa"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Bob Struct",
            date_of_birth="1993-09-22",
            stated_income=42000.0,
            occupation="Retail Associate",
            kyc_level="standard",
            account_opened_at=_dt(275),
            products_held=["chequing", "crypto"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Carl Layer",
            date_of_birth="1997-02-05",
            stated_income=38000.0,
            occupation="Freelance Designer",
            kyc_level="standard",
            account_opened_at=_dt(90),
            products_held=["chequing", "crypto"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Dana Cooper",
            date_of_birth="1991-11-30",
            stated_income=36000.0,
            occupation="Sales Associate",
            kyc_level="standard",
            account_opened_at=_dt(75),
            products_held=["chequing", "crypto"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Eve Smith",
            date_of_birth="1995-07-18",
            stated_income=34000.0,
            occupation="Customer Service",
            kyc_level="standard",
            account_opened_at=_dt(65),
            products_held=["chequing", "crypto"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Frank Wilson",
            date_of_birth="1989-03-14",
            stated_income=37000.0,
            occupation="Warehouse Worker",
            kyc_level="standard",
            account_opened_at=_dt(58),
            products_held=["chequing", "crypto"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Grace Hill",
            date_of_birth="1985-12-01",
            stated_income=32000.0,
            occupation="Administrative Assistant",
            kyc_level="standard",
            account_opened_at=_dt(150),
            products_held=["chequing"],
        ),
    ]

    clients = {}
    for data in clients_data:
        client = Client(**data)
        db.add(client)
        clients[data["name"].split()[0].lower()] = client

    db.flush()
    return clients


# ── Transactions ──────────────────────────────────────────────────────────────

def _txn(client_id: str, type_: str, product: str, amount: float, timestamp: datetime,
         source: str = None, destination: str = None, counterparty_name: str = None,
         metadata: dict = None) -> Transaction:
    return Transaction(
        id=str(uuid.uuid4()),
        client_id=client_id,
        type=type_,
        product=product,
        amount=amount,
        timestamp=timestamp,
        source=source,
        destination=destination,
        counterparty_name=counterparty_name,
        txn_metadata=metadata or {},
    )


def _create_transactions(db: Session, clients: dict) -> None:
    txns = []

    # ── Alice Normal: clean payroll investor ──────────────────────────────────
    alice_id = clients["alice"].id
    # 26 bi-weekly payroll deposits over 12 months
    for i in range(26):
        amount = 2400.0 + (i % 4) * 50  # slight variation
        txns.append(_txn(alice_id, "e_transfer_in", "chequing", amount,
                         _dt(365 - i * 14, hour=9),
                         source="external", destination="chequing",
                         counterparty_name="Northern Data Inc"))
    # Monthly TFSA contributions
    for i in range(12):
        txns.append(_txn(alice_id, "investment_buy", "tfsa", 500.0,
                         _dt(350 - i * 30, hour=11),
                         source="chequing", destination="tfsa",
                         counterparty_name="Wealthsimple TFSA"))
    # Regular e-transfer outs to known friends
    for i in range(10):
        amount = 150.0 + (i % 5) * 80
        name = ["Sarah K.", "Mike T.", "Sarah K.", "Mike T.", "James P."][i % 5]
        txns.append(_txn(alice_id, "e_transfer_out", "chequing", amount,
                         _dt(360 - i * 35, hour=19),
                         source="chequing", destination="external",
                         counterparty_name=name))

    # ── Bob Struct: structuring pattern ──────────────────────────────────────
    bob_id = clients["bob"].id
    # 8 months of normal deposits (~$1,500/month)
    for i in range(8):
        amount = 1400.0 + (i % 3) * 70
        txns.append(_txn(bob_id, "e_transfer_in", "chequing", amount,
                         _dt(275 - i * 30, hour=9),
                         source="external", destination="chequing",
                         counterparty_name="RiverSide Retail LLC"))
        # A few small crypto buys from normal funds
        if i % 3 == 0:
            txns.append(_txn(bob_id, "crypto_buy", "crypto", 200.0,
                             _dt(273 - i * 30, hour=14),
                             source="chequing", destination="crypto"))

    # SUSPICIOUS ACTIVITY — three near-$10K deposits + immediate crypto conversion + send
    suspicious_bob = [
        (14, 9400.0, "0xB1a2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"),
        (11, 9600.0, "0xB2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1"),
        (7,  9500.0, "0xB3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2"),
    ]
    for days_ago, dep_amount, wallet in suspicious_bob:
        txns.append(_txn(bob_id, "e_transfer_in", "chequing", dep_amount,
                         _dt(days_ago, hour=8, minute=15),
                         source="external", destination="chequing",
                         counterparty_name="Unknown Sender",
                         metadata={"flagged": True}))
        txns.append(_txn(bob_id, "crypto_buy", "crypto", dep_amount - 50,
                         _dt(days_ago, hour=8, minute=45),
                         source="chequing", destination="crypto",
                         metadata={"asset": "BTC"}))
        # Swap BTC → ETH
        txns.append(_txn(bob_id, "crypto_sell", "crypto", dep_amount - 55,
                         _dt(days_ago, hour=9, minute=30),
                         source="crypto_btc", destination="crypto_eth",
                         metadata={"from_asset": "BTC", "to_asset": "ETH"}))
        txns.append(_txn(bob_id, "crypto_send", "crypto", dep_amount - 60,
                         _dt(days_ago, hour=10, minute=20),
                         source="crypto", destination=wallet,
                         metadata={"asset": "ETH", "external_wallet": wallet}))

    # ── Carl Layer: crypto layering chain ────────────────────────────────────
    carl_id = clients["carl"].id
    # 2 months of thin history
    for i in range(2):
        txns.append(_txn(carl_id, "e_transfer_in", "chequing", 1200.0,
                         _dt(80 - i * 35, hour=10),
                         source="external", destination="chequing",
                         counterparty_name="Freelance Client A"))

    layering_carl = [
        (18, 8000.0, "0xC1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0"),
        (6,  7200.0, "0xC2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1"),
    ]
    for days_ago, dep_amount, wallet in layering_carl:
        # Fiat deposit
        txns.append(_txn(carl_id, "deposit", "chequing", dep_amount,
                         _dt(days_ago, hour=9, minute=0),
                         source="external", destination="chequing",
                         metadata={"flagged": True}))
        # Buy BTC 1 hour later
        txns.append(_txn(carl_id, "crypto_buy", "crypto", dep_amount,
                         _dt(days_ago, hour=10, minute=5),
                         source="chequing", destination="crypto",
                         metadata={"asset": "BTC"}))
        # Swap BTC → ETH 2 hours later
        txns.append(_txn(carl_id, "crypto_sell", "crypto", dep_amount - 30,
                         _dt(days_ago, hour=11, minute=15),
                         source="crypto_btc", destination="crypto_eth",
                         metadata={"from_asset": "BTC", "to_asset": "ETH"}))
        # Send ETH to external wallet 4 hours after deposit
        txns.append(_txn(carl_id, "crypto_send", "crypto", dep_amount - 50,
                         _dt(days_ago, hour=13, minute=10),
                         source="crypto", destination=wallet,
                         metadata={"asset": "ETH", "external_wallet": wallet,
                                   "minutes_since_deposit": 245}))

    # ── Dana, Eve, Frank: coordinated group ──────────────────────────────────
    # Wallet cluster: all 0x7a3* prefix — the correlation engine will link these
    coordinated = [
        (clients["dana"].id, 13, 9200.0, "0x7a3f4b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4"),
        (clients["eve"].id,  12, 8800.0, "0x7a41e2a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5"),
        (clients["frank"].id, 10, 9500.0, "0x7a39f1d3e4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9"),
    ]
    for client_id_owner, days_ago, dep_amount, wallet in coordinated:
        # Thin history: 2 small deposits
        for i in range(2):
            txns.append(_txn(client_id_owner, "e_transfer_in", "chequing", 400.0 + i * 100,
                             _dt(50 - i * 20, hour=11),
                             source="external", destination="chequing",
                             counterparty_name="Cash App Transfer"))
        # Suspicious deposit + immediate crypto conversion + external send
        txns.append(_txn(client_id_owner, "e_transfer_in", "chequing", dep_amount,
                         _dt(days_ago, hour=8, minute=30),
                         source="external", destination="chequing",
                         counterparty_name="Unknown Sender",
                         metadata={"flagged": True}))
        txns.append(_txn(client_id_owner, "crypto_buy", "crypto", dep_amount - 20,
                         _dt(days_ago, hour=9, minute=10),
                         source="chequing", destination="crypto",
                         metadata={"asset": "ETH"}))
        txns.append(_txn(client_id_owner, "crypto_send", "crypto", dep_amount - 40,
                         _dt(days_ago, hour=9, minute=55),
                         source="crypto", destination=wallet,
                         metadata={"asset": "ETH", "external_wallet": wallet,
                                   "wallet_cluster": "0x7a3*"}))

    # ── Grace Hill: income inconsistency ─────────────────────────────────────
    grace_id = clients["grace"].id
    # 4 months of normal low-volume deposits
    for i in range(5):
        txns.append(_txn(grace_id, "e_transfer_in", "chequing", 780.0 + (i % 3) * 30,
                         _dt(150 - i * 28, hour=10),
                         source="external", destination="chequing",
                         counterparty_name="Metro Staffing Agency"))
        txns.append(_txn(grace_id, "bill_payment", "chequing", 120.0 + (i % 2) * 40,
                         _dt(148 - i * 28, hour=16),
                         source="chequing", destination="Rogers Communications",
                         counterparty_name="Rogers Communications"))

    # Suspicious: 3 large deposits from NEW counterparties
    suspicious_grace = [
        (10, 7000.0, "Apex Trading Ltd"),
        (5,  8500.0, "Global Finance Co"),
        (1,  6800.0, "Pacific Holdings LLC"),
    ]
    for days_ago, amount, cp_name in suspicious_grace:
        txns.append(_txn(grace_id, "e_transfer_in", "chequing", amount,
                         _dt(days_ago, hour=14, minute=20),
                         source="external", destination="chequing",
                         counterparty_name=cp_name,
                         metadata={"new_counterparty": True, "flagged": True}))

    for t in txns:
        db.add(t)
    db.flush()


# ── Behavioral profiles ───────────────────────────────────────────────────────

def _create_profiles(db: Session, clients: dict) -> None:
    profiles = [
        BehavioralProfile(
            id=str(uuid.uuid4()),
            client_id=clients["alice"].id,
            avg_deposit_amount=2490.0,
            avg_withdrawal_amount=280.0,
            deposit_frequency_per_week=0.5,
            total_inflow_30d=4900.0,
            total_outflow_30d=560.0,
            known_counterparties=[
                {"name": "Northern Data Inc", "type": "sender",
                 "last_seen": "2026-02-14", "frequency": 26},
                {"name": "Sarah K.", "type": "recipient",
                 "last_seen": "2026-01-10", "frequency": 4},
                {"name": "Mike T.", "type": "recipient",
                 "last_seen": "2025-12-20", "frequency": 3},
            ],
            risk_scores={"chequing": 0.04, "tfsa": 0.02, "overall": 0.03},
            overall_risk_score=0.03,
            archetype="payroll_depositor",
            archetype_trajectory="stable",
            risk_trend="stable",
            risk_history=_risk_history(base=0.04),
            indicators_detected=[],
            last_updated=SEED_DATE,
        ),
        BehavioralProfile(
            id=str(uuid.uuid4()),
            client_id=clients["bob"].id,
            avg_deposit_amount=1510.0,
            avg_withdrawal_amount=120.0,
            deposit_frequency_per_week=0.28,
            total_inflow_30d=28500.0,   # the 3 suspicious deposits
            total_outflow_30d=28400.0,  # crypto sends
            known_counterparties=[
                {"name": "RiverSide Retail LLC", "type": "sender",
                 "last_seen": "2025-12-01", "frequency": 8},
                {"name": "Unknown Sender", "type": "sender",
                 "last_seen": "2026-02-21", "frequency": 3},
            ],
            risk_scores={"chequing": 0.88, "crypto": 0.86, "overall": 0.87},
            overall_risk_score=0.87,
            archetype="mule_like",
            archetype_trajectory="shifting_negative",
            risk_trend="rising",
            risk_history=_risk_history(base=0.08, spike_start_days_ago=14, spike_value=0.87),
            indicators_detected=[
                {"indicator": "structuring",
                 "detected_at": "2026-02-14", "confidence": 0.91},
                {"indicator": "rapid_crypto_conversion",
                 "detected_at": "2026-02-14", "confidence": 0.88},
                {"indicator": "income_inconsistency",
                 "detected_at": "2026-02-21", "confidence": 0.79},
            ],
            proactive_actions=[
                {"timestamp": _dt(14, hour=8, minute=50).isoformat(), "action": "notification_sent",
                 "label": "Client notified: verification step added for large transfers",
                 "trigger": "Level 2 guardrail activated", "channel": "push + email", "status": "delivered"},
                {"timestamp": _dt(14, hour=9, minute=5).isoformat(), "action": "step_up_auth",
                 "label": "Step-up authentication activated for outbound transfers",
                 "trigger": "Level 3 escalation — structuring pattern", "channel": "biometric + 2FA", "status": "active"},
                {"timestamp": _dt(7, hour=10, minute=45).isoformat(), "action": "follow_up_call_scheduled",
                 "label": "Agent scheduled verification call",
                 "trigger": "Level 3 restriction applied", "channel": "phone", "status": "completed"},
            ],
            last_updated=SEED_DATE,
        ),
        BehavioralProfile(
            id=str(uuid.uuid4()),
            client_id=clients["carl"].id,
            avg_deposit_amount=1100.0,
            avg_withdrawal_amount=0.0,
            deposit_frequency_per_week=0.12,
            total_inflow_30d=15200.0,
            total_outflow_30d=15120.0,
            known_counterparties=[
                {"name": "Freelance Client A", "type": "sender",
                 "last_seen": "2025-12-15", "frequency": 2},
            ],
            risk_scores={"chequing": 0.82, "crypto": 0.91, "overall": 0.87},
            overall_risk_score=0.87,
            archetype="mule_like",
            archetype_trajectory="shifting_negative",
            risk_trend="rising",
            risk_history=_risk_history(base=0.06, spike_start_days_ago=20, spike_value=0.87),
            indicators_detected=[
                {"indicator": "layering",
                 "detected_at": "2026-02-10", "confidence": 0.93},
                {"indicator": "rapid_crypto_conversion",
                 "detected_at": "2026-02-10", "confidence": 0.95},
                {"indicator": "income_inconsistency",
                 "detected_at": "2026-02-22", "confidence": 0.81},
            ],
            proactive_actions=[
                {"timestamp": _dt(18, hour=9, minute=5).isoformat(), "action": "notification_sent",
                 "label": "Client notified: crypto transfers temporarily paused",
                 "trigger": "Layering pattern detected", "channel": "push + email", "status": "delivered"},
                {"timestamp": _dt(18, hour=9, minute=20).isoformat(), "action": "step_up_auth",
                 "label": "Step-up authentication activated for all crypto operations",
                 "trigger": "Level 3 escalation — layering chain", "channel": "biometric", "status": "active"},
                {"timestamp": _dt(6, hour=13, minute=30).isoformat(), "action": "follow_up_call_scheduled",
                 "label": "Agent scheduled identity verification call",
                 "trigger": "Level 3 restriction applied", "channel": "phone", "status": "scheduled"},
            ],
            last_updated=SEED_DATE,
        ),
        BehavioralProfile(
            id=str(uuid.uuid4()),
            client_id=clients["dana"].id,
            avg_deposit_amount=500.0,
            avg_withdrawal_amount=0.0,
            deposit_frequency_per_week=0.1,
            total_inflow_30d=9200.0,
            total_outflow_30d=9160.0,
            known_counterparties=[
                {"name": "Cash App Transfer", "type": "sender",
                 "last_seen": "2026-01-20", "frequency": 2},
                {"name": "Unknown Sender", "type": "sender",
                 "last_seen": "2026-02-15", "frequency": 1},
            ],
            risk_scores={"chequing": 0.81, "crypto": 0.84, "overall": 0.83},
            overall_risk_score=0.83,
            archetype="mule_like",
            archetype_trajectory="shifting_negative",
            risk_trend="rising",
            risk_history=_risk_history(base=0.07, spike_start_days_ago=13, spike_value=0.83),
            indicators_detected=[
                {"indicator": "structuring", "detected_at": "2026-02-15", "confidence": 0.85},
                {"indicator": "rapid_crypto_conversion",
                 "detected_at": "2026-02-15", "confidence": 0.89},
            ],
            proactive_actions=[
                {"timestamp": _dt(13, hour=10, minute=15).isoformat(), "action": "notification_sent",
                 "label": "Client notified: crypto transfers paused pending review",
                 "trigger": "Coordinated wallet cluster detected", "channel": "push + email", "status": "delivered"},
                {"timestamp": _dt(13, hour=10, minute=30).isoformat(), "action": "step_up_auth",
                 "label": "Step-up authentication required for all outbound transfers",
                 "trigger": "Level 3 — coordinated activity", "channel": "2FA", "status": "active"},
            ],
            last_updated=SEED_DATE,
        ),
        BehavioralProfile(
            id=str(uuid.uuid4()),
            client_id=clients["eve"].id,
            avg_deposit_amount=467.0,
            avg_withdrawal_amount=0.0,
            deposit_frequency_per_week=0.09,
            total_inflow_30d=8800.0,
            total_outflow_30d=8760.0,
            known_counterparties=[
                {"name": "Cash App Transfer", "type": "sender",
                 "last_seen": "2026-01-08", "frequency": 2},
                {"name": "Unknown Sender", "type": "sender",
                 "last_seen": "2026-02-16", "frequency": 1},
            ],
            risk_scores={"chequing": 0.80, "crypto": 0.83, "overall": 0.82},
            overall_risk_score=0.82,
            archetype="mule_like",
            archetype_trajectory="shifting_negative",
            risk_trend="rising",
            risk_history=_risk_history(base=0.06, spike_start_days_ago=12, spike_value=0.82),
            indicators_detected=[
                {"indicator": "structuring", "detected_at": "2026-02-16", "confidence": 0.83},
                {"indicator": "rapid_crypto_conversion",
                 "detected_at": "2026-02-16", "confidence": 0.87},
            ],
            proactive_actions=[
                {"timestamp": _dt(12, hour=10, minute=5).isoformat(), "action": "notification_sent",
                 "label": "Client notified: crypto transfers paused pending review",
                 "trigger": "Coordinated wallet cluster detected", "channel": "push + email", "status": "delivered"},
                {"timestamp": _dt(12, hour=10, minute=20).isoformat(), "action": "step_up_auth",
                 "label": "Step-up authentication required for all outbound transfers",
                 "trigger": "Level 3 — coordinated activity", "channel": "2FA", "status": "active"},
            ],
            last_updated=SEED_DATE,
        ),
        BehavioralProfile(
            id=str(uuid.uuid4()),
            client_id=clients["frank"].id,
            avg_deposit_amount=533.0,
            avg_withdrawal_amount=0.0,
            deposit_frequency_per_week=0.1,
            total_inflow_30d=9500.0,
            total_outflow_30d=9460.0,
            known_counterparties=[
                {"name": "Cash App Transfer", "type": "sender",
                 "last_seen": "2026-01-15", "frequency": 2},
                {"name": "Unknown Sender", "type": "sender",
                 "last_seen": "2026-02-18", "frequency": 1},
            ],
            risk_scores={"chequing": 0.82, "crypto": 0.85, "overall": 0.84},
            overall_risk_score=0.84,
            archetype="mule_like",
            archetype_trajectory="shifting_negative",
            risk_trend="rising",
            risk_history=_risk_history(base=0.07, spike_start_days_ago=10, spike_value=0.84),
            indicators_detected=[
                {"indicator": "structuring", "detected_at": "2026-02-18", "confidence": 0.86},
                {"indicator": "rapid_crypto_conversion",
                 "detected_at": "2026-02-18", "confidence": 0.90},
            ],
            proactive_actions=[
                {"timestamp": _dt(10, hour=10, minute=35).isoformat(), "action": "notification_sent",
                 "label": "Client notified: crypto transfers paused pending review",
                 "trigger": "Coordinated wallet cluster detected", "channel": "push + email", "status": "delivered"},
                {"timestamp": _dt(10, hour=10, minute=45).isoformat(), "action": "step_up_auth",
                 "label": "Step-up authentication required for all outbound transfers",
                 "trigger": "Level 3 — coordinated activity", "channel": "2FA", "status": "active"},
            ],
            last_updated=SEED_DATE,
        ),
        BehavioralProfile(
            id=str(uuid.uuid4()),
            client_id=clients["grace"].id,
            avg_deposit_amount=790.0,
            avg_withdrawal_amount=140.0,
            deposit_frequency_per_week=0.25,
            total_inflow_30d=22300.0,   # 3 suspicious deposits
            total_outflow_30d=280.0,
            known_counterparties=[
                {"name": "Metro Staffing Agency", "type": "sender",
                 "last_seen": "2026-01-05", "frequency": 5},
                {"name": "Apex Trading Ltd", "type": "sender",
                 "last_seen": "2026-02-18", "frequency": 1},
                {"name": "Global Finance Co", "type": "sender",
                 "last_seen": "2026-02-23", "frequency": 1},
                {"name": "Pacific Holdings LLC", "type": "sender",
                 "last_seen": "2026-02-27", "frequency": 1},
            ],
            risk_scores={"chequing": 0.73, "overall": 0.73},
            overall_risk_score=0.73,
            archetype="payroll_depositor",
            archetype_trajectory="shifting_negative",
            risk_trend="rising",
            risk_history=_risk_history(base=0.06, spike_start_days_ago=12, spike_value=0.73),
            indicators_detected=[
                {"indicator": "income_inconsistency",
                 "detected_at": "2026-02-18", "confidence": 0.82},
                {"indicator": "new_counterparty_burst",
                 "detected_at": "2026-02-23", "confidence": 0.78},
            ],
            proactive_actions=[
                {"timestamp": _dt(10, hour=14, minute=35).isoformat(), "action": "notification_sent",
                 "label": "Client notified: verification step added for large incoming transfers",
                 "trigger": "Level 2 guardrail — income inconsistency", "channel": "push + email", "status": "delivered"},
                {"timestamp": _dt(5, hour=14, minute=35).isoformat(), "action": "info_request_sent",
                 "label": "Information request sent: source of funds documentation required",
                 "trigger": "Level 2 guardrail — income inconsistency", "channel": "secure message + email",
                 "status": "awaiting_response"},
            ],
            last_updated=SEED_DATE,
        ),
    ]

    for p in profiles:
        db.add(p)
    db.flush()


# ── Account restrictions ──────────────────────────────────────────────────────

def _create_restrictions(db: Session, clients: dict) -> None:
    restrictions = [
        # Bob — Level 3: crypto restricted, fiat unaffected
        AccountRestriction(
            id=str(uuid.uuid4()),
            client_id=clients["bob"].id,
            level=3,
            restricted_capabilities=[
                "crypto_send_external",
                "crypto_buy",
                "crypto_sell",
            ],
            allowed_capabilities=[
                "chequing_deposit",
                "e_transfer_in",
                "bill_payment",
                "investment_buy",
                "investment_sell",
            ],
            reason="Structuring pattern detected: 3 deposits near $10,000 threshold followed by "
                   "immediate crypto conversion and external wallet transfer.",
            client_message="We've temporarily paused external crypto transfers while we verify "
                           "some recent activity. Your chequing account, investments, and all "
                           "other services are working normally. We'll update you within 24 hours.",
            gemini_reasoning="Trigger involves crypto-specific layering. Chequing and TFSA products "
                             "show no independent suspicious activity and should remain accessible "
                             "to avoid disproportionate client impact.",
            trigger_type="structuring_crypto_layering",
            is_active=True,
            triggered_at=_dt(7, hour=10, minute=45),
        ),
        # Carl — Level 3: crypto restricted
        AccountRestriction(
            id=str(uuid.uuid4()),
            client_id=clients["carl"].id,
            level=3,
            restricted_capabilities=[
                "crypto_send_external",
                "crypto_buy",
                "crypto_sell",
            ],
            allowed_capabilities=[
                "chequing_deposit",
                "e_transfer_in",
                "bill_payment",
            ],
            reason="Crypto layering chain detected: fiat → BTC → ETH → external wallet "
                   "completed within 4 hours on two separate occasions.",
            client_message="We've temporarily paused external crypto transfers while we verify "
                           "recent account activity. Your chequing account remains fully "
                           "accessible. A specialist will review your account within 24 hours.",
            gemini_reasoning="The suspicious activity is entirely within the crypto product. "
                             "Chequing shows only minimal, legitimate activity. "
                             "Full account freeze would be disproportionate.",
            trigger_type="crypto_layering",
            is_active=True,
            triggered_at=_dt(6, hour=13, minute=30),
        ),
        # Dana — Level 3: crypto restricted (coordinated group)
        AccountRestriction(
            id=str(uuid.uuid4()),
            client_id=clients["dana"].id,
            level=3,
            restricted_capabilities=["crypto_send_external", "crypto_buy"],
            allowed_capabilities=["chequing_deposit", "e_transfer_in", "bill_payment"],
            reason="Coordinated activity: funds sent to wallet cluster linked to two other "
                   "flagged accounts.",
            client_message="We've temporarily paused external crypto transfers pending a "
                           "verification review. All other account features remain available.",
            trigger_type="coordinated_crypto",
            is_active=True,
            triggered_at=_dt(13, hour=10, minute=10),
        ),
        # Eve — Level 3: crypto restricted (coordinated group)
        AccountRestriction(
            id=str(uuid.uuid4()),
            client_id=clients["eve"].id,
            level=3,
            restricted_capabilities=["crypto_send_external", "crypto_buy"],
            allowed_capabilities=["chequing_deposit", "e_transfer_in", "bill_payment"],
            reason="Coordinated activity: funds sent to wallet cluster linked to two other "
                   "flagged accounts.",
            client_message="We've temporarily paused external crypto transfers pending a "
                           "verification review. All other account features remain available.",
            trigger_type="coordinated_crypto",
            is_active=True,
            triggered_at=_dt(12, hour=10, minute=0),
        ),
        # Frank — Level 3: crypto restricted (coordinated group)
        AccountRestriction(
            id=str(uuid.uuid4()),
            client_id=clients["frank"].id,
            level=3,
            restricted_capabilities=["crypto_send_external", "crypto_buy"],
            allowed_capabilities=["chequing_deposit", "e_transfer_in", "bill_payment"],
            reason="Coordinated activity: funds sent to wallet cluster linked to two other "
                   "flagged accounts.",
            client_message="We've temporarily paused external crypto transfers pending a "
                           "verification review. All other account features remain available.",
            trigger_type="coordinated_crypto",
            is_active=True,
            triggered_at=_dt(10, hour=10, minute=30),
        ),
        # Grace — Level 2: step-up auth for large inbound transfers
        AccountRestriction(
            id=str(uuid.uuid4()),
            client_id=clients["grace"].id,
            level=2,
            restricted_capabilities=["e_transfer_in_large_unverified"],
            allowed_capabilities=[
                "chequing_deposit",
                "e_transfer_in_known",
                "bill_payment",
                "e_transfer_out",
            ],
            reason="Income inconsistency: inflow over 10 days ($22,300) represents 70% of "
                   "stated annual income. Three new counterparties appeared simultaneously.",
            client_message="For your security, we've added a verification step for large "
                           "incoming transfers from new sources. All other account features "
                           "are working normally.",
            trigger_type="income_inconsistency",
            is_active=True,
            triggered_at=_dt(5, hour=14, minute=30),
        ),
    ]

    for r in restrictions:
        db.add(r)
    db.flush()


# ── Audit entries for seeded restrictions ─────────────────────────────────────

def _create_audit_entries(db: Session, clients: dict) -> None:
    entries = []
    flagged = ["bob", "carl", "dana", "eve", "frank", "grace"]
    for key in flagged:
        c = clients[key]
        entries.append(AuditEntry(
            id=str(uuid.uuid4()),
            entity_type="restriction",
            entity_id=c.id,
            action="restriction_applied",
            actor="system:layer2_response_engine",
            timestamp=SEED_DATE - timedelta(days=5),
            details={"client_name": c.name, "seeded": True},
        ))
    for e in entries:
        db.add(e)
    db.flush()


# ── Pre-seed investigations ───────────────────────────────────────────────────

def _seed_investigations(db: Session, clients: dict) -> None:
    """
    Pre-seed completed investigations for all non-clean clients so the
    investigations page and client profiles show data on first load.
    Dana/Eve/Frank are seeded together so cross-client correlation fires.
    """
    # Clients that should have investigations (level 3: full pipeline; level 2: fast track)
    level3_clients = ["bob", "carl", "dana", "eve", "frank"]
    level2_clients = ["grace"]

    all_inv_clients = level3_clients + level2_clients

    for key in all_inv_clients:
        c = clients[key]
        inv = Investigation(
            id=str(uuid.uuid4()),
            client_id=c.id,
            trigger_event={
                "trigger_type": "automatic",
                "source": "layer2_response_engine",
                "notes": "Pre-seeded investigation for demo",
            },
            response_level=3 if key in level3_clients else 2,
            status="open",
            step_log=[],
        )
        db.add(inv)
        db.add(AuditEntry(
            id=str(uuid.uuid4()),
            entity_type="investigation",
            entity_id=inv.id,
            action="investigation_auto_triggered",
            actor="system:layer2_response_engine",
            timestamp=SEED_DATE - timedelta(days=3),
            details={"client_name": c.name, "seeded": True},
        ))
        db.flush()

        print(f"  Running investigation pipeline for {c.name}...")
        try:
            run_investigation(inv.id, db)
            db.commit()
            print(f"    Done — status: {db.query(Investigation).get(inv.id).status}")
        except Exception as exc:
            db.rollback()
            print(f"    WARNING: Investigation failed for {c.name}: {exc}")


# ── Main entrypoint ───────────────────────────────────────────────────────────

def seed_all(db: Session) -> None:
    print("Clearing existing data...")
    # Delete in FK-safe order
    db.query(AuditEntry).delete()
    db.query(STRDraft).delete()
    db.query(Investigation).delete()
    db.query(AccountRestriction).delete()
    db.query(BehavioralProfile).delete()
    db.query(Transaction).delete()
    db.query(Client).delete()
    db.commit()

    print("Creating clients...")
    clients = _create_clients(db)

    print("Creating transactions...")
    _create_transactions(db, clients)

    print("Creating behavioral profiles...")
    _create_profiles(db, clients)

    print("Creating restrictions for flagged clients...")
    _create_restrictions(db, clients)

    print("Creating audit entries...")
    _create_audit_entries(db, clients)

    db.commit()

    print("Running investigation pipeline for flagged clients...")
    _seed_investigations(db, clients)

    print(f"\nSeed complete. {len(clients)} clients created:")
    for key, c in clients.items():
        print(f"  {c.id}  {c.name}")


if __name__ == "__main__":
    create_tables()
    with SessionLocal() as db:
        seed_all(db)
