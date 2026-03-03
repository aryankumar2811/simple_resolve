"""
Seed script -- populates the database with clients and transactions for all demo scenarios.
Profiles, restrictions, and investigations are NOT pre-seeded -- they are created when
the analyst clicks "Run Simulation" on the dashboard.

Run with:
    cd backend && python -m app.seed.seed_data

20 Clients, 20-30 transactions each:

  L0 Auto-Resolve (4):
    1  Alice Chen      : Clean payroll depositor
    2  Henry Park      : Salary spike from known employer
    3  Natasha Volkov  : Freelancer with irregular but legit income
    4  Raj Patel       : Small business owner, seasonal fluctuation

  L2 Guardrail (5):
    5  Isabel Torres   : Minor structuring (2x near-$10K)
    6  Frank Lim       : Coordinated minor participant (0x7a3f cluster)
    7  Priya Sharma    : Moderate income inconsistency (family trust)
    8  Marcus Webb     : Early mule signals + 0x8b4f cluster link
    9  Sophie Laurent  : Crypto volatility (legit trader)

  L3 Investigation (9):
   10  Bob Kamara      : Structuring + crypto exit
   11  Carl Mendez     : Crypto layering (fiat->BTC->external in 3hrs)
   12  Dana Osei       : Coordinated group leader (0x7a3f cluster)
   13  Eve Johansson   : Coordinated participant (0x7a3f cluster)
   14  Grace Okonkwo   : Severe income inconsistency (shell companies)
   15  James Okafor    : Mule account (8 new senders -> crypto)
   16  Wei Zhang       : Round-tripping (wire out -> wire in, diff entity)
   17  Amara Diallo    : Multi-hop layering (fiat->BTC->ETH->external)

  Near-L4 / Extreme (2):
   18  Viktor Petrov   : Extreme wire deposits + multi-wallet crypto exit
   19  Chen Wei Li     : Account takeover pattern (5yr baseline shattered)

  Second Coordinated Cluster:
   20  Yuki Tanaka     : 0x8b4f cluster (links to Marcus Webb)

  Coordinated clusters:
    Cluster 1 (0x7a3f): Dana + Eve + Frank
    Cluster 2 (0x8b4f): Yuki + Marcus
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import Client, Transaction

# -- Helpers -------------------------------------------------------------------

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


# -- Clients -------------------------------------------------------------------

def _create_clients(db: Session) -> dict[str, Client]:
    clients_data = [
        # L0 Auto-Resolve
        dict(id=str(uuid.uuid4()), name="Alice Chen", date_of_birth="1988-04-12",
             stated_income=72000.0, occupation="Software Developer",
             kyc_level="enhanced", account_opened_at=_dt(480),
             products_held=["chequing", "tfsa"]),
        dict(id=str(uuid.uuid4()), name="Henry Park", date_of_birth="1982-06-15",
             stated_income=95000.0, occupation="Senior Engineer",
             kyc_level="enhanced", account_opened_at=_dt(730),
             products_held=["chequing", "tfsa", "rrsp"]),
        dict(id=str(uuid.uuid4()), name="Natasha Volkov", date_of_birth="1990-03-22",
             stated_income=85000.0, occupation="UX Designer (Freelance)",
             kyc_level="enhanced", account_opened_at=_dt(420),
             products_held=["chequing", "tfsa"]),
        dict(id=str(uuid.uuid4()), name="Raj Patel", date_of_birth="1979-11-08",
             stated_income=110000.0, occupation="Restaurant Owner",
             kyc_level="enhanced", account_opened_at=_dt(900),
             products_held=["chequing", "visa"]),

        # L2 Guardrail
        dict(id=str(uuid.uuid4()), name="Isabel Torres", date_of_birth="1990-09-28",
             stated_income=72000.0, occupation="Marketing Manager",
             kyc_level="standard", account_opened_at=_dt(200),
             products_held=["chequing"]),
        dict(id=str(uuid.uuid4()), name="Frank Lim", date_of_birth="1989-03-14",
             stated_income=41000.0, occupation="Warehouse Supervisor",
             kyc_level="standard", account_opened_at=_dt(62),
             products_held=["chequing", "crypto"]),
        dict(id=str(uuid.uuid4()), name="Priya Sharma", date_of_birth="1992-07-19",
             stated_income=35000.0, occupation="Administrative Clerk",
             kyc_level="standard", account_opened_at=_dt(740),
             products_held=["chequing"]),
        dict(id=str(uuid.uuid4()), name="Marcus Webb", date_of_birth="1996-12-03",
             stated_income=26000.0, occupation="Part-time Security Guard",
             kyc_level="standard", account_opened_at=_dt(55),
             products_held=["chequing", "crypto"]),
        dict(id=str(uuid.uuid4()), name="Sophie Laurent", date_of_birth="1994-05-11",
             stated_income=68000.0, occupation="Financial Analyst",
             kyc_level="standard", account_opened_at=_dt(240),
             products_held=["chequing", "crypto"]),

        # L3 Investigation
        dict(id=str(uuid.uuid4()), name="Bob Kamara", date_of_birth="1993-09-22",
             stated_income=56000.0, occupation="Retail Manager",
             kyc_level="standard", account_opened_at=_dt(310),
             products_held=["chequing", "crypto"]),
        dict(id=str(uuid.uuid4()), name="Carl Mendez", date_of_birth="1997-02-05",
             stated_income=62000.0, occupation="Freelance Consultant",
             kyc_level="standard", account_opened_at=_dt(95),
             products_held=["chequing", "crypto"]),
        dict(id=str(uuid.uuid4()), name="Dana Osei", date_of_birth="1991-11-30",
             stated_income=42000.0, occupation="Sales Representative",
             kyc_level="standard", account_opened_at=_dt(80),
             products_held=["chequing", "crypto"]),
        dict(id=str(uuid.uuid4()), name="Eve Johansson", date_of_birth="1995-07-18",
             stated_income=38000.0, occupation="Customer Service Agent",
             kyc_level="standard", account_opened_at=_dt(70),
             products_held=["chequing", "crypto"]),
        dict(id=str(uuid.uuid4()), name="Grace Okonkwo", date_of_birth="1985-12-01",
             stated_income=38000.0, occupation="Administrative Assistant",
             kyc_level="standard", account_opened_at=_dt(160),
             products_held=["chequing"]),
        dict(id=str(uuid.uuid4()), name="James Okafor", date_of_birth="1998-01-07",
             stated_income=28000.0, occupation="Part-time Barista",
             kyc_level="standard", account_opened_at=_dt(45),
             products_held=["chequing", "crypto"]),
        dict(id=str(uuid.uuid4()), name="Wei Zhang", date_of_birth="1983-08-25",
             stated_income=75000.0, occupation="Import/Export Consultant",
             kyc_level="standard", account_opened_at=_dt(365),
             products_held=["chequing", "crypto"]),
        dict(id=str(uuid.uuid4()), name="Amara Diallo", date_of_birth="2001-04-17",
             stated_income=18000.0, occupation="University Student (Part-time)",
             kyc_level="basic", account_opened_at=_dt(90),
             products_held=["chequing", "crypto"]),

        # Near-L4 / Extreme
        dict(id=str(uuid.uuid4()), name="Viktor Petrov", date_of_birth="1986-10-14",
             stated_income=45000.0, occupation="Import/Export Trader",
             kyc_level="standard", account_opened_at=_dt(120),
             products_held=["chequing", "crypto"]),
        dict(id=str(uuid.uuid4()), name="Chen Wei Li", date_of_birth="1958-02-20",
             stated_income=52000.0, occupation="Retired Teacher (Pension)",
             kyc_level="enhanced", account_opened_at=_dt(1825),
             products_held=["chequing", "tfsa"]),

        # Second Coordinated Cluster
        dict(id=str(uuid.uuid4()), name="Yuki Tanaka", date_of_birth="1993-06-09",
             stated_income=40000.0, occupation="Freelance Photographer",
             kyc_level="standard", account_opened_at=_dt(150),
             products_held=["chequing", "crypto"]),
    ]

    clients = {}
    for data in clients_data:
        client = Client(**data)
        db.add(client)
        # Build lookup key from name
        key = data["name"].split()[0].lower()
        # Handle duplicate first names
        if key in clients:
            key = data["name"].replace(" ", "_").lower()
        clients[key] = client

    db.flush()
    return clients


# -- Transactions ---------------------------------------------------------------

def _create_transactions(db: Session, clients: dict) -> None:
    txns = []

    def add(t):
        txns.append(t)

    # ==========================================================================
    # 1. ALICE CHEN - Clean payroll depositor (expected: L0)
    # ==========================================================================
    # Regular bi-weekly payroll, TFSA, rent, bills. All CPs are known/established.
    # 30d inflow ~$4,800 vs monthly income $6,000 -> ratio 0.8 -> no indicators.
    alice = clients["alice"].id
    # Bi-weekly payroll (7 deposits over ~14 weeks)
    for i, w in enumerate([0.5, 2.5, 4.5, 6.5, 8.5, 10.5, 12.5]):
        add(_txn(alice, "deposit", "chequing", 2400.0, _dt(w * 7, 9, 0),
                 source="Maple Leaf Technologies", counterparty_name="Maple Leaf Technologies"))
    # TFSA contributions (3 quarterly)
    for d in [75, 45, 10]:
        add(_txn(alice, "deposit", "tfsa", 500.0, _dt(d, 11), counterparty_name="Self Transfer"))
    # Rent (3 months)
    for d in [60, 30, 3]:
        add(_txn(alice, "e_transfer_out", "chequing", 1650.0, _dt(d, 8),
                 destination="Pacific Properties Ltd", counterparty_name="Pacific Properties Ltd"))
    # Bills (6 different recurring)
    bills = [("Rogers Wireless", 95.0), ("BC Hydro", 140.0), ("Shoppers Drug Mart", 62.0),
             ("Loblaw", 180.0), ("Netflix", 22.99), ("GoodLife Fitness", 55.0)]
    for i, (name, amt) in enumerate(bills):
        add(_txn(alice, "withdrawal", "chequing", amt, _dt(i * 7 + 2, 14),
                 destination=name, counterparty_name=name))
    # One-time furniture purchase
    add(_txn(alice, "withdrawal", "chequing", 1200.0, _dt(20, 15),
             destination="IKEA", counterparty_name="IKEA"))
    # Gas station
    add(_txn(alice, "withdrawal", "chequing", 65.0, _dt(5, 17),
             destination="Petro-Canada", counterparty_name="Petro-Canada"))
    # Self transfer savings
    add(_txn(alice, "e_transfer_out", "chequing", 300.0, _dt(8, 10),
             destination="Self - Savings", counterparty_name="Self Transfer"))
    # Coffee shop
    add(_txn(alice, "withdrawal", "chequing", 12.50, _dt(1, 8, 30),
             destination="Tim Hortons", counterparty_name="Tim Hortons"))
    # Total: 25 txns

    # ==========================================================================
    # 2. HENRY PARK - Salary spike auto-resolve (expected: L0)
    # ==========================================================================
    # Long account history, known employer. One-time bonus $8,500 is from SAME employer.
    # struct_conf = 0.35 (only 1 in band), income ratio = 1.07 -> auto-resolve.
    henry = clients["henry"].id
    # Regular payroll (8 bi-weekly)
    for w in [1, 3, 5, 7, 9, 11, 13, 15]:
        add(_txn(henry, "deposit", "chequing", 3958.0, _dt(w * 7, 9),
                 source="Northern Dynamics Corp", counterparty_name="Northern Dynamics Corp"))
    # RRSP contributions (2)
    add(_txn(henry, "deposit", "rrsp", 2500.0, _dt(60, 11), counterparty_name="Self Transfer"))
    add(_txn(henry, "deposit", "rrsp", 2500.0, _dt(30, 11), counterparty_name="Self Transfer"))
    # TFSA (2)
    add(_txn(henry, "deposit", "tfsa", 1000.0, _dt(75, 11), counterparty_name="Self Transfer"))
    add(_txn(henry, "deposit", "tfsa", 1000.0, _dt(15, 11), counterparty_name="Self Transfer"))
    # Mortgage (3 months)
    for d in [60, 30, 2]:
        add(_txn(henry, "withdrawal", "chequing", 2800.0, _dt(d, 14),
                 destination="TD Mortgage Services", counterparty_name="TD Mortgage Services"))
    # Groceries (4)
    for i, (name, amt) in enumerate([("Costco", 320.0), ("Whole Foods", 185.0),
                                       ("No Frills", 95.0), ("Loblaws", 210.0)]):
        add(_txn(henry, "withdrawal", "chequing", amt, _dt(i * 8 + 3, 11),
                 destination=name, counterparty_name=name))
    # THE FLAGGED DEPOSIT: $8,500 bonus from KNOWN employer -> auto-resolve
    add(_txn(henry, "deposit", "chequing", 8500.0, _dt(4, 10),
             source="Northern Dynamics Corp", counterparty_name="Northern Dynamics Corp",
             metadata={"memo": "Q4 performance bonus"}))
    # Car insurance
    add(_txn(henry, "withdrawal", "chequing", 225.0, _dt(20, 9),
             destination="Intact Insurance", counterparty_name="Intact Insurance"))
    # Utility
    add(_txn(henry, "withdrawal", "chequing", 165.0, _dt(12, 14),
             destination="Enbridge Gas", counterparty_name="Enbridge Gas"))
    # Total: 24 txns

    # ==========================================================================
    # 3. NATASHA VOLKOV - Freelancer, irregular but legit (expected: L0)
    # ==========================================================================
    # Irregular consulting payments from 3 known long-term clients. All established CPs.
    # Income matches stated range. 400+ day account history.
    natasha = clients["natasha"].id
    # Consulting payments from 3 known clients (7 total, irregular timing)
    consulting_clients = [
        ("Bright Ideas Studio", [80, 55, 25]),
        ("Digital Wave Agency", [70, 40, 12]),
        ("Northstar UX Corp", [60]),
    ]
    for name, days in consulting_clients:
        for d in days:
            amt = 2500.0 + (hash(f"{name}{d}") % 2500)  # $2,500-$5,000 range
            add(_txn(natasha, "e_transfer_in", "chequing", round(amt, 2), _dt(d, 10),
                     source=name, counterparty_name=name))
    # Rent (3 months)
    for d in [60, 30, 3]:
        add(_txn(natasha, "e_transfer_out", "chequing", 1800.0, _dt(d, 8),
                 destination="Maple Ridge Properties", counterparty_name="Maple Ridge Properties"))
    # Utilities
    add(_txn(natasha, "withdrawal", "chequing", 120.0, _dt(25, 14),
             destination="FortisBC", counterparty_name="FortisBC"))
    add(_txn(natasha, "withdrawal", "chequing", 85.0, _dt(18, 14),
             destination="Telus", counterparty_name="Telus"))
    # Adobe subscription
    add(_txn(natasha, "withdrawal", "chequing", 79.99, _dt(10, 9),
             destination="Adobe Inc", counterparty_name="Adobe Inc"))
    # Conference registration
    add(_txn(natasha, "withdrawal", "chequing", 1200.0, _dt(35, 16),
             destination="UX Canada Conference", counterparty_name="UX Canada Conference"))
    # Amazon purchases (3)
    for d in [45, 22, 8]:
        add(_txn(natasha, "withdrawal", "chequing", 85.0 + (d % 50), _dt(d, 13),
                 destination="Amazon.ca", counterparty_name="Amazon.ca"))
    # TFSA (2)
    add(_txn(natasha, "deposit", "tfsa", 750.0, _dt(50, 11), counterparty_name="Self Transfer"))
    add(_txn(natasha, "deposit", "tfsa", 750.0, _dt(15, 11), counterparty_name="Self Transfer"))
    # Total: 22 txns

    # ==========================================================================
    # 4. RAJ PATEL - Small business owner, seasonal (expected: L0)
    # ==========================================================================
    # Daily Square deposits vary $400-$2,500. Known supplier payments, CRA tax.
    # High income stated ($110K), 2.5yr account. Seasonal Dec spike is normal for restaurants.
    raj = clients["raj"].id
    # Square payment deposits (10 over various days - daily restaurant revenue)
    square_days = [85, 72, 60, 50, 40, 30, 22, 14, 7, 2]
    for d in square_days:
        amt = 600.0 + (d * 17 % 1900)  # varies $600-$2,500
        add(_txn(raj, "deposit", "chequing", round(amt, 2), _dt(d, 18),
                 source="Square Payments", counterparty_name="Square Payments"))
    # Supplier payments (4 recurring)
    suppliers = [("Sysco Food Services", 2400.0, 45), ("GFS Canada", 1800.0, 35),
                 ("Sysco Food Services", 2600.0, 15), ("Coca-Cola Bottling", 850.0, 8)]
    for name, amt, d in suppliers:
        add(_txn(raj, "e_transfer_out", "chequing", amt, _dt(d, 10),
                 destination=name, counterparty_name=name))
    # Commercial rent
    for d in [60, 30, 1]:
        add(_txn(raj, "e_transfer_out", "chequing", 4200.0, _dt(d, 8),
                 destination="Dundas Commercial Properties", counterparty_name="Dundas Commercial Properties"))
    # CRA quarterly tax
    add(_txn(raj, "withdrawal", "chequing", 6500.0, _dt(20, 9),
             destination="CRA - GST/HST", counterparty_name="Canada Revenue Agency"))
    # Equipment lease
    add(_txn(raj, "withdrawal", "chequing", 450.0, _dt(25, 10),
             destination="Kitchen Equipment Leasing", counterparty_name="Kitchen Equipment Leasing"))
    # Personal draw
    add(_txn(raj, "e_transfer_out", "chequing", 3000.0, _dt(28, 15),
             destination="Self - Personal", counterparty_name="Raj Patel"))
    # Insurance
    add(_txn(raj, "withdrawal", "chequing", 380.0, _dt(42, 11),
             destination="Aviva Insurance", counterparty_name="Aviva Insurance"))
    # Staff payroll (Interac)
    add(_txn(raj, "e_transfer_out", "chequing", 1850.0, _dt(12, 16),
             destination="Staff - Maria R.", counterparty_name="Maria R."))
    add(_txn(raj, "e_transfer_out", "chequing", 1650.0, _dt(12, 16, 5),
             destination="Staff - Ahmed K.", counterparty_name="Ahmed K."))
    # Total: 26 txns

    # ==========================================================================
    # 5. ISABEL TORRES - Minor structuring (expected: L2, score ~0.70)
    # ==========================================================================
    # 2 deposits in $8K-$9K band within 7 days -> struct_conf=0.70 -> L2.
    # Income $72K/yr -> $6K/mo; 30d inflow ~$18K -> ratio 3.0 -> income_conf ~0.74.
    # Overall = max(0.70, 0.74) = 0.74 -> L2 (just under 0.75 threshold for L3).
    isabel = clients["isabel"].id
    # Regular payroll (6 bi-weekly)
    for w in [1, 3, 5, 7, 9, 11]:
        add(_txn(isabel, "deposit", "chequing", 3200.0, _dt(w * 7, 9),
                 source="BrightMark Agency", counterparty_name="BrightMark Agency"))
    # Rent (3)
    for d in [60, 30, 3]:
        add(_txn(isabel, "e_transfer_out", "chequing", 2100.0, _dt(d, 8),
                 destination="Downtown Suites", counterparty_name="Downtown Suites"))
    # Normal spending (6)
    spending = [("Shoppers Drug Mart", 45.0, 50), ("Loblaws", 165.0, 38),
                ("H&M", 120.0, 28), ("Uber Eats", 35.0, 18), ("Starbucks", 8.50, 10),
                ("LCBO", 52.0, 5)]
    for name, amt, d in spending:
        add(_txn(isabel, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    # MINOR STRUCTURING: 2 deposits in $8K-$10K band within 7 days
    add(_txn(isabel, "e_transfer_in", "chequing", 8500.0, _dt(5, 14),
             source="Client payment A", counterparty_name="Spark Ventures Ltd"))
    add(_txn(isabel, "e_transfer_in", "chequing", 8200.0, _dt(3, 11),
             source="Client payment B", counterparty_name="Spark Ventures Ltd"))
    # Third deposit below structuring band
    add(_txn(isabel, "e_transfer_in", "chequing", 7500.0, _dt(1, 9),
             source="Client payment C", counterparty_name="Creative Co"))
    # Gym membership
    add(_txn(isabel, "withdrawal", "chequing", 65.0, _dt(15, 10),
             destination="Equinox", counterparty_name="Equinox"))
    # Phone bill
    add(_txn(isabel, "withdrawal", "chequing", 95.0, _dt(12, 9),
             destination="Bell Canada", counterparty_name="Bell Canada"))
    # Insurance
    add(_txn(isabel, "withdrawal", "chequing", 180.0, _dt(22, 14),
             destination="TD Insurance", counterparty_name="TD Insurance"))
    # Total: 24 txns

    # ==========================================================================
    # 6. FRANK LIM - Coordinated minor participant (expected: L2, score ~0.60)
    # ==========================================================================
    # Only 2 new CPs within 7 days -> cp_burst=0.60 -> L2.
    # Crypto send to 0x7a3f cluster links him to Dana/Eve investigation.
    frank = clients["frank"].id
    # Payroll (6)
    for w in [1, 3, 5, 7, 9, 11]:
        add(_txn(frank, "deposit", "chequing", 2050.0, _dt(w * 7, 9),
                 source="Logistics Partners Inc", counterparty_name="Logistics Partners Inc"))
    # Rent (3)
    for d in [60, 30, 3]:
        add(_txn(frank, "e_transfer_out", "chequing", 1500.0, _dt(d, 8),
                 destination="Eastside Rentals", counterparty_name="Eastside Rentals"))
    # Groceries (4)
    for i, d in enumerate([55, 40, 25, 10]):
        add(_txn(frank, "withdrawal", "chequing", 120.0 + i * 15, _dt(d, 12),
                 destination="FreshCo", counterparty_name="FreshCo"))
    # Normal spending (3)
    add(_txn(frank, "withdrawal", "chequing", 45.0, _dt(35, 14),
             destination="Canadian Tire", counterparty_name="Canadian Tire"))
    add(_txn(frank, "withdrawal", "chequing", 22.0, _dt(20, 10),
             destination="Tim Hortons", counterparty_name="Tim Hortons"))
    add(_txn(frank, "withdrawal", "chequing", 85.0, _dt(8, 15),
             destination="Walmart", counterparty_name="Walmart"))
    # COORDINATED: 2 new senders (below L3 threshold of 3)
    add(_txn(frank, "e_transfer_in", "chequing", 1800.0, _dt(5, 13),
             source="New sender X", counterparty_name="Malik A."))
    add(_txn(frank, "e_transfer_in", "chequing", 1400.0, _dt(3, 10),
             source="New sender Y", counterparty_name="Chloe D."))
    # Crypto send to 0x7a3f cluster (links to Dana/Eve)
    add(_txn(frank, "crypto_send", "crypto", 2800.0, _dt(2, 15),
             destination="0x7a3f8b2c1d9e4f5a6b7c8d9e0f1a2b3c4d5e6f",
             counterparty_name="Crypto Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c..."}))
    # Total: 22 txns

    # ==========================================================================
    # 7. PRIYA SHARMA - Moderate income inconsistency (expected: L2)
    # ==========================================================================
    # Stated income $35K -> $2,917/mo. Family trust transfers total $8,500 in 30d.
    # Ratio = $8,500 / $2,917 = 2.91x -> income_conf ~0.72 -> L2.
    # 2yr account, known CPs. Trust payments are new but not alarming enough for L3.
    priya = clients["priya"].id
    # Payroll (6)
    for w in [1, 3, 5, 7, 9, 11]:
        add(_txn(priya, "deposit", "chequing", 1458.0, _dt(w * 7, 9),
                 source="City Services Corp", counterparty_name="City Services Corp"))
    # Rent (3)
    for d in [60, 30, 3]:
        add(_txn(priya, "e_transfer_out", "chequing", 1100.0, _dt(d, 8),
                 destination="Hillcrest Apartments", counterparty_name="Hillcrest Apartments"))
    # Normal spending (5)
    for name, amt, d in [("No Frills", 95.0, 50), ("Dollarama", 22.0, 35),
                          ("TTC Monthly Pass", 156.0, 28), ("Shoppers", 38.0, 15),
                          ("Winners", 75.0, 8)]:
        add(_txn(priya, "withdrawal", "chequing", amt, _dt(d, 13),
                 destination=name, counterparty_name=name))
    # INCOME INCONSISTENCY: 3 transfers from "Sharma Family Trust" in 30 days
    add(_txn(priya, "e_transfer_in", "chequing", 3500.0, _dt(25, 14),
             source="Sharma Family Trust", counterparty_name="Sharma Family Trust",
             metadata={"memo": "Family support"}))
    add(_txn(priya, "e_transfer_in", "chequing", 2500.0, _dt(15, 11),
             source="Sharma Family Trust", counterparty_name="Sharma Family Trust",
             metadata={"memo": "Family support"}))
    add(_txn(priya, "e_transfer_in", "chequing", 2500.0, _dt(5, 16),
             source="Sharma Family Trust", counterparty_name="Sharma Family Trust",
             metadata={"memo": "Family support"}))
    # Utilities
    add(_txn(priya, "withdrawal", "chequing", 65.0, _dt(20, 14),
             destination="Toronto Hydro", counterparty_name="Toronto Hydro"))
    # Phone
    add(_txn(priya, "withdrawal", "chequing", 50.0, _dt(12, 9),
             destination="Freedom Mobile", counterparty_name="Freedom Mobile"))
    # Groceries
    add(_txn(priya, "withdrawal", "chequing", 110.0, _dt(2, 11),
             destination="T&T Supermarket", counterparty_name="T&T Supermarket"))
    # Total: 23 txns

    # ==========================================================================
    # 8. MARCUS WEBB - Early mule signals (expected: L2, score ~0.60)
    # ==========================================================================
    # 2 new CPs in 7 days -> cp_burst=0.60 -> L2. Crypto send to 0x8b4f cluster
    # links to Yuki Tanaka. Trajectory is concerning but not yet L3.
    marcus = clients["marcus"].id
    # Payroll (4)
    for w in [2, 4, 6, 8]:
        add(_txn(marcus, "deposit", "chequing", 1083.0, _dt(w * 7, 9),
                 source="SecureGuard Services", counterparty_name="SecureGuard Services"))
    # Rent (3)
    for d in [45, 30, 3]:
        add(_txn(marcus, "e_transfer_out", "chequing", 800.0, _dt(d, 8),
                 destination="Parkview Rooms", counterparty_name="Parkview Rooms"))
    # Spending (4)
    for name, amt, d in [("McDonalds", 12.50, 40), ("Walmart", 65.0, 25),
                          ("Petro-Canada", 45.0, 15), ("Dollar Tree", 18.0, 5)]:
        add(_txn(marcus, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    # EARLY MULE SIGNALS: 2 new senders within 7 days
    add(_txn(marcus, "e_transfer_in", "chequing", 550.0, _dt(6, 11),
             source="Unknown sender 1", counterparty_name="Derek L."))
    add(_txn(marcus, "e_transfer_in", "chequing", 720.0, _dt(4, 14),
             source="Unknown sender 2", counterparty_name="Fatima H."))
    # Small crypto buy
    add(_txn(marcus, "crypto_buy", "crypto", 900.0, _dt(3, 16),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    # Crypto send to 0x8b4f cluster (links to Yuki Tanaka)
    add(_txn(marcus, "crypto_send", "crypto", 850.0, _dt(2, 10),
             destination="0x8b4f2a1c3d7e9f0b5a6c8d4e2f1a3b7c9d0e5f",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0x8b4f2a1c..."}))
    # Phone
    add(_txn(marcus, "withdrawal", "chequing", 45.0, _dt(10, 9),
             destination="Chatr Mobile", counterparty_name="Chatr Mobile"))
    # Transit
    add(_txn(marcus, "withdrawal", "chequing", 128.0, _dt(1, 8),
             destination="TTC Monthly Pass", counterparty_name="TTC"))
    # Total: 20 txns

    # ==========================================================================
    # 9. SOPHIE LAURENT - Crypto volatility, legit trader (expected: L2)
    # ==========================================================================
    # Active crypto trader with high volume. No external sends (all internal).
    # Crypto product score elevated from volume. One large $6K buy pushes score up.
    # Score ~0.62 -> L2 monitoring on crypto volume.
    sophie = clients["sophie"].id
    # Payroll (4)
    for w in [2, 4, 6, 8]:
        add(_txn(sophie, "deposit", "chequing", 2833.0, _dt(w * 7, 9),
                 source="RBC Capital Markets", counterparty_name="RBC Capital Markets"))
    # Crypto buy/sell pairs (8 trades - all internal, no external sends)
    crypto_trades = [
        ("crypto_buy", "BTC", 1500.0, 50), ("crypto_sell", "BTC", 1450.0, 48),
        ("crypto_buy", "ETH", 2000.0, 40), ("crypto_sell", "ETH", 2200.0, 38),
        ("crypto_buy", "BTC", 800.0, 30), ("crypto_sell", "BTC", 850.0, 25),
        ("crypto_buy", "ETH", 1200.0, 18), ("crypto_sell", "ETH", 1150.0, 12),
    ]
    for type_, asset, amt, d in crypto_trades:
        cp = "Wealthsimple Crypto"
        add(_txn(sophie, type_, "crypto", amt, _dt(d, 14),
                 destination=cp if "buy" in type_ else None,
                 source=cp if "sell" in type_ else None,
                 counterparty_name=cp,
                 metadata={"asset": asset}))
    # ONE LARGE crypto buy that pushes score up
    add(_txn(sophie, "crypto_buy", "crypto", 6000.0, _dt(5, 10),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    # Normal spending (5)
    for name, amt, d in [("Sephora", 85.0, 45), ("Indigo Books", 42.0, 32),
                          ("Metro", 155.0, 20), ("Uber", 28.0, 8), ("Starbucks", 7.50, 2)]:
        add(_txn(sophie, "withdrawal", "chequing", amt, _dt(d, 13),
                 destination=name, counterparty_name=name))
    # Rent
    add(_txn(sophie, "e_transfer_out", "chequing", 1900.0, _dt(3, 8),
             destination="Yorkville Apartments", counterparty_name="Yorkville Apartments"))
    # Phone
    add(_txn(sophie, "withdrawal", "chequing", 80.0, _dt(15, 9),
             destination="Rogers", counterparty_name="Rogers"))
    # Total: 25 txns

    # ==========================================================================
    # 10. BOB KAMARA - Structuring + crypto exit (expected: L3, score ~0.90)
    # ==========================================================================
    # 3 deposits in $8K-$10K band within 7 days -> struct_conf=0.90.
    # Followed by crypto buy + external send. Multiple overlapping flags.
    bob = clients["bob"].id
    # Regular payroll (6)
    for w in [2, 4, 6, 8, 10, 12]:
        add(_txn(bob, "deposit", "chequing", 2200.0, _dt(w * 7, 9),
                 source="Retail Corp Payroll", counterparty_name="Retail Corp Payroll"))
    # Normal spending (6)
    for name, amt, d in [("FoodCo", 350.0, 80), ("Best Buy", 220.0, 65),
                          ("Canadian Tire", 85.0, 50), ("Metro", 145.0, 35),
                          ("Pizza Pizza", 28.0, 20), ("Shoppers", 55.0, 10)]:
        add(_txn(bob, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    # Rent
    for d in [60, 30, 3]:
        add(_txn(bob, "e_transfer_out", "chequing", 1400.0, _dt(d, 8),
                 destination="King West Rentals", counterparty_name="King West Rentals"))
    # STRUCTURING: 3 near-$10K deposits within 7 days from unknowns
    add(_txn(bob, "e_transfer_in", "chequing", 9200.0, _dt(6, 14, 30),
             source="Unknown sender A", counterparty_name="Marcus T."))
    add(_txn(bob, "e_transfer_in", "chequing", 9500.0, _dt(3, 11, 15),
             source="Unknown sender B", counterparty_name="Jordan R."))
    add(_txn(bob, "e_transfer_in", "chequing", 9400.0, _dt(1, 16, 0),
             source="Unknown sender C", counterparty_name="Tyler M."))
    # Crypto buy then external send
    add(_txn(bob, "crypto_buy", "crypto", 8000.0, _dt(0.5, 10, 30),
             destination="Coinbase", counterparty_name="Coinbase",
             metadata={"asset": "BTC"}))
    add(_txn(bob, "crypto_send", "crypto", 7500.0, _dt(0.3, 14, 0),
             destination="0xd3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xd3e4f5a6..."}))
    # Additional small deposits to pad
    add(_txn(bob, "e_transfer_in", "chequing", 450.0, _dt(4, 9),
             source="Refund", counterparty_name="Amazon.ca"))
    add(_txn(bob, "deposit", "chequing", 200.0, _dt(2, 11),
             source="ATM Deposit", counterparty_name="ATM"))
    # Total: 28 txns

    # ==========================================================================
    # 11. CARL MENDEZ - Crypto layering (expected: L3, score ~0.92)
    # ==========================================================================
    # $18K deposit -> crypto buy 1.5hrs later -> crypto send 3hrs after deposit.
    # rapid_crypto_conversion=0.92. Classic fiat-to-crypto-to-external layering.
    carl = clients["carl"].id
    # Background consulting (5)
    for i, (name, d) in enumerate([("Nexus Solutions Inc", 80), ("Apex Digital Inc", 65),
                                     ("Nexus Solutions Inc", 50), ("Pinnacle Tech", 35),
                                     ("Apex Digital Inc", 20)]):
        add(_txn(carl, "deposit", "chequing", 2800.0 + i * 200, _dt(d, 9),
                 source=f"Consulting Client", counterparty_name=name))
    # Rent (3)
    for d in [70, 40, 5]:
        add(_txn(carl, "e_transfer_out", "chequing", 1800.0, _dt(d, 8),
                 destination="Metro Properties", counterparty_name="Metro Properties"))
    # Normal spending (5)
    for name, amt, d in [("Costco", 280.0, 60), ("Shell Gas", 72.0, 45),
                          ("Amazon.ca", 156.0, 30), ("Uber Eats", 42.0, 15),
                          ("Winners", 95.0, 8)]:
        add(_txn(carl, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    # Phone
    add(_txn(carl, "withdrawal", "chequing", 75.0, _dt(22, 9),
             destination="Koodo", counterparty_name="Koodo"))
    # Insurance
    add(_txn(carl, "withdrawal", "chequing", 190.0, _dt(55, 10),
             destination="Desjardins Insurance", counterparty_name="Desjardins Insurance"))
    # THE SUSPICIOUS DAY: fiat -> crypto -> external in 3 hours
    add(_txn(carl, "deposit", "chequing", 18000.0, _dt(2, 9, 0),
             source="Wire Transfer", counterparty_name="Offshore Holdings Ltd",
             metadata={"flagged": True, "wire_ref": "WIRE-2024-0891"}))
    add(_txn(carl, "crypto_buy", "crypto", 16500.0, _dt(2, 10, 30),
             destination="Binance", counterparty_name="Binance",
             metadata={"asset": "BTC"}))
    add(_txn(carl, "crypto_send", "crypto", 16200.0, _dt(2, 12, 0),
             destination="0x9f2c4a8e1b7d3f6c5a0e9d2b4f7a1c3e8b5d",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0x9f2c4a8e..."}))
    # Small legitimate crypto trade before suspicious day (establishes crypto usage)
    add(_txn(carl, "crypto_buy", "crypto", 500.0, _dt(25, 14),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "ETH"}))
    add(_txn(carl, "crypto_sell", "crypto", 520.0, _dt(18, 11),
             source="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "ETH"}))
    # Total: 26 txns

    # ==========================================================================
    # 12. DANA OSEI - Coordinated group leader (expected: L3, score ~0.85)
    # ==========================================================================
    # 4 new CPs within 7 days -> cp_burst=0.85 -> L3.
    # Crypto sends to 0x7a3f cluster. Cross-client link with Eve and Frank.
    dana = clients["dana"].id
    # Payroll (6)
    for w in [1, 3, 5, 7, 9, 11]:
        add(_txn(dana, "deposit", "chequing", 2100.0, _dt(w * 7, 9),
                 source="City Sales Corp", counterparty_name="City Sales Corp"))
    # Rent (3)
    for d in [60, 30, 3]:
        add(_txn(dana, "e_transfer_out", "chequing", 1400.0, _dt(d, 8),
                 destination="Urban Properties Inc", counterparty_name="Urban Properties Inc"))
    # Normal spending (5)
    for name, amt, d in [("Dollarama", 25.0, 55), ("Popeyes", 18.0, 40),
                          ("TTC Pass", 156.0, 28), ("Shoppers", 42.0, 18),
                          ("Metro", 130.0, 10)]:
        add(_txn(dana, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    # Phone
    add(_txn(dana, "withdrawal", "chequing", 55.0, _dt(35, 9),
             destination="Fido", counterparty_name="Fido"))
    # COORDINATED: 4 new senders within 7 days
    add(_txn(dana, "e_transfer_in", "chequing", 3200.0, _dt(6, 13),
             source="New sender 1", counterparty_name="Kevin B."))
    add(_txn(dana, "e_transfer_in", "chequing", 2800.0, _dt(5, 10),
             source="New sender 2", counterparty_name="Priya S."))
    add(_txn(dana, "e_transfer_in", "chequing", 4100.0, _dt(3, 15),
             source="New sender 3", counterparty_name="Liam W."))
    add(_txn(dana, "e_transfer_in", "chequing", 3500.0, _dt(2, 11),
             source="New sender 4", counterparty_name="Zara N."))
    # Crypto sends to 0x7a3f cluster
    add(_txn(dana, "crypto_send", "crypto", 11200.0, _dt(1, 16),
             destination="0x7a3f8b2c1d9e4f5a6b7c8d9e0f1a2b3c4d5e6f",
             counterparty_name="Crypto Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c..."}))
    # Follow-up smaller send next day
    add(_txn(dana, "crypto_send", "crypto", 2400.0, _dt(0.5, 10),
             destination="0x7a3f8b2c1d9e4f5a6b7c8d9e0f1a2b3c4d5e6f",
             counterparty_name="Crypto Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c..."}))
    # Small crypto buy to fund the sends
    add(_txn(dana, "crypto_buy", "crypto", 14000.0, _dt(1.5, 9),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    # Total: 28 txns

    # ==========================================================================
    # 13. EVE JOHANSSON - Coordinated participant (expected: L3, score ~0.85)
    # ==========================================================================
    # 3 new CPs within 7 days -> cp_burst=0.85 -> L3.
    # Crypto send to SAME 0x7a3f wallet as Dana. Cross-client correlation.
    eve = clients["eve"].id
    # Payroll (6)
    for w in [1, 3, 5, 7, 9, 11]:
        add(_txn(eve, "deposit", "chequing", 1850.0, _dt(w * 7, 9),
                 source="Service Plus Ltd", counterparty_name="Service Plus Ltd"))
    # Rent (3)
    for d in [60, 30, 3]:
        add(_txn(eve, "e_transfer_out", "chequing", 1200.0, _dt(d, 8),
                 destination="Affordable Homes Corp", counterparty_name="Affordable Homes Corp"))
    # Normal spending (4)
    for name, amt, d in [("Walmart", 95.0, 50), ("Tim Hortons", 8.50, 35),
                          ("Shoppers", 32.0, 20), ("No Frills", 110.0, 10)]:
        add(_txn(eve, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    # Phone
    add(_txn(eve, "withdrawal", "chequing", 45.0, _dt(25, 9),
             destination="Public Mobile", counterparty_name="Public Mobile"))
    # COORDINATED: 3 new senders within 7 days
    add(_txn(eve, "e_transfer_in", "chequing", 2400.0, _dt(6, 14),
             source="New sender A", counterparty_name="Ryan C."))
    add(_txn(eve, "e_transfer_in", "chequing", 1900.0, _dt(4, 11),
             source="New sender B", counterparty_name="Sofia M."))
    add(_txn(eve, "e_transfer_in", "chequing", 2700.0, _dt(2, 9),
             source="New sender C", counterparty_name="Jaden T."))
    # Crypto buy to fund send
    add(_txn(eve, "crypto_buy", "crypto", 6800.0, _dt(1.5, 10),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    # Crypto send to SAME 0x7a3f wallet as Dana
    add(_txn(eve, "crypto_send", "crypto", 6400.0, _dt(1, 14),
             destination="0x7a3f8b2c1d9e4f5a6b7c8d9e0f1a2b3c4d5e6f",
             counterparty_name="Crypto Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c..."}))
    # Second smaller send
    add(_txn(eve, "crypto_send", "crypto", 1800.0, _dt(0.5, 11),
             destination="0x7a3f8b2c1d9e4f5a6b7c8d9e0f1a2b3c4d5e6f",
             counterparty_name="Crypto Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c..."}))
    # Total: 24 txns

    # ==========================================================================
    # 14. GRACE OKONKWO - Severe income inconsistency (expected: L3, score ~0.88)
    # ==========================================================================
    # Stated $38K -> $3,167/mo. 5 e-transfers from shell companies = $20K in 30d.
    # Ratio = 6.3x -> income_conf ~0.88 -> L3 full investigation.
    grace = clients["grace"].id
    # Payroll (6)
    for w in [1, 3, 5, 7, 9, 11]:
        add(_txn(grace, "deposit", "chequing", 1800.0, _dt(w * 7, 9),
                 source="Admin Services Corp", counterparty_name="Admin Services Corp"))
    # Rent (3)
    for d in [60, 30, 3]:
        add(_txn(grace, "e_transfer_out", "chequing", 1100.0, _dt(d, 8),
                 destination="River View Apartments", counterparty_name="River View Apartments"))
    # Groceries (4)
    for name, amt, d in [("Loblaws", 140.0, 55), ("No Frills", 85.0, 40),
                          ("T&T Supermarket", 95.0, 20), ("Walmart", 110.0, 8)]:
        add(_txn(grace, "withdrawal", "chequing", amt, _dt(d, 12),
                 destination=name, counterparty_name=name))
    # Bills (3)
    add(_txn(grace, "withdrawal", "chequing", 75.0, _dt(45, 14),
             destination="Rogers", counterparty_name="Rogers"))
    add(_txn(grace, "withdrawal", "chequing", 120.0, _dt(32, 14),
             destination="Toronto Hydro", counterparty_name="Toronto Hydro"))
    add(_txn(grace, "withdrawal", "chequing", 95.0, _dt(18, 9),
             destination="Bell Canada", counterparty_name="Bell Canada"))
    # INCOME INCONSISTENCY: 5 large e-transfers from shell-looking companies
    add(_txn(grace, "e_transfer_in", "chequing", 5500.0, _dt(25, 14),
             source="Unknown A", counterparty_name="Coastal Import LLC",
             metadata={"flagged": True}))
    add(_txn(grace, "e_transfer_in", "chequing", 4200.0, _dt(18, 11),
             source="Unknown B", counterparty_name="Pacific Trade Group",
             metadata={"flagged": True}))
    add(_txn(grace, "e_transfer_in", "chequing", 5300.0, _dt(10, 16),
             source="Unknown C", counterparty_name="Northern Goods Inc",
             metadata={"flagged": True}))
    add(_txn(grace, "e_transfer_in", "chequing", 2800.0, _dt(5, 10),
             source="Unknown D", counterparty_name="Global Exports Ltd",
             metadata={"flagged": True}))
    add(_txn(grace, "e_transfer_in", "chequing", 1900.0, _dt(2, 15),
             source="Unknown E", counterparty_name="Global Exports Ltd",
             metadata={"flagged": True}))
    # Total: 26 txns

    # ==========================================================================
    # 15. JAMES OKAFOR - Mule account (expected: L3, score ~0.92)
    # ==========================================================================
    # 8 new CPs within 7 days -> cp_burst=0.85. Crypto send within 3hrs of deposit.
    # rapid_crypto_conversion=0.92. Multiple indicators active simultaneously.
    james = clients["james"].id
    # Minimal payroll (4 - new account)
    for w in [4, 6, 8, 10]:
        add(_txn(james, "deposit", "chequing", 1500.0, _dt(w * 7, 9),
                 source="Metro Coffee Chain", counterparty_name="Metro Coffee Chain"))
    # Spending (3)
    for name, amt, d in [("Subway", 12.0, 55), ("Dollar Tree", 8.0, 35),
                          ("Shoppers", 22.0, 15)]:
        add(_txn(james, "withdrawal", "chequing", amt, _dt(d, 13),
                 destination=name, counterparty_name=name))
    # MULE PATTERN: 8 new senders within 7 days
    senders = [
        ("Alex H.", 480.0, 6, 10), ("Maria K.", 650.0, 6, 14),
        ("Tom B.", 520.0, 5, 9), ("Yuki S.", 780.0, 5, 15),
        ("Amir P.", 440.0, 4, 11), ("Leila C.", 590.0, 4, 16),
        ("Owen D.", 720.0, 3, 12), ("Nina R.", 520.0, 3, 14),
    ]
    for name, amt, days_ago, hour in senders:
        add(_txn(james, "e_transfer_in", "chequing", amt, _dt(days_ago, hour),
                 source=f"Interac from {name}", counterparty_name=name))
    # Crypto buy
    add(_txn(james, "crypto_buy", "crypto", 3500.0, _dt(3, 13),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    # RAPID CRYPTO CONVERSION: crypto_send within 3hrs of Owen D. deposit
    add(_txn(james, "crypto_send", "crypto", 4200.0, _dt(3, 15),
             destination="0xf4e2a1b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4",
             counterparty_name="Anonymous Wallet",
             metadata={"asset": "USDT", "external_wallet": "0xf4e2a1b8..."}))
    # 3 repeat deposits from some of the same senders (deepens pattern)
    add(_txn(james, "e_transfer_in", "chequing", 520.0, _dt(2, 10),
             source="Repeat", counterparty_name="Alex H."))
    add(_txn(james, "e_transfer_in", "chequing", 680.0, _dt(2, 14),
             source="Repeat", counterparty_name="Maria K."))
    add(_txn(james, "e_transfer_in", "chequing", 450.0, _dt(1, 11),
             source="Repeat", counterparty_name="Tom B."))
    # Second crypto send
    add(_txn(james, "crypto_send", "crypto", 1400.0, _dt(1, 16),
             destination="0xf4e2a1b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4",
             counterparty_name="Anonymous Wallet",
             metadata={"asset": "USDT", "external_wallet": "0xf4e2a1b8..."}))
    # Total: 30 txns

    # ==========================================================================
    # 16. WEI ZHANG - Round-tripping (expected: L3, score ~0.82)
    # ==========================================================================
    # Funds leave via wire, return 14 days later from different entity at similar amount.
    # Pattern repeats twice. Plus income inconsistency from wire amounts.
    wei = clients["wei"].id
    # Payroll (4)
    for w in [2, 4, 6, 8]:
        add(_txn(wei, "deposit", "chequing", 3125.0, _dt(w * 7, 9),
                 source="Pacific Rim Consulting", counterparty_name="Pacific Rim Consulting"))
    # Normal spending (6)
    for name, amt, d in [("T&T Supermarket", 180.0, 70), ("Petro-Canada", 65.0, 55),
                          ("Best Buy", 350.0, 45), ("LCBO", 48.0, 30),
                          ("Home Depot", 220.0, 15), ("Metro", 95.0, 5)]:
        add(_txn(wei, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    # Rent
    for d in [60, 30, 3]:
        add(_txn(wei, "e_transfer_out", "chequing", 2200.0, _dt(d, 8),
                 destination="Pacific Heights Apartments", counterparty_name="Pacific Heights Apartments"))
    # ROUND-TRIPPING CYCLE 1: wire out, then 14 days later wire in from diff entity
    add(_txn(wei, "e_transfer_out", "chequing", 12000.0, _dt(50, 10),
             destination="Asia Pacific Trading Ltd", counterparty_name="Asia Pacific Trading Ltd",
             metadata={"wire_ref": "WIRE-OUT-001"}))
    add(_txn(wei, "e_transfer_in", "chequing", 11400.0, _dt(36, 11),
             source="Pacific Commerce Group", counterparty_name="Pacific Commerce Group",
             metadata={"wire_ref": "WIRE-IN-001", "flagged": True}))
    # ROUND-TRIPPING CYCLE 2: same pattern, different entities
    add(_txn(wei, "e_transfer_out", "chequing", 15000.0, _dt(25, 10),
             destination="Orient Star Holdings", counterparty_name="Orient Star Holdings",
             metadata={"wire_ref": "WIRE-OUT-002"}))
    add(_txn(wei, "e_transfer_in", "chequing", 14200.0, _dt(11, 14),
             source="Golden Dragon Enterprises", counterparty_name="Golden Dragon Enterprises",
             metadata={"wire_ref": "WIRE-IN-002", "flagged": True}))
    # Crypto activity (adds layering indicator)
    add(_txn(wei, "crypto_buy", "crypto", 5000.0, _dt(8, 15),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(wei, "crypto_sell", "crypto", 4800.0, _dt(4, 11),
             source="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    # Phone
    add(_txn(wei, "withdrawal", "chequing", 95.0, _dt(20, 9),
             destination="Telus", counterparty_name="Telus"))
    # Total: 28 txns

    # ==========================================================================
    # 17. AMARA DIALLO - Multi-hop layering (expected: L3, score ~0.94)
    # ==========================================================================
    # Student, $18K/yr. $15K from unknown -> BTC buy -> ETH swap -> external send.
    # All within 6 hours. Income ratio astronomical. Multiple layering indicators.
    amara = clients["amara"].id
    # Part-time payroll (4)
    for w in [2, 4, 6, 8]:
        add(_txn(amara, "deposit", "chequing", 750.0, _dt(w * 7, 9),
                 source="Campus Bookstore", counterparty_name="Campus Bookstore"))
    # Rent (3)
    for d in [60, 30, 3]:
        add(_txn(amara, "e_transfer_out", "chequing", 650.0, _dt(d, 8),
                 destination="Student Housing Co-op", counterparty_name="Student Housing Co-op"))
    # Textbooks (2)
    add(_txn(amara, "withdrawal", "chequing", 180.0, _dt(75, 14),
             destination="University Bookstore", counterparty_name="University Bookstore"))
    add(_txn(amara, "withdrawal", "chequing", 145.0, _dt(40, 14),
             destination="Amazon.ca", counterparty_name="Amazon.ca"))
    # Normal student spending
    add(_txn(amara, "withdrawal", "chequing", 15.0, _dt(50, 12),
             destination="Tim Hortons", counterparty_name="Tim Hortons"))
    add(_txn(amara, "withdrawal", "chequing", 8.0, _dt(25, 10),
             destination="Subway", counterparty_name="Subway"))
    # MULTI-HOP LAYERING CYCLE 1: $15K unknown -> BTC -> ETH -> external (6hrs)
    add(_txn(amara, "e_transfer_in", "chequing", 15000.0, _dt(2, 9, 0),
             source="Unknown Sender", counterparty_name="Investment Opportunity Corp",
             metadata={"flagged": True}))
    add(_txn(amara, "crypto_buy", "crypto", 14500.0, _dt(2, 10, 0),
             destination="Binance", counterparty_name="Binance",
             metadata={"asset": "BTC"}))
    add(_txn(amara, "crypto_sell", "crypto", 14200.0, _dt(2, 12, 0),
             source="Binance", counterparty_name="Binance",
             metadata={"asset": "BTC", "to_asset": "ETH", "from_asset": "BTC"}))
    add(_txn(amara, "crypto_send", "crypto", 13800.0, _dt(2, 15, 0),
             destination="0xa1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
             counterparty_name="External Wallet",
             metadata={"asset": "ETH", "external_wallet": "0xa1b2c3d4..."}))
    # LAYERING CYCLE 2 (smaller): $4K in -> crypto -> external
    add(_txn(amara, "e_transfer_in", "chequing", 4000.0, _dt(1, 9, 0),
             source="Unknown Sender 2", counterparty_name="Quick Returns LLC",
             metadata={"flagged": True}))
    add(_txn(amara, "crypto_buy", "crypto", 3800.0, _dt(1, 10, 30),
             destination="Binance", counterparty_name="Binance",
             metadata={"asset": "BTC"}))
    add(_txn(amara, "crypto_send", "crypto", 3600.0, _dt(1, 13, 0),
             destination="0xa1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xa1b2c3d4..."}))
    # Transit pass
    add(_txn(amara, "withdrawal", "chequing", 128.0, _dt(15, 8),
             destination="PRESTO", counterparty_name="PRESTO"))
    # Total: 24 txns

    # ==========================================================================
    # 18. VIKTOR PETROV - Extreme patterns (expected: near-L4, score ~0.95)
    # ==========================================================================
    # 3 massive wire deposits ($25K, $18K, $22K) in one week from shell companies.
    # Immediate crypto conversion to multiple different wallets.
    # Income ratio ~14x. Extreme deviation from baseline.
    viktor = clients["viktor"].id
    # Minimal legitimate payroll (3)
    for w in [4, 8, 12]:
        add(_txn(viktor, "deposit", "chequing", 1875.0, _dt(w * 7, 9),
                 source="Eastern European Imports", counterparty_name="Eastern European Imports"))
    # Spending (3)
    for name, amt, d in [("Walmart", 85.0, 75), ("Petro-Canada", 60.0, 50),
                          ("No Frills", 95.0, 25)]:
        add(_txn(viktor, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    # Rent
    add(_txn(viktor, "e_transfer_out", "chequing", 1200.0, _dt(30, 8),
             destination="Scarborough Apartments", counterparty_name="Scarborough Apartments"))
    # EXTREME: 3 massive wire deposits in one week
    add(_txn(viktor, "deposit", "chequing", 25000.0, _dt(6, 9),
             source="Wire Transfer", counterparty_name="Baltic Shipping Consolidated",
             metadata={"flagged": True, "wire_ref": "WIRE-BALTIC-001"}))
    add(_txn(viktor, "deposit", "chequing", 18000.0, _dt(4, 11),
             source="Wire Transfer", counterparty_name="Eurasian Trade Holdings",
             metadata={"flagged": True, "wire_ref": "WIRE-EURAS-002"}))
    add(_txn(viktor, "deposit", "chequing", 22000.0, _dt(2, 14),
             source="Wire Transfer", counterparty_name="North Sea Commodities Ltd",
             metadata={"flagged": True, "wire_ref": "WIRE-NSEA-003"}))
    # Immediate crypto conversion
    add(_txn(viktor, "crypto_buy", "crypto", 24000.0, _dt(5.5, 15),
             destination="Binance", counterparty_name="Binance",
             metadata={"asset": "BTC"}))
    add(_txn(viktor, "crypto_buy", "crypto", 17000.0, _dt(3.5, 16),
             destination="Binance", counterparty_name="Binance",
             metadata={"asset": "ETH"}))
    add(_txn(viktor, "crypto_buy", "crypto", 21000.0, _dt(1.5, 10),
             destination="Binance", counterparty_name="Binance",
             metadata={"asset": "USDT"}))
    # Sends to MULTIPLE different external wallets
    add(_txn(viktor, "crypto_send", "crypto", 23500.0, _dt(5, 18),
             destination="0xc1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9",
             counterparty_name="External Wallet 1",
             metadata={"asset": "BTC", "external_wallet": "0xc1d2e3f4..."}))
    add(_txn(viktor, "crypto_send", "crypto", 16500.0, _dt(3, 19),
             destination="0xe5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3",
             counterparty_name="External Wallet 2",
             metadata={"asset": "ETH", "external_wallet": "0xe5f6a7b8..."}))
    add(_txn(viktor, "crypto_send", "crypto", 20500.0, _dt(1, 14),
             destination="0xf7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5",
             counterparty_name="External Wallet 3",
             metadata={"asset": "USDT", "external_wallet": "0xf7a8b9c0..."}))
    # Phone
    add(_txn(viktor, "withdrawal", "chequing", 50.0, _dt(15, 9),
             destination="Chatr", counterparty_name="Chatr"))
    # Small ATM withdrawal
    add(_txn(viktor, "withdrawal", "chequing", 200.0, _dt(10, 12),
             destination="ATM", counterparty_name="ATM"))
    # Total: 22 txns

    # ==========================================================================
    # 19. CHEN WEI LI - Account takeover pattern (expected: near-L4, score ~0.95)
    # ==========================================================================
    # 5-year account, retired teacher. Extremely stable baseline (pension + pharmacy).
    # Then sudden: 3 e-transfers out to unknowns, crypto buy (never used crypto!).
    # Behavioral deviation from 5yr baseline is extreme.
    chen = clients["chen"].id
    # Regular pension deposits (8 monthly over past months)
    for m in range(8):
        add(_txn(chen, "deposit", "chequing", 2167.0, _dt(m * 30 + 5, 9),
                 source="Ontario Teachers Pension Plan", counterparty_name="Ontario Teachers Pension Plan"))
    # Pharmacy (3)
    for d in [75, 45, 15]:
        add(_txn(chen, "withdrawal", "chequing", 85.0, _dt(d, 10),
                 destination="Rexall Pharmacy", counterparty_name="Rexall Pharmacy"))
    # Groceries (4)
    for i, d in enumerate([80, 55, 30, 8]):
        add(_txn(chen, "withdrawal", "chequing", 95.0 + i * 10, _dt(d, 11),
                 destination="T&T Supermarket", counterparty_name="T&T Supermarket"))
    # TFSA (steady saver)
    add(_txn(chen, "deposit", "tfsa", 500.0, _dt(60, 14), counterparty_name="Self Transfer"))
    add(_txn(chen, "deposit", "tfsa", 500.0, _dt(30, 14), counterparty_name="Self Transfer"))
    # Utilities (stable, known)
    add(_txn(chen, "withdrawal", "chequing", 65.0, _dt(40, 14),
             destination="Toronto Hydro", counterparty_name="Toronto Hydro"))
    add(_txn(chen, "withdrawal", "chequing", 50.0, _dt(20, 14),
             destination="Enbridge Gas", counterparty_name="Enbridge Gas"))
    # ACCOUNT TAKEOVER PATTERN: sudden deviation from 5yr stable baseline
    # 3 e-transfers out to never-before-seen counterparties within 2 days
    add(_txn(chen, "e_transfer_out", "chequing", 4000.0, _dt(2, 11),
             destination="Unknown Recipient", counterparty_name="Jason R.",
             metadata={"new_device": True, "ip_changed": True}))
    add(_txn(chen, "e_transfer_out", "chequing", 4000.0, _dt(2, 14),
             destination="Unknown Recipient 2", counterparty_name="Nicole P.",
             metadata={"new_device": True}))
    add(_txn(chen, "e_transfer_out", "chequing", 4000.0, _dt(1, 9),
             destination="Unknown Recipient 3", counterparty_name="Brandon K.",
             metadata={"new_device": True}))
    # Crypto buy - client has NEVER used crypto in 5 years
    add(_txn(chen, "crypto_buy", "crypto", 8000.0, _dt(1, 15),
             destination="Binance", counterparty_name="Binance",
             metadata={"asset": "BTC", "first_crypto_ever": True}))
    # Total: 24 txns

    # ==========================================================================
    # 20. YUKI TANAKA - Second coordinated cluster (expected: L3, score ~0.85)
    # ==========================================================================
    # 3 new senders within 7 days -> cp_burst=0.85 -> L3.
    # Crypto send to 0x8b4f cluster (links to Marcus Webb).
    yuki = clients["yuki"].id
    # Freelance payments (5 - irregular)
    for name, d in [("Wedding Photo Co", 65), ("Portrait Studio", 50),
                     ("Event Planners Inc", 35), ("Magazine Weekly", 20),
                     ("Wedding Photo Co", 8)]:
        add(_txn(yuki, "e_transfer_in", "chequing", 1500.0 + (d * 13 % 1000), _dt(d, 10),
                 source=name, counterparty_name=name))
    # Rent (3)
    for d in [60, 30, 3]:
        add(_txn(yuki, "e_transfer_out", "chequing", 1300.0, _dt(d, 8),
                 destination="Kensington Market Lofts", counterparty_name="Kensington Market Lofts"))
    # Spending (4)
    for name, amt, d in [("Henry's Photo", 320.0, 55), ("Amazon.ca", 85.0, 40),
                          ("Uber", 22.0, 25), ("Metro", 110.0, 12)]:
        add(_txn(yuki, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    # COORDINATED: 3 new senders within 7 days
    add(_txn(yuki, "e_transfer_in", "chequing", 1800.0, _dt(6, 11),
             source="New sender 1", counterparty_name="Ravi M."))
    add(_txn(yuki, "e_transfer_in", "chequing", 2500.0, _dt(4, 14),
             source="New sender 2", counterparty_name="Andrea S."))
    add(_txn(yuki, "e_transfer_in", "chequing", 1500.0, _dt(2, 10),
             source="New sender 3", counterparty_name="Kofi A."))
    # Crypto buy
    add(_txn(yuki, "crypto_buy", "crypto", 5500.0, _dt(1.5, 15),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    # Crypto send to 0x8b4f cluster (links to Marcus Webb)
    add(_txn(yuki, "crypto_send", "crypto", 5800.0, _dt(1, 11),
             destination="0x8b4f2a1c3d7e9f0b5a6c8d4e2f1a3b7c9d0e5f",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0x8b4f2a1c..."}))
    # Phone
    add(_txn(yuki, "withdrawal", "chequing", 55.0, _dt(18, 9),
             destination="Koodo", counterparty_name="Koodo"))
    # Total: 22 txns

    # Bulk add all transactions
    for t in txns:
        db.add(t)
    db.flush()


# -- Main seed function ---------------------------------------------------------

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
    print(f"\nSeed complete: {len(clients)} clients with transactions seeded.")
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
