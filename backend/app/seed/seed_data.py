"""
Seed script — populates the database with clients and transactions for all demo scenarios.
Profiles, restrictions, and investigations are NOT pre-seeded — they are created when
the analyst clicks "Run Simulation" on the dashboard.

Run with:
    cd backend && python -m app.seed.seed_data

Scenarios:
  1 — Alice Chen     : Clean payroll depositor                → L0 auto-resolved
  2 — Bob Kamara     : Structuring (3x near-$10K deposits)    → L3 full investigation + STR
  3 — Carl Mendez    : Crypto layering (fiat→crypto in 4hrs)  → L3 full investigation + STR
  4 — Dana Osei      : Coordinated group leader               → L3 cross-client investigation
  5 — Eve Johansson  : Coordinated group participant          → L3 cross-client investigation
  6 — Frank Lim      : Coordinated minor participant          → L2 step-up auth + guardrail
  7 — Grace Okonkwo  : Income inconsistency                   → L3 investigation + STR
  8 — Henry Park     : Salary spike (auto-resolve)            → L0 de-escalated immediately
  9 — Isabel Torres  : Minor structuring pattern              → L2 guardrail only
 10 — James Okafor   : Mule account (many senders→1 wallet)  → L3 full investigation + STR
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Client, Transaction

# ── Helpers ──────────────────────────────────────────────────────────────────

# Use current time so "within 7 days" detection always works
SEED_NOW = datetime.utcnow()


def _dt(days_ago: float, hour: int = 10, minute: int = 0) -> datetime:
    """Return a datetime `days_ago` days before SEED_NOW."""
    return SEED_NOW - timedelta(days=days_ago, hours=-(hour - 10), minutes=-minute)


def _txn(
    client_id: str,
    type_: str,
    product: str,
    amount: float,
    timestamp: datetime,
    source: str = None,
    destination: str = None,
    counterparty_name: str = None,
    metadata: dict = None,
) -> Transaction:
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


# ── Clients ───────────────────────────────────────────────────────────────────

def _create_clients(db: Session) -> dict[str, Client]:
    clients_data = [
        dict(
            id=str(uuid.uuid4()),
            name="Alice Chen",
            date_of_birth="1988-04-12",
            stated_income=72000.0,
            occupation="Software Developer",
            kyc_level="enhanced",
            account_opened_at=_dt(480),
            products_held=["chequing", "tfsa"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Bob Kamara",
            date_of_birth="1993-09-22",
            stated_income=56000.0,
            occupation="Retail Manager",
            kyc_level="standard",
            account_opened_at=_dt(310),
            products_held=["chequing", "crypto"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Carl Mendez",
            date_of_birth="1997-02-05",
            stated_income=62000.0,
            occupation="Freelance Consultant",
            kyc_level="standard",
            account_opened_at=_dt(95),
            products_held=["chequing", "crypto"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Dana Osei",
            date_of_birth="1991-11-30",
            stated_income=42000.0,
            occupation="Sales Representative",
            kyc_level="standard",
            account_opened_at=_dt(80),
            products_held=["chequing", "crypto"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Eve Johansson",
            date_of_birth="1995-07-18",
            stated_income=38000.0,
            occupation="Customer Service Agent",
            kyc_level="standard",
            account_opened_at=_dt(70),
            products_held=["chequing", "crypto"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Frank Lim",
            date_of_birth="1989-03-14",
            stated_income=41000.0,
            occupation="Warehouse Supervisor",
            kyc_level="standard",
            account_opened_at=_dt(62),
            products_held=["chequing", "crypto"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Grace Okonkwo",
            date_of_birth="1985-12-01",
            stated_income=38000.0,
            occupation="Administrative Assistant",
            kyc_level="standard",
            account_opened_at=_dt(160),
            products_held=["chequing"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Henry Park",
            date_of_birth="1982-06-15",
            stated_income=95000.0,
            occupation="Senior Engineer",
            kyc_level="enhanced",
            account_opened_at=_dt(730),
            products_held=["chequing", "tfsa", "rrsp"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="Isabel Torres",
            date_of_birth="1990-09-28",
            stated_income=72000.0,
            occupation="Marketing Manager",
            kyc_level="standard",
            account_opened_at=_dt(200),
            products_held=["chequing"],
        ),
        dict(
            id=str(uuid.uuid4()),
            name="James Okafor",
            date_of_birth="1998-01-07",
            stated_income=28000.0,
            occupation="Part-time Barista",
            kyc_level="standard",
            account_opened_at=_dt(45),
            products_held=["chequing", "crypto"],
        ),
    ]

    clients = {}
    for data in clients_data:
        client = Client(**data)
        db.add(client)
        key = data["name"].split()[0].lower()
        clients[key] = client

    db.flush()
    return clients


# ── Transactions ──────────────────────────────────────────────────────────────

def _create_transactions(db: Session, clients: dict) -> None:

    # ── 1. Alice Chen — Clean payroll depositor (expected: L0) ───────────────
    # Regular bi-weekly payroll from employer, TFSA contributions, normal spending
    # 30d inflow: ~$4,800  vs monthly income $6,000 → ratio 0.8 → income_inconsistency: none
    # No structuring, no new CPs, no crypto → overall score < 0.20
    alice = clients["alice"].id
    for weeks_ago in [0.5, 2.5, 4.5, 6.5, 8.5, 10.5, 12.5]:
        db.add(_txn(alice, "deposit", "chequing", 2400.0, _dt(weeks_ago * 7, 9),
                    source="Maple Leaf Technologies", counterparty_name="Maple Leaf Technologies"))
    # TFSA contributions (quarterly)
    db.add(_txn(alice, "deposit", "tfsa", 500.0, _dt(45, 11), counterparty_name="Self Transfer"))
    db.add(_txn(alice, "deposit", "tfsa", 500.0, _dt(10, 11), counterparty_name="Self Transfer"))
    # Normal bill payments
    for i, (name, amt) in enumerate([("Rogers Wireless", 95.0), ("BC Hydro", 140.0),
                                      ("Shoppers Drug Mart", 62.0), ("Loblaw", 180.0)]):
        db.add(_txn(alice, "withdrawal", "chequing", amt, _dt(i * 7 + 2, 14),
                    destination=name, counterparty_name=name))
    # Rent
    db.add(_txn(alice, "e_transfer_out", "chequing", 1650.0, _dt(3, 8),
                destination="Pacific Properties Ltd", counterparty_name="Pacific Properties Ltd"))

    # ── 2. Bob Kamara — Structuring (expected: L3, score ~0.90) ──────────────
    # 3 deposits in [$8,000-$9,999] within 7 days → structuring_conf = 0.90
    # + crypto buy (for crypto product in products_held)
    # Stated income $56K → monthly $4,667; 30d inflow ~$29K → income_conf ~0.88
    # Overall = max(struct=0.90, income=0.88) = 0.90 → L3
    bob = clients["bob"].id
    # Background normal deposits (older)
    for weeks_ago in [10, 8, 6]:
        db.add(_txn(bob, "deposit", "chequing", 2200.0, _dt(weeks_ago * 7, 9),
                    source="Retail Corp Payroll", counterparty_name="Retail Corp Payroll"))
    # STRUCTURING: 3 near-$10K deposits within 7 days (days 1, 3, 6)
    db.add(_txn(bob, "e_transfer_in", "chequing", 9200.0, _dt(6, 14, 30),
                source="Unknown sender A", counterparty_name="Marcus T."))
    db.add(_txn(bob, "e_transfer_in", "chequing", 9500.0, _dt(3, 11, 15),
                source="Unknown sender B", counterparty_name="Jordan R."))
    db.add(_txn(bob, "e_transfer_in", "chequing", 9400.0, _dt(1, 16, 0),
                source="Unknown sender C", counterparty_name="Tyler M."))
    # Crypto buy (after structuring deposits)
    db.add(_txn(bob, "crypto_buy", "crypto", 8000.0, _dt(0, 10, 30),
                destination="Coinbase", counterparty_name="Coinbase",
                metadata={"asset": "BTC"}))
    # Some normal spending
    db.add(_txn(bob, "withdrawal", "chequing", 350.0, _dt(12, 13),
                destination="FoodCo", counterparty_name="FoodCo"))

    # ── 3. Carl Mendez — Crypto layering (expected: L3, score ~0.92) ─────────
    # Large deposit then crypto_send to external wallet within 4 hours
    # rapid_crypto_conversion = 0.92 → crypto risk = 0.92 → L3
    # Stated income $62K → monthly $5,167; 30d inflow $18K → income_conf = 0.76
    # Overall = max(income=0.76, crypto_conv=0.92) = 0.92 → L3
    carl = clients["carl"].id
    # Background transactions (older, normal-looking)
    db.add(_txn(carl, "deposit", "chequing", 3200.0, _dt(45, 9),
                source="Consulting Client A", counterparty_name="Nexus Solutions Inc"))
    db.add(_txn(carl, "deposit", "chequing", 2800.0, _dt(35, 9),
                source="Consulting Client B", counterparty_name="Apex Digital Inc"))
    db.add(_txn(carl, "withdrawal", "chequing", 1800.0, _dt(30, 14),
                destination="Rent", counterparty_name="Metro Properties"))
    # THE SUSPICIOUS DAY: large deposit then rapid crypto conversion (within 4 hours)
    # _dt(2, 9) = 2 days ago at 9am = deposit
    # _dt(2, 12) = 2 days ago at 12pm = crypto_send (3 hours later → rapid_crypto_conversion triggers)
    db.add(_txn(carl, "deposit", "chequing", 18000.0, _dt(2, 9, 0),
                source="Wire Transfer", counterparty_name="Offshore Holdings Ltd",
                metadata={"flagged": True, "wire_ref": "WIRE-2024-0891"}))
    db.add(_txn(carl, "crypto_buy", "crypto", 16500.0, _dt(2, 10, 30),
                destination="Binance", counterparty_name="Binance",
                metadata={"asset": "BTC"}))
    db.add(_txn(carl, "crypto_send", "crypto", 16200.0, _dt(2, 12, 0),
                destination="0x9f2c4a8e1b7d3f6c5a0e9d2b4f7a1c3e8b5d",
                counterparty_name="External Wallet",
                metadata={"asset": "BTC", "external_wallet": "0x9f2c4a8e1b7d3f6c5a0e9d2b4f7a1c3e8b5d"}))

    # ── 4. Dana Osei — Coordinated group leader (expected: L3, score ~0.85) ──
    # 4 new counterparties sending money within 7 days → new_counterparty_burst = 0.85
    # + crypto sends to 0x7a3f... wallet cluster for cross-client detection
    # Stated income $42K → monthly $3,500; 30d inflow ~$14K → income_conf = 0.75
    # Overall = max(cp_burst=0.85, income=0.75) = 0.85 → L3
    dana = clients["dana"].id
    # Background (older)
    db.add(_txn(dana, "deposit", "chequing", 2100.0, _dt(40, 9),
                source="Payroll", counterparty_name="City Sales Corp"))
    db.add(_txn(dana, "deposit", "chequing", 2100.0, _dt(26, 9),
                source="Payroll", counterparty_name="City Sales Corp"))
    db.add(_txn(dana, "withdrawal", "chequing", 1400.0, _dt(20, 11),
                destination="Rent", counterparty_name="Urban Properties Inc"))
    # COORDINATED PATTERN: 4 new senders within 7 days (all new counterparties)
    db.add(_txn(dana, "e_transfer_in", "chequing", 3200.0, _dt(6, 13),
                source="New sender 1", counterparty_name="Kevin B."))
    db.add(_txn(dana, "e_transfer_in", "chequing", 2800.0, _dt(5, 10),
                source="New sender 2", counterparty_name="Priya S."))
    db.add(_txn(dana, "e_transfer_in", "chequing", 4100.0, _dt(3, 15),
                source="New sender 3", counterparty_name="Liam W."))
    db.add(_txn(dana, "e_transfer_in", "chequing", 3500.0, _dt(2, 11),
                source="New sender 4", counterparty_name="Zara N."))
    # Crypto sends to shared wallet cluster (0x7a3f prefix — for cross-client correlation)
    db.add(_txn(dana, "crypto_send", "crypto", 11200.0, _dt(1, 16),
                destination="0x7a3f8b2c1d9e4f5a6b7c8d9e0f1a2b3c4d5e6f",
                counterparty_name="Crypto Consolidation Wallet",
                metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c..."}))

    # ── 5. Eve Johansson — Coordinated participant (expected: L3, score ~0.85) ─
    # 3 new counterparties within 7 days → cp_burst = 0.85 → L3
    # + crypto sends to same 0x7a3f... cluster as Dana and Frank
    eve = clients["eve"].id
    # Background
    db.add(_txn(eve, "deposit", "chequing", 1850.0, _dt(42, 9),
                source="Payroll", counterparty_name="Service Plus Ltd"))
    db.add(_txn(eve, "deposit", "chequing", 1850.0, _dt(28, 9),
                source="Payroll", counterparty_name="Service Plus Ltd"))
    db.add(_txn(eve, "withdrawal", "chequing", 1200.0, _dt(22, 11),
                destination="Rent", counterparty_name="Affordable Homes Corp"))
    # COORDINATED PATTERN: 3 new senders within 7 days
    db.add(_txn(eve, "e_transfer_in", "chequing", 2400.0, _dt(6, 14),
                source="New sender A", counterparty_name="Ryan C."))
    db.add(_txn(eve, "e_transfer_in", "chequing", 1900.0, _dt(4, 11),
                source="New sender B", counterparty_name="Sofia M."))
    db.add(_txn(eve, "e_transfer_in", "chequing", 2700.0, _dt(2, 9),
                source="New sender C", counterparty_name="Jaden T."))
    # Crypto send to SAME wallet cluster as Dana
    db.add(_txn(eve, "crypto_send", "crypto", 6400.0, _dt(1, 14),
                destination="0x7a3f8b2c1d9e4f5a6b7c8d9e0f1a2b3c4d5e6f",
                counterparty_name="Crypto Consolidation Wallet",
                metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c..."}))

    # ── 6. Frank Lim — Coordinated minor participant (expected: L2, score ~0.60) ─
    # Only 2 new counterparties within 7 days → cp_burst = 0.60 → L2 (below L3 threshold)
    # + crypto send to same 0x7a3f... cluster (appears in Dana/Eve's investigation)
    frank = clients["frank"].id
    # Background
    db.add(_txn(frank, "deposit", "chequing", 2050.0, _dt(45, 9),
                source="Payroll", counterparty_name="Logistics Partners Inc"))
    db.add(_txn(frank, "deposit", "chequing", 2050.0, _dt(31, 9),
                source="Payroll", counterparty_name="Logistics Partners Inc"))
    db.add(_txn(frank, "withdrawal", "chequing", 1500.0, _dt(25, 11),
                destination="Rent", counterparty_name="Eastside Rentals"))
    # MINOR COORDINATED PATTERN: only 2 new senders within 7 days → L2 not L3
    db.add(_txn(frank, "e_transfer_in", "chequing", 1800.0, _dt(5, 13),
                source="New sender X", counterparty_name="Malik A."))
    db.add(_txn(frank, "e_transfer_in", "chequing", 1400.0, _dt(3, 10),
                source="New sender Y", counterparty_name="Chloe D."))
    # Crypto send to same wallet cluster
    db.add(_txn(frank, "crypto_send", "crypto", 2800.0, _dt(2, 15),
                destination="0x7a3f8b2c1d9e4f5a6b7c8d9e0f1a2b3c4d5e6f",
                counterparty_name="Crypto Consolidation Wallet",
                metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c..."}))

    # ── 7. Grace Okonkwo — Income inconsistency (expected: L3, score ~0.83) ──
    # Stated income $38K → monthly $3,167
    # 30d inflow: $15,000 → ratio = 4.73 → income_conf = 0.83 → L3
    grace = clients["grace"].id
    # Background (older)
    db.add(_txn(grace, "deposit", "chequing", 1800.0, _dt(65, 9),
                source="Payroll", counterparty_name="Admin Services Corp"))
    db.add(_txn(grace, "deposit", "chequing", 1800.0, _dt(50, 9),
                source="Payroll", counterparty_name="Admin Services Corp"))
    db.add(_txn(grace, "withdrawal", "chequing", 1100.0, _dt(45, 11),
                destination="Rent", counterparty_name="River View Apartments"))
    # INCOME INCONSISTENCY: large deposits in last 30 days
    # Total 30d inflow = $5,500 + $4,200 + $5,300 = $15,000 → ratio = 4.73
    db.add(_txn(grace, "e_transfer_in", "chequing", 5500.0, _dt(25, 14),
                source="Unknown A", counterparty_name="Coastal Import LLC",
                metadata={"flagged": True}))
    db.add(_txn(grace, "e_transfer_in", "chequing", 4200.0, _dt(15, 11),
                source="Unknown B", counterparty_name="Pacific Trade Group",
                metadata={"flagged": True}))
    db.add(_txn(grace, "e_transfer_in", "chequing", 5300.0, _dt(5, 16),
                source="Unknown C", counterparty_name="Northern Goods Inc",
                metadata={"flagged": True}))
    # Normal spending
    db.add(_txn(grace, "withdrawal", "chequing", 900.0, _dt(8, 13),
                destination="Groceries", counterparty_name="Loblaws"))

    # ── 8. Henry Park — Salary bonus auto-resolve (expected: L0, score ~0.35) ─
    # Stated income $95K → monthly $7,917
    # 1 deposit of $8,500 from known employer
    # - In structuring band [$8K-$10K] BUT only 1 deposit → struct_conf = 0.35 (below threshold)
    # - 30d inflow $8,500 → ratio = 1.07 → below 1.5x threshold → income_conf = 0.0
    # - Not a new counterparty (employer name in counterparty list from older txns)
    # → overall score = 0.35 → L0 (auto-resolved, no action required)
    henry = clients["henry"].id
    # Regular history with Northern Dynamics Corp (employer is KNOWN)
    for weeks_ago in [20, 16, 12, 8, 4]:
        db.add(_txn(henry, "deposit", "chequing", 3958.0, _dt(weeks_ago * 7, 9),
                    source="Northern Dynamics Corp", counterparty_name="Northern Dynamics Corp"))
    # TFSA / RRSP regular contributions
    db.add(_txn(henry, "deposit", "tfsa", 1000.0, _dt(60, 11),
                counterparty_name="Self Transfer"))
    db.add(_txn(henry, "deposit", "rrsp", 2500.0, _dt(30, 11),
                counterparty_name="Self Transfer"))
    # THE FLAGGED DEPOSIT: large one-time bonus from known employer
    # Same employer as regular payroll → counterparty IS known → cp_burst = 0
    # $8,500 in structuring band but only 1 occurrence → struct_conf = 0.35
    db.add(_txn(henry, "deposit", "chequing", 8500.0, _dt(4, 10),
                source="Northern Dynamics Corp", counterparty_name="Northern Dynamics Corp",
                metadata={"memo": "Q4 performance bonus"}))
    # Normal spending
    db.add(_txn(henry, "withdrawal", "chequing", 2800.0, _dt(2, 14),
                destination="Mortgage", counterparty_name="TD Mortgage Services"))
    db.add(_txn(henry, "withdrawal", "chequing", 450.0, _dt(1, 11),
                destination="Grocery", counterparty_name="Whole Foods"))

    # ── 9. Isabel Torres — Minor structuring (expected: L2, score ~0.70) ──────
    # 2 deposits in [$8K-$10K] within 7 days → struct_conf = 0.70 → L2
    # Stated income $72K → monthly $6,000; 30d inflow ~$18K → income_conf = 0.74
    # Overall = max(struct=0.70, income=0.74) = 0.74 → L2 (just under L3 threshold of 0.75)
    isabel = clients["isabel"].id
    # Background
    for weeks_ago in [10, 8, 6]:
        db.add(_txn(isabel, "deposit", "chequing", 3200.0, _dt(weeks_ago * 7, 9),
                    source="Payroll", counterparty_name="BrightMark Agency"))
    db.add(_txn(isabel, "withdrawal", "chequing", 2100.0, _dt(30, 11),
                destination="Rent", counterparty_name="Downtown Suites"))
    # MINOR STRUCTURING: 2 deposits in [$8K-$10K] within 7 days
    db.add(_txn(isabel, "e_transfer_in", "chequing", 8500.0, _dt(5, 14),
                source="Client payment A", counterparty_name="Spark Ventures Ltd"))
    db.add(_txn(isabel, "e_transfer_in", "chequing", 8200.0, _dt(3, 11),
                source="Client payment B", counterparty_name="Spark Ventures Ltd"))
    # A recent third deposit (but NOT in structuring band — below $8K)
    db.add(_txn(isabel, "e_transfer_in", "chequing", 1400.0, _dt(1, 9),
                source="Client payment C", counterparty_name="Creative Co"))

    # ── 10. James Okafor — Mule account (expected: L3, score ~0.92) ──────────
    # 8 new counterparties sending small amounts within 7 days → cp_burst = 0.85
    # + 1 crypto_send to external wallet within 4h of a deposit → crypto_conv = 0.92
    # Stated income $28K → monthly $2,333; 30d inflow $4,700 → income_conf = 0.67
    # chequing = max(cp=0.85, income=0.67) = 0.85; crypto = max(crypto_conv=0.92) = 0.92
    # Overall = max(0.85, 0.92) = 0.92 → L3
    james = clients["james"].id
    # Background (minimal — new account)
    db.add(_txn(james, "deposit", "chequing", 1500.0, _dt(40, 9),
                source="Payroll", counterparty_name="Metro Coffee Chain"))
    db.add(_txn(james, "deposit", "chequing", 1500.0, _dt(26, 9),
                source="Payroll", counterparty_name="Metro Coffee Chain"))
    # MULE PATTERN: 8 new senders within 7 days (all new counterparties)
    senders = [
        ("Alex H.", 480.0, 6), ("Maria K.", 650.0, 6), ("Tom B.", 520.0, 5),
        ("Yuki S.", 780.0, 5), ("Amir P.", 440.0, 4), ("Leila C.", 590.0, 4),
        ("Owen D.", 720.0, 3), ("Nina R.", 520.0, 3),
    ]
    for name, amt, days_ago in senders:
        db.add(_txn(james, "e_transfer_in", "chequing", amt, _dt(days_ago, 12),
                    source=f"Interac from {name}", counterparty_name=name))

    # RAPID CRYPTO CONVERSION: deposit at 2pm, crypto_send at 5pm (3 hours later)
    # The e_transfer_in from Owen D. at day 3 is the deposit that triggers it
    # (type="e_transfer_in" matches _detect_rapid_crypto_conversion's deposits list)
    db.add(_txn(james, "crypto_send", "crypto", 4200.0, _dt(3, 15),
                destination="0xf4e2a1b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4",
                counterparty_name="Anonymous Wallet",
                metadata={"asset": "USDT", "external_wallet": "0xf4e2a1b8c7d6e5..."}))

    db.flush()


# ── Main seed function ────────────────────────────────────────────────────────

def seed_all(db: Session) -> None:
    print("Dropping and recreating all tables (schema refresh)...")
    from app.models.base import Base
    import app.models  # noqa: F401
    from app.core.database import engine
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("Creating clients...")
    clients = _create_clients(db)

    print("Creating transactions...")
    _create_transactions(db, clients)

    db.commit()
    print(f"\nSeed complete — {len(clients)} clients with transactions seeded.")
    print("Profiles, restrictions, and investigations will be created when")
    print("the analyst clicks 'Run Simulation' on the dashboard.\n")
    for name, client in clients.items():
        print(f"  {client.name:20} | income ${client.stated_income:,.0f}/yr | {len(client.products_held)} products")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()
