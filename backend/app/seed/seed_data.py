"""
Seed script -- populates the database with clients and transactions for all demo scenarios.
Profiles, restrictions, and investigations are NOT pre-seeded -- they are created when
the analyst clicks "Run Simulation" on the dashboard.

Run with:
    cd backend && python -m app.seed.seed_data

=============================================================================
TYPOLOGY COVERAGE (mapped to FINTRAC ML/TF indicators & FATF red flags)
=============================================================================

  L0 Auto-Resolve (5 clients):
    1  Alice Chen       : Clean payroll depositor, established CPs
    2  Henry Park       : Salary spike from KNOWN employer (bonus)
    3  Natasha Volkov   : Freelancer with irregular but legit income
    4  Raj Patel        : Small business owner, seasonal fluctuation
    5  Maria Santos     : RRSP deadline season large deposit (benign spike)

  L1 Monitor (3 clients):
    6  David Kim        : Travel-triggered geo anomaly + larger purchase
    7  Lisa Thompson    : Inheritance deposit (large one-time, new CP)
    8  Omar Hassan      : Remittances to high-risk jurisdiction (legit family)

  L2 Guardrail (5 clients):
    9  Isabel Torres    : Minor structuring (2x near-$10K within 7d)
   10  Frank Lim        : Coordinated minor participant (0x7a3f cluster)
   11  Priya Sharma     : Moderate income inconsistency (family trust)
   12  Marcus Webb      : Early mule signals + 0x8b4f cluster link
   13  Sophie Laurent   : Crypto volatility (legit day-trader)

  L3 Investigation (13 clients):
   14  Bob Kamara       : FINTRAC structuring + rapid crypto exit
   15  Carl Mendez      : Crypto layering (fiat->BTC->external <3hrs)
   16  Dana Osei        : Coordinated group leader (0x7a3f cluster)
   17  Eve Johansson    : Coordinated participant (0x7a3f cluster)
   18  Grace Okonkwo    : Severe income inconsistency (shell companies)
   19  James Okafor     : Mule account (8+ new senders -> crypto)
   20  Wei Zhang        : Round-tripping (wire out -> wire in, diff entity)
   21  Amara Diallo     : Multi-hop layering (fiat->BTC->ETH->external)
   22  Elena Petrova    : Pig butchering VICTIM (escalating crypto over weeks)
   23  Kwame Asante     : Smurfing funnel account (many small in, bulk out)
   24  Tariq Al-Rashidi : Trade-based ML (invoice inconsistencies + layering)
   25  Nadia Ivanova    : Dormant account reactivation (2yr quiet -> burst)
   26  Rachel Chen      : Romance scam VICTIM (elderly, e-transfers to "partner")

  Near-L4 / Extreme (2 clients):
   27  Viktor Petrov    : Extreme wire deposits + multi-wallet crypto exit
   28  Chen Wei Li      : Account takeover pattern (5yr baseline shattered)

  Coordinated Clusters:
   29  Yuki Tanaka      : 0x8b4f cluster (links to Marcus Webb)
   30  Kofi Mensah      : 0x5c2d cluster (links to Kwame Asante)

  Clusters:
    Cluster 1 (0x7a3f): Dana + Eve + Frank
    Cluster 2 (0x8b4f): Yuki + Marcus
    Cluster 3 (0x5c2d): Kwame + Kofi (smurfing network)

=============================================================================
FINTRAC INDICATORS COVERED:
  - Structuring below $10K reporting threshold (Bob, Isabel)
  - Income inconsistency (Grace, Amara, Priya, James)
  - Rapid fiat-to-crypto conversion (Carl, James, Amara, Viktor)
  - Crypto layering / multi-hop (Amara, Carl, Viktor)
  - Round-tripping (Wei)
  - Money mule patterns (James, Marcus, Kwame, Kofi)
  - Coordinated network activity (Dana+Eve+Frank, Yuki+Marcus, Kwame+Kofi)
  - Shell company counterparties (Grace, Tariq, Viktor)
  - Transactions with high-risk jurisdictions (Omar benign, Tariq suspicious)
  - Pig butchering / investment fraud victim (Elena)
  - Romance scam victim (Rachel)
  - Dormant account reactivation (Nadia)
  - Trade-based money laundering (Tariq)
  - Smurfing / funnel account (Kwame, Kofi)
  - Account takeover / device anomaly (Chen Wei Li)
  - Privacy coin / mixing indicators (via wallet metadata)
  - PEP-adjacent transactions (Tariq)
  - Unusual transaction timing patterns (coordinated clusters)
  - Third-party directed transactions (mule accounts)
=============================================================================
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import uuid
from datetime import datetime, timedelta
from typing import Optional

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


# Shared wallet addresses for cluster detection
WALLET_CLUSTER_1 = "0x7a3f8b2c1d9e4f5a6b7c8d9e0f1a2b3c4d5e6f"  # Dana+Eve+Frank
WALLET_CLUSTER_2 = "0x8b4f2a1c3d7e9f0b5a6c8d4e2f1a3b7c9d0e5f"  # Yuki+Marcus
WALLET_CLUSTER_3 = "0x5c2d9a3b7e1f4c8d2a6b0e3f5c7d9a1b4e6f8c"  # Kwame+Kofi


# -- Clients -------------------------------------------------------------------

def _create_clients(db: Session) -> dict[str, Client]:
    clients_data = [
        # ======================================================================
        # L0 AUTO-RESOLVE (5)
        # ======================================================================
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

        dict(id=str(uuid.uuid4()), name="Maria Santos", date_of_birth="1986-01-19",
             stated_income=88000.0, occupation="Registered Nurse",
             kyc_level="enhanced", account_opened_at=_dt(600),
             products_held=["chequing", "rrsp", "tfsa"]),

        # ======================================================================
        # L1 MONITOR (3)
        # ======================================================================
        dict(id=str(uuid.uuid4()), name="David Kim", date_of_birth="1991-09-03",
             stated_income=105000.0, occupation="Management Consultant",
             kyc_level="enhanced", account_opened_at=_dt(540),
             products_held=["chequing", "tfsa", "crypto"]),

        dict(id=str(uuid.uuid4()), name="Lisa Thompson", date_of_birth="1965-12-07",
             stated_income=62000.0, occupation="Office Manager",
             kyc_level="enhanced", account_opened_at=_dt(1200),
             products_held=["chequing", "tfsa"]),

        dict(id=str(uuid.uuid4()), name="Omar Hassan", date_of_birth="1987-05-22",
             stated_income=55000.0, occupation="Civil Engineer",
             kyc_level="enhanced", account_opened_at=_dt(365),
             products_held=["chequing", "tfsa"]),

        # ======================================================================
        # L2 GUARDRAIL (5)
        # ======================================================================
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

        # ======================================================================
        # L3 INVESTIGATION (13)
        # ======================================================================
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

        # NEW L3 clients
        dict(id=str(uuid.uuid4()), name="Elena Petrova", date_of_birth="1970-08-30",
             stated_income=48000.0, occupation="Bookkeeper",
             kyc_level="enhanced", account_opened_at=_dt(800),
             products_held=["chequing", "tfsa", "crypto"]),

        dict(id=str(uuid.uuid4()), name="Kwame Asante", date_of_birth="1995-03-11",
             stated_income=32000.0, occupation="Delivery Driver",
             kyc_level="standard", account_opened_at=_dt(110),
             products_held=["chequing", "crypto"]),

        dict(id=str(uuid.uuid4()), name="Tariq Al-Rashidi", date_of_birth="1980-11-25",
             stated_income=95000.0, occupation="International Trade Consultant",
             kyc_level="enhanced", account_opened_at=_dt(450),
             products_held=["chequing", "crypto"]),

        dict(id=str(uuid.uuid4()), name="Nadia Ivanova", date_of_birth="1993-06-14",
             stated_income=44000.0, occupation="Graphic Designer",
             kyc_level="standard", account_opened_at=_dt(730),
             products_held=["chequing", "crypto"]),

        dict(id=str(uuid.uuid4()), name="Rachel Chen", date_of_birth="1955-03-28",
             stated_income=38000.0, occupation="Retired Librarian (Pension)",
             kyc_level="enhanced", account_opened_at=_dt(2000),
             products_held=["chequing", "tfsa"]),

        # ======================================================================
        # NEAR-L4 / EXTREME (2)
        # ======================================================================
        dict(id=str(uuid.uuid4()), name="Viktor Petrov", date_of_birth="1986-10-14",
             stated_income=45000.0, occupation="Import/Export Trader",
             kyc_level="standard", account_opened_at=_dt(120),
             products_held=["chequing", "crypto"]),

        dict(id=str(uuid.uuid4()), name="Chen Wei Li", date_of_birth="1958-02-20",
             stated_income=52000.0, occupation="Retired Teacher (Pension)",
             kyc_level="enhanced", account_opened_at=_dt(1825),
             products_held=["chequing", "tfsa"]),

        # ======================================================================
        # COORDINATED CLUSTER MEMBERS (2)
        # ======================================================================
        dict(id=str(uuid.uuid4()), name="Yuki Tanaka", date_of_birth="1993-06-09",
             stated_income=40000.0, occupation="Freelance Photographer",
             kyc_level="standard", account_opened_at=_dt(150),
             products_held=["chequing", "crypto"]),

        dict(id=str(uuid.uuid4()), name="Kofi Mensah", date_of_birth="1997-09-18",
             stated_income=30000.0, occupation="Rideshare Driver",
             kyc_level="standard", account_opened_at=_dt(95),
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
    # FINTRAC profile: No indicators. Consistent payroll from known employer,
    # stable counterparties, spending matches income level. 480-day account.
    # 30d inflow ~$4,800 vs monthly income $6,000 -> ratio 0.8.
    alice = clients["alice"].id

    # Bi-weekly payroll (8 deposits over ~16 weeks, consistent amount)
    for i, w in enumerate([0.5, 2.5, 4.5, 6.5, 8.5, 10.5, 12.5, 14.5]):
        add(_txn(alice, "deposit", "chequing", 2400.0, _dt(w * 7, 9, 0),
                 source="Maple Leaf Technologies", counterparty_name="Maple Leaf Technologies",
                 metadata={"deposit_method": "direct_deposit", "pay_period": f"bi-weekly-{i+1}"}))

    # TFSA contributions (quarterly, consistent pattern)
    for d in [90, 60, 30, 5]:
        add(_txn(alice, "deposit", "tfsa", 500.0, _dt(d, 11), counterparty_name="Self Transfer"))

    # Rent (4 months, same landlord, same amount)
    for d in [90, 60, 30, 3]:
        add(_txn(alice, "e_transfer_out", "chequing", 1650.0, _dt(d, 8, 0),
                 destination="Pacific Properties Ltd", counterparty_name="Pacific Properties Ltd"))

    # Recurring bills (all known CPs, consistent timing)
    bill_schedule = [
        ("Rogers Wireless", 95.0, [85, 55, 25]),
        ("BC Hydro", 140.0, [80, 50, 20]),
        ("Netflix", 22.99, [78, 48, 18]),
        ("GoodLife Fitness", 55.0, [75, 45, 15]),
        ("Spotify", 11.99, [72, 42, 12]),
    ]
    for name, amt, days in bill_schedule:
        for d in days:
            add(_txn(alice, "withdrawal", "chequing", amt, _dt(d, 14),
                     destination=name, counterparty_name=name))

    # Groceries (known stores, realistic weekly frequency)
    grocery_trips = [
        ("Loblaw", 178.50, 82), ("Loblaw", 195.20, 68), ("Loblaw", 162.80, 54),
        ("Loblaw", 185.40, 40), ("Loblaw", 171.90, 26), ("Loblaw", 192.30, 12),
        ("Shoppers Drug Mart", 62.40, 70), ("Shoppers Drug Mart", 38.90, 35),
        ("Shoppers Drug Mart", 55.70, 7),
    ]
    for name, amt, d in grocery_trips:
        add(_txn(alice, "withdrawal", "chequing", amt, _dt(d, 11 + d % 4),
                 destination=name, counterparty_name=name))

    # Misc spending (restaurants, gas, personal)
    misc = [
        ("Petro-Canada", 65.40, 60), ("Petro-Canada", 58.20, 30), ("Petro-Canada", 71.80, 5),
        ("Tim Hortons", 12.50, 50), ("Tim Hortons", 8.90, 22), ("Tim Hortons", 14.20, 3),
        ("IKEA", 1200.0, 42), ("Amazon.ca", 89.99, 35), ("Amazon.ca", 45.50, 15),
        ("Indigo Books", 32.99, 28),
    ]
    for name, amt, d in misc:
        add(_txn(alice, "withdrawal", "chequing", amt, _dt(d, 13 + d % 5),
                 destination=name, counterparty_name=name))

    # Self transfer savings
    add(_txn(alice, "e_transfer_out", "chequing", 300.0, _dt(45, 10),
             destination="Self - Savings", counterparty_name="Self Transfer"))
    add(_txn(alice, "e_transfer_out", "chequing", 300.0, _dt(15, 10),
             destination="Self - Savings", counterparty_name="Self Transfer"))

    # ==========================================================================
    # 2. HENRY PARK - Salary spike auto-resolve (expected: L0)
    # ==========================================================================
    # FINTRAC: One large deposit ($8,500) but from SAME employer as regular payroll.
    # Known employer, 2yr+ account, enhanced KYC. Metadata confirms "Q4 bonus".
    # struct_conf ~0.35 (only 1 txn in band), income ratio ~1.07.
    henry = clients["henry"].id

    # Regular payroll (10 bi-weekly, very consistent)
    for w in range(1, 21, 2):
        add(_txn(henry, "deposit", "chequing", 3958.0, _dt(w * 7, 9),
                 source="Northern Dynamics Corp", counterparty_name="Northern Dynamics Corp",
                 metadata={"deposit_method": "direct_deposit"}))

    # RRSP contributions (established pattern)
    for d in [90, 60, 30]:
        add(_txn(henry, "deposit", "rrsp", 2500.0, _dt(d, 11), counterparty_name="Self Transfer"))

    # TFSA
    for d in [85, 55, 25]:
        add(_txn(henry, "deposit", "tfsa", 1000.0, _dt(d, 11), counterparty_name="Self Transfer"))

    # Mortgage (long-running, same amount/CP for years)
    for d in [90, 60, 30, 2]:
        add(_txn(henry, "withdrawal", "chequing", 2800.0, _dt(d, 14),
                 destination="TD Mortgage Services", counterparty_name="TD Mortgage Services"))

    # Groceries
    for i in range(8):
        store = ["Costco", "Whole Foods", "No Frills", "Loblaws"][i % 4]
        amt = [320.0, 185.0, 95.0, 210.0][i % 4] + (i * 5 % 30)
        add(_txn(henry, "withdrawal", "chequing", amt, _dt(i * 12 + 3, 11),
                 destination=store, counterparty_name=store))

    # Recurring bills
    for d in [80, 50, 20]:
        add(_txn(henry, "withdrawal", "chequing", 225.0, _dt(d, 9),
                 destination="Intact Insurance", counterparty_name="Intact Insurance"))
    for d in [75, 45, 15]:
        add(_txn(henry, "withdrawal", "chequing", 165.0, _dt(d, 14),
                 destination="Enbridge Gas", counterparty_name="Enbridge Gas"))
    for d in [70, 40, 10]:
        add(_txn(henry, "withdrawal", "chequing", 85.0, _dt(d, 14),
                 destination="Rogers Wireless", counterparty_name="Rogers Wireless"))

    # Kids activities
    add(_txn(henry, "withdrawal", "chequing", 450.0, _dt(65, 10),
             destination="Toronto Swim Club", counterparty_name="Toronto Swim Club"))
    add(_txn(henry, "withdrawal", "chequing", 380.0, _dt(35, 10),
             destination="Kumon Learning Centre", counterparty_name="Kumon Learning Centre"))

    # THE FLAGGED DEPOSIT: $8,500 bonus from KNOWN employer -> auto-resolve
    add(_txn(henry, "deposit", "chequing", 8500.0, _dt(4, 10),
             source="Northern Dynamics Corp", counterparty_name="Northern Dynamics Corp",
             metadata={"memo": "Q4 performance bonus", "deposit_method": "direct_deposit"}))

    # ==========================================================================
    # 3. NATASHA VOLKOV - Freelancer, irregular but legit (expected: L0)
    # ==========================================================================
    # FINTRAC: Irregular consulting payments from 3 KNOWN long-term clients.
    # All CPs established over 400+ day account history. Amounts vary but
    # match stated freelance income. No new counterparties.
    natasha = clients["natasha"].id

    # Consulting payments from 3 known long-term clients (irregular timing, variable amounts)
    consulting = [
        ("Bright Ideas Studio", 3200.0, 95), ("Bright Ideas Studio", 4100.0, 70),
        ("Bright Ideas Studio", 2800.0, 45), ("Bright Ideas Studio", 3500.0, 20),
        ("Digital Wave Agency", 4500.0, 85), ("Digital Wave Agency", 3800.0, 55),
        ("Digital Wave Agency", 5000.0, 30), ("Digital Wave Agency", 2500.0, 8),
        ("Northstar UX Corp", 6000.0, 75), ("Northstar UX Corp", 4200.0, 40),
    ]
    for name, amt, d in consulting:
        add(_txn(natasha, "e_transfer_in", "chequing", amt, _dt(d, 10 + d % 4),
                 source=name, counterparty_name=name,
                 metadata={"memo": "Consulting invoice"}))

    # Rent (same landlord, consistent)
    for d in [90, 60, 30, 3]:
        add(_txn(natasha, "e_transfer_out", "chequing", 1800.0, _dt(d, 8),
                 destination="Maple Ridge Properties", counterparty_name="Maple Ridge Properties"))

    # Professional expenses (tools, conferences - legitimate for freelancer)
    add(_txn(natasha, "withdrawal", "chequing", 79.99, _dt(80, 9),
             destination="Adobe Inc", counterparty_name="Adobe Inc"))
    add(_txn(natasha, "withdrawal", "chequing", 79.99, _dt(50, 9),
             destination="Adobe Inc", counterparty_name="Adobe Inc"))
    add(_txn(natasha, "withdrawal", "chequing", 79.99, _dt(20, 9),
             destination="Adobe Inc", counterparty_name="Adobe Inc"))
    add(_txn(natasha, "withdrawal", "chequing", 1200.0, _dt(60, 16),
             destination="UX Canada Conference", counterparty_name="UX Canada Conference"))
    add(_txn(natasha, "withdrawal", "chequing", 2499.0, _dt(35, 14),
             destination="Apple Store", counterparty_name="Apple Store",
             metadata={"memo": "MacBook Pro - business equipment"}))

    # Utilities and bills
    for d in [85, 55, 25]:
        add(_txn(natasha, "withdrawal", "chequing", 120.0 + d % 20, _dt(d, 14),
                 destination="FortisBC", counterparty_name="FortisBC"))
    for d in [80, 50, 20]:
        add(_txn(natasha, "withdrawal", "chequing", 85.0, _dt(d, 14),
                 destination="Telus", counterparty_name="Telus"))

    # Groceries and daily
    for d in [88, 72, 58, 44, 28, 14, 4]:
        add(_txn(natasha, "withdrawal", "chequing", 75.0 + (d * 3 % 60), _dt(d, 12),
                 destination="Whole Foods Market", counterparty_name="Whole Foods Market"))

    # Amazon (3 purchases)
    for d, amt in [(65, 125.0), (38, 89.99), (12, 54.50)]:
        add(_txn(natasha, "withdrawal", "chequing", amt, _dt(d, 13),
                 destination="Amazon.ca", counterparty_name="Amazon.ca"))

    # TFSA
    for d in [70, 35]:
        add(_txn(natasha, "deposit", "tfsa", 750.0, _dt(d, 11), counterparty_name="Self Transfer"))

    # ==========================================================================
    # 4. RAJ PATEL - Small business owner, seasonal (expected: L0)
    # ==========================================================================
    # FINTRAC: Daily Square deposits vary widely. Known supplier payments, CRA tax
    # remittances. High stated income ($110K), 2.5yr account. Seasonal December spike
    # is normal for restaurant industry.
    raj = clients["raj"].id

    # Square payment deposits (daily restaurant revenue, varies significantly)
    square_deposits = [
        (95, 840.0), (92, 1210.0), (89, 680.0), (86, 1540.0), (83, 920.0),
        (80, 1750.0), (77, 2100.0), (74, 650.0), (71, 1380.0), (68, 990.0),
        (65, 1620.0), (62, 2450.0), (59, 780.0), (56, 1340.0), (53, 1890.0),
        (50, 710.0), (47, 1560.0), (44, 2200.0), (41, 1050.0), (38, 1430.0),
        (35, 1780.0), (32, 2380.0), (29, 1150.0), (26, 1640.0), (23, 920.0),
        (20, 1870.0), (17, 2510.0), (14, 1280.0), (11, 1690.0), (8, 1440.0),
        (5, 1920.0), (2, 2150.0),
    ]
    for d, amt in square_deposits:
        add(_txn(raj, "deposit", "chequing", amt, _dt(d, 18 + d % 3),
                 source="Square Payments", counterparty_name="Square Payments",
                 metadata={"deposit_method": "merchant_deposit"}))

    # Supplier payments (recurring, established)
    for d in [85, 55, 25]:
        add(_txn(raj, "e_transfer_out", "chequing", 2400.0 + d * 3, _dt(d, 10),
                 destination="Sysco Food Services", counterparty_name="Sysco Food Services"))
    for d in [80, 50, 20]:
        add(_txn(raj, "e_transfer_out", "chequing", 1800.0 + d * 2, _dt(d, 10),
                 destination="GFS Canada", counterparty_name="GFS Canada"))
    for d in [75, 45]:
        add(_txn(raj, "e_transfer_out", "chequing", 850.0, _dt(d, 10),
                 destination="Coca-Cola Bottling", counterparty_name="Coca-Cola Bottling"))

    # Commercial rent
    for d in [90, 60, 30, 1]:
        add(_txn(raj, "e_transfer_out", "chequing", 4200.0, _dt(d, 8),
                 destination="Dundas Commercial Properties",
                 counterparty_name="Dundas Commercial Properties"))

    # CRA quarterly tax remittances (known CP)
    for d in [85, 55]:
        add(_txn(raj, "withdrawal", "chequing", 6500.0 + d * 10, _dt(d, 9),
                 destination="CRA - GST/HST", counterparty_name="Canada Revenue Agency"))

    # Equipment lease, insurance, staff payroll
    for d in [80, 50, 20]:
        add(_txn(raj, "withdrawal", "chequing", 450.0, _dt(d, 10),
                 destination="Kitchen Equipment Leasing",
                 counterparty_name="Kitchen Equipment Leasing"))
    add(_txn(raj, "withdrawal", "chequing", 380.0, _dt(70, 11),
             destination="Aviva Insurance", counterparty_name="Aviva Insurance"))
    add(_txn(raj, "withdrawal", "chequing", 380.0, _dt(40, 11),
             destination="Aviva Insurance", counterparty_name="Aviva Insurance"))

    # Staff payroll (bi-weekly, 2 employees)
    for d in [84, 70, 56, 42, 28, 14]:
        add(_txn(raj, "e_transfer_out", "chequing", 1850.0, _dt(d, 16),
                 destination="Staff - Maria R.", counterparty_name="Maria R."))
        add(_txn(raj, "e_transfer_out", "chequing", 1650.0, _dt(d, 16, 5),
                 destination="Staff - Ahmed K.", counterparty_name="Ahmed K."))

    # Personal draw
    for d in [75, 45, 15]:
        add(_txn(raj, "e_transfer_out", "chequing", 3000.0, _dt(d, 15),
                 destination="Self - Personal", counterparty_name="Raj Patel"))

    # ==========================================================================
    # 5. MARIA SANTOS - RRSP deadline season (expected: L0)
    # ==========================================================================
    # FINTRAC: Large $12K deposit near RRSP deadline from KNOWN bank transfer.
    # 600-day enhanced KYC account. Seasonal pattern visible in prior year data.
    # Legitimate tax-optimization behavior.
    maria = clients["maria"].id

    # Bi-weekly nursing payroll (stable, known employer)
    for w in range(1, 19, 2):
        add(_txn(maria, "deposit", "chequing", 3667.0, _dt(w * 7, 9),
                 source="Sunnybrook Health Sciences", counterparty_name="Sunnybrook Health Sciences",
                 metadata={"deposit_method": "direct_deposit"}))

    # Rent/mortgage
    for d in [90, 60, 30, 3]:
        add(_txn(maria, "withdrawal", "chequing", 2200.0, _dt(d, 14),
                 destination="Scotiabank Mortgage", counterparty_name="Scotiabank Mortgage"))

    # Bills (3 months each)
    for d in [85, 55, 25]:
        add(_txn(maria, "withdrawal", "chequing", 110.0, _dt(d, 14),
                 destination="Toronto Hydro", counterparty_name="Toronto Hydro"))
    for d in [82, 52, 22]:
        add(_txn(maria, "withdrawal", "chequing", 75.0, _dt(d, 14),
                 destination="Rogers Wireless", counterparty_name="Rogers Wireless"))
    for d in [78, 48, 18]:
        add(_txn(maria, "withdrawal", "chequing", 160.0, _dt(d, 14),
                 destination="Intact Insurance", counterparty_name="Intact Insurance"))

    # Groceries
    for d in [88, 74, 62, 48, 34, 22, 10]:
        add(_txn(maria, "withdrawal", "chequing", 140.0 + d % 40, _dt(d, 11),
                 destination="Loblaws", counterparty_name="Loblaws"))

    # Regular RRSP and TFSA (established pattern)
    for d in [85, 55, 25]:
        add(_txn(maria, "deposit", "rrsp", 1500.0, _dt(d, 11), counterparty_name="Self Transfer"))
    for d in [80, 50, 20]:
        add(_txn(maria, "deposit", "tfsa", 500.0, _dt(d, 11), counterparty_name="Self Transfer"))

    # THE FLAGGED DEPOSIT: Large RRSP contribution near deadline from bank transfer
    # This is benign - RRSP deadline is Feb/Mar, many Canadians do lump-sum contributions.
    add(_txn(maria, "deposit", "chequing", 12000.0, _dt(5, 10),
             source="TD Bank - Transfer", counterparty_name="Self - TD Savings Account",
             metadata={"memo": "RRSP catch-up contribution", "transfer_type": "interbank"}))
    add(_txn(maria, "deposit", "rrsp", 12000.0, _dt(4, 11),
             counterparty_name="Self Transfer",
             metadata={"memo": "2024 RRSP contribution room"}))

    # Misc spending
    for name, amt, d in [("Sephora", 85.0, 65), ("Indigo Books", 32.0, 45),
                          ("Uber", 28.0, 25), ("Starbucks", 7.50, 10)]:
        add(_txn(maria, "withdrawal", "chequing", amt, _dt(d, 13),
                 destination=name, counterparty_name=name))

    # ==========================================================================
    # 6. DAVID KIM - Travel-triggered geo anomaly (expected: L1 Monitor)
    # ==========================================================================
    # FINTRAC: Login from Germany, some larger-than-usual purchases. But 540-day
    # account, enhanced KYC, high income. Previous travel patterns exist.
    # Slight behavioral deviation but not enough for L2.
    david = clients["david"].id

    # Consulting payroll (bi-weekly)
    for w in range(1, 17, 2):
        add(_txn(david, "deposit", "chequing", 4375.0, _dt(w * 7, 9),
                 source="McKinsey & Company", counterparty_name="McKinsey & Company",
                 metadata={"deposit_method": "direct_deposit"}))

    # Rent
    for d in [90, 60, 30, 3]:
        add(_txn(david, "e_transfer_out", "chequing", 2400.0, _dt(d, 8),
                 destination="Bay Street Residences", counterparty_name="Bay Street Residences"))

    # Normal Canadian spending (establishing baseline)
    for d in [88, 72, 58, 44, 28, 14]:
        add(_txn(david, "withdrawal", "chequing", 160.0 + d % 50, _dt(d, 12),
                 destination="Loblaws", counterparty_name="Loblaws",
                 metadata={"geo": "Toronto, ON", "device": "iPhone-14-Pro"}))
    for d in [85, 55, 25]:
        add(_txn(david, "withdrawal", "chequing", 65.0, _dt(d, 17),
                 destination="Petro-Canada", counterparty_name="Petro-Canada",
                 metadata={"geo": "Toronto, ON"}))

    # Bills
    for d in [80, 50, 20]:
        add(_txn(david, "withdrawal", "chequing", 95.0, _dt(d, 14),
                 destination="Bell Canada", counterparty_name="Bell Canada"))

    # Small crypto trades (established user)
    add(_txn(david, "crypto_buy", "crypto", 1000.0, _dt(60, 14),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC", "geo": "Toronto, ON"}))
    add(_txn(david, "crypto_sell", "crypto", 1050.0, _dt(40, 11),
             source="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC", "geo": "Toronto, ON"}))

    # TRAVEL ANOMALY: Purchases suddenly from Frankfurt, Germany
    # (Legitimate business travel but triggers geo-deviation)
    add(_txn(david, "withdrawal", "chequing", 320.0, _dt(5, 19),
             destination="Marriott Frankfurt", counterparty_name="Marriott Hotel",
             metadata={"geo": "Frankfurt, DE", "device": "iPhone-14-Pro", "ip": "85.214.132.xx"}))
    add(_txn(david, "withdrawal", "chequing", 85.0, _dt(4, 12),
             destination="Restaurant Frankfurter Haus", counterparty_name="Restaurant",
             metadata={"geo": "Frankfurt, DE"}))
    add(_txn(david, "withdrawal", "chequing", 2200.0, _dt(3, 15),
             destination="Rolex Boutique Frankfurt", counterparty_name="Rolex Boutique",
             metadata={"geo": "Frankfurt, DE",
                        "note": "Unusual luxury purchase while abroad - triggers L1"}))
    add(_txn(david, "crypto_buy", "crypto", 3000.0, _dt(3, 20),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "ETH", "geo": "Frankfurt, DE",
                        "note": "Crypto buy from travel location"}))

    # ==========================================================================
    # 7. LISA THOMPSON - Inheritance deposit (expected: L1 Monitor)
    # ==========================================================================
    # FINTRAC: $45K deposit from estate executor (new CP). 1200-day account, very
    # stable baseline of pension + modest spending. Large deposit is anomalous
    # relative to baseline but single event from identifiable source.
    lisa = clients["lisa"].id

    # Pension deposits (very stable, monthly for years)
    for m in range(12):
        add(_txn(lisa, "deposit", "chequing", 2583.0, _dt(m * 30 + 5, 9),
                 source="Ontario Public Service Pension", counterparty_name="OPSEU Pension Trust",
                 metadata={"deposit_method": "direct_deposit"}))

    # Very stable, predictable spending (3+ years of history implied)
    # Rent
    for d in [90, 60, 30, 3]:
        add(_txn(lisa, "withdrawal", "chequing", 1450.0, _dt(d, 14),
                 destination="Lakeshore Apartments", counterparty_name="Lakeshore Apartments"))

    # Groceries (same stores every week)
    for d in [88, 74, 60, 46, 32, 18, 4]:
        add(_txn(lisa, "withdrawal", "chequing", 85.0 + d % 25, _dt(d, 10),
                 destination="No Frills", counterparty_name="No Frills"))

    # Bills (very consistent)
    for d in [85, 55, 25]:
        add(_txn(lisa, "withdrawal", "chequing", 65.0, _dt(d, 14),
                 destination="Toronto Hydro", counterparty_name="Toronto Hydro"))
    for d in [82, 52, 22]:
        add(_txn(lisa, "withdrawal", "chequing", 45.0, _dt(d, 14),
                 destination="Koodo Mobile", counterparty_name="Koodo Mobile"))

    # Pharmacy (regular)
    for d in [80, 50, 20]:
        add(_txn(lisa, "withdrawal", "chequing", 42.0, _dt(d, 10),
                 destination="Shoppers Drug Mart", counterparty_name="Shoppers Drug Mart"))

    # TFSA (steady small saver)
    for d in [75, 45, 15]:
        add(_txn(lisa, "deposit", "tfsa", 300.0, _dt(d, 11), counterparty_name="Self Transfer"))

    # THE INHERITANCE: $45K from estate of deceased parent
    # New counterparty but identifiable, documented source
    add(_txn(lisa, "e_transfer_in", "chequing", 45000.0, _dt(6, 14),
             source="Estate of Margaret Thompson", counterparty_name="Gowling WLG - Estate Trust",
             metadata={"memo": "Inheritance distribution - Estate of Margaret Thompson",
                        "wire_ref": "ESTATE-2024-MT-0147",
                        "note": "New CP but documented estate distribution"}))

    # ==========================================================================
    # 8. OMAR HASSAN - Remittances to high-risk jurisdiction (expected: L1 Monitor)
    # ==========================================================================
    # FINTRAC indicator: Transactions involving jurisdictions known as higher ML/TF risk.
    # BUT: Omar has consistent employment, sends regular amounts to same family
    # members (established pattern), amounts match stated purpose (family support).
    # Enhanced KYC completed. Account 1yr+. This is legitimate diaspora remittance.
    omar = clients["omar"].id

    # Engineering payroll (stable)
    for w in range(1, 15, 2):
        add(_txn(omar, "deposit", "chequing", 2292.0, _dt(w * 7, 9),
                 source="SNC-Lavalin Group", counterparty_name="SNC-Lavalin Group",
                 metadata={"deposit_method": "direct_deposit"}))

    # Rent
    for d in [90, 60, 30, 3]:
        add(_txn(omar, "e_transfer_out", "chequing", 1600.0, _dt(d, 8),
                 destination="Greenfield Apartments", counterparty_name="Greenfield Apartments"))

    # Normal Canadian spending
    for d in [85, 65, 45, 25, 10]:
        add(_txn(omar, "withdrawal", "chequing", 110.0 + d % 30, _dt(d, 12),
                 destination="FreshCo", counterparty_name="FreshCo"))
    for d in [80, 50, 20]:
        add(_txn(omar, "withdrawal", "chequing", 75.0, _dt(d, 14),
                 destination="Freedom Mobile", counterparty_name="Freedom Mobile"))

    # TFSA
    for d in [75, 45, 15]:
        add(_txn(omar, "deposit", "tfsa", 400.0, _dt(d, 11), counterparty_name="Self Transfer"))

    # REMITTANCES: Monthly to same family member in Somalia via established MSB
    # Pattern is consistent, amount is stable, same recipient every time
    for d in [85, 55, 25]:
        add(_txn(omar, "e_transfer_out", "chequing", 800.0, _dt(d, 10),
                 destination="Dahabshiil Money Transfer",
                 counterparty_name="Dahabshiil Money Transfer",
                 metadata={"recipient": "Fatima Hassan (Mother)",
                            "destination_country": "SO",  # Somalia - FATF grey list
                            "purpose": "Family support",
                            "note": "Consistent monthly remittance to same family member via licensed MSB"}))

    # One slightly larger remittance (Eid)
    add(_txn(omar, "e_transfer_out", "chequing", 1500.0, _dt(10, 10),
             destination="Dahabshiil Money Transfer",
             counterparty_name="Dahabshiil Money Transfer",
             metadata={"recipient": "Fatima Hassan (Mother)",
                        "destination_country": "SO",
                        "purpose": "Eid celebration - family",
                        "note": "Seasonal increase, same CP and recipient"}))

    # ==========================================================================
    # 9. ISABEL TORRES - Minor structuring (expected: L2, score ~0.70)
    # ==========================================================================
    # FINTRAC indicator: "Client appears to be structuring amounts to avoid client
    # identification or reporting thresholds." Two deposits in $8K-$9.9K range
    # within 7 days from SAME counterparty. Combined exceeds $10K threshold.
    # But only 2 transactions (not 3+), and CP name is plausible business name.
    isabel = clients["isabel"].id

    # Regular payroll (established)
    for w in range(1, 15, 2):
        add(_txn(isabel, "deposit", "chequing", 3200.0, _dt(w * 7, 9),
                 source="BrightMark Agency", counterparty_name="BrightMark Agency",
                 metadata={"deposit_method": "direct_deposit"}))

    # Rent
    for d in [90, 60, 30, 3]:
        add(_txn(isabel, "e_transfer_out", "chequing", 2100.0, _dt(d, 8),
                 destination="Downtown Suites", counterparty_name="Downtown Suites"))

    # Normal spending (establishing baseline)
    spending_baseline = [
        ("Shoppers Drug Mart", 45.0, 85), ("Loblaws", 165.0, 72),
        ("H&M", 120.0, 58), ("Uber Eats", 35.0, 50), ("Starbucks", 8.50, 42),
        ("LCBO", 52.0, 35), ("Metro", 140.0, 28), ("Winners", 75.0, 22),
        ("Shoppers Drug Mart", 38.0, 15), ("Loblaws", 155.0, 8),
    ]
    for name, amt, d in spending_baseline:
        add(_txn(isabel, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))

    # Bills
    for d in [80, 50, 20]:
        add(_txn(isabel, "withdrawal", "chequing", 65.0, _dt(d, 10),
                 destination="Equinox", counterparty_name="Equinox"))
    for d in [78, 48, 18]:
        add(_txn(isabel, "withdrawal", "chequing", 95.0, _dt(d, 9),
                 destination="Bell Canada", counterparty_name="Bell Canada"))
    for d in [75, 45, 15]:
        add(_txn(isabel, "withdrawal", "chequing", 180.0, _dt(d, 14),
                 destination="TD Insurance", counterparty_name="TD Insurance"))

    # STRUCTURING PATTERN: 2 deposits in $8K-$10K band within 7 days
    # from SAME entity. Combined = $16,700 (exceeds $10K FINTRAC reporting).
    # FINTRAC indicator: "Multiple transactions conducted below the reporting
    # threshold within a short period."
    add(_txn(isabel, "e_transfer_in", "chequing", 8500.0, _dt(5, 14),
             source="Spark Ventures Ltd", counterparty_name="Spark Ventures Ltd",
             metadata={"memo": "Consulting payment - Phase 1",
                        "fintrac_indicator": "below_threshold_structuring"}))
    add(_txn(isabel, "e_transfer_in", "chequing", 8200.0, _dt(3, 11),
             source="Spark Ventures Ltd", counterparty_name="Spark Ventures Ltd",
             metadata={"memo": "Consulting payment - Phase 2",
                        "fintrac_indicator": "same_cp_split_payment"}))

    # Third payment from different CP (less suspicious but adds to 30d volume)
    add(_txn(isabel, "e_transfer_in", "chequing", 7500.0, _dt(1, 9),
             source="Creative Co", counterparty_name="Creative Co",
             metadata={"memo": "Design project payment"}))

    # ==========================================================================
    # 10. FRANK LIM - Coordinated minor participant (expected: L2, score ~0.60)
    # ==========================================================================
    # FINTRAC indicator: "Wire transfers to or from unrelated parties."
    # Only 2 new CPs (below L3 threshold of 3+). Crypto send to 0x7a3f wallet
    # creates cross-client link to Dana/Eve cluster. Recent account (62 days).
    frank = clients["frank"].id

    # Payroll (established)
    for w in range(1, 13, 2):
        add(_txn(frank, "deposit", "chequing", 2050.0, _dt(w * 7, 9),
                 source="Logistics Partners Inc", counterparty_name="Logistics Partners Inc"))

    # Rent
    for d in [60, 30, 3]:
        add(_txn(frank, "e_transfer_out", "chequing", 1500.0, _dt(d, 8),
                 destination="Eastside Rentals", counterparty_name="Eastside Rentals"))

    # Groceries
    for d in [55, 40, 25, 10]:
        add(_txn(frank, "withdrawal", "chequing", 120.0 + d % 30, _dt(d, 12),
                 destination="FreshCo", counterparty_name="FreshCo"))

    # Normal spending
    add(_txn(frank, "withdrawal", "chequing", 45.0, _dt(50, 14),
             destination="Canadian Tire", counterparty_name="Canadian Tire"))
    add(_txn(frank, "withdrawal", "chequing", 22.0, _dt(35, 10),
             destination="Tim Hortons", counterparty_name="Tim Hortons"))
    add(_txn(frank, "withdrawal", "chequing", 85.0, _dt(20, 15),
             destination="Walmart", counterparty_name="Walmart"))
    add(_txn(frank, "withdrawal", "chequing", 55.0, _dt(12, 9),
             destination="Chatr Mobile", counterparty_name="Chatr Mobile"))

    # COORDINATED: 2 new senders (below L3 threshold of 3)
    # FINTRAC indicator: "Client is accompanied by persons who appear to be
    # instructing the sending or receiving of wire transfers on their behalf"
    add(_txn(frank, "e_transfer_in", "chequing", 1800.0, _dt(5, 13),
             source="New sender X", counterparty_name="Malik A.",
             metadata={"new_counterparty": True}))
    add(_txn(frank, "e_transfer_in", "chequing", 1400.0, _dt(3, 10),
             source="New sender Y", counterparty_name="Chloe D.",
             metadata={"new_counterparty": True}))

    # Crypto send to 0x7a3f cluster (links to Dana/Eve)
    add(_txn(frank, "crypto_buy", "crypto", 3000.0, _dt(2.5, 14),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    add(_txn(frank, "crypto_send", "crypto", 2800.0, _dt(2, 15),
             destination=WALLET_CLUSTER_1,
             counterparty_name="Crypto Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c..."}))

    # ==========================================================================
    # 11. PRIYA SHARMA - Moderate income inconsistency (expected: L2)
    # ==========================================================================
    # FINTRAC indicator: "Transactional activity inconsistent with client's apparent
    # financial standing or occupational information."
    # Stated $35K -> $2,917/mo. 3 family trust transfers = $8,500 in 30d (2.91x).
    # BUT: 2yr account, trust name includes client surname, memo says "family support".
    priya = clients["priya"].id

    # Payroll (established, consistent)
    for w in range(1, 15, 2):
        add(_txn(priya, "deposit", "chequing", 1458.0, _dt(w * 7, 9),
                 source="City Services Corp", counterparty_name="City Services Corp"))

    # Rent
    for d in [90, 60, 30, 3]:
        add(_txn(priya, "e_transfer_out", "chequing", 1100.0, _dt(d, 8),
                 destination="Hillcrest Apartments", counterparty_name="Hillcrest Apartments"))

    # Spending (modest, matches stated income)
    for d in [88, 72, 58, 42, 28, 14]:
        add(_txn(priya, "withdrawal", "chequing", 65.0 + d % 30, _dt(d, 13),
                 destination="No Frills", counterparty_name="No Frills"))
    add(_txn(priya, "withdrawal", "chequing", 156.0, _dt(75, 8),
             destination="TTC Monthly Pass", counterparty_name="TTC"))
    add(_txn(priya, "withdrawal", "chequing", 156.0, _dt(45, 8),
             destination="TTC Monthly Pass", counterparty_name="TTC"))
    add(_txn(priya, "withdrawal", "chequing", 156.0, _dt(15, 8),
             destination="TTC Monthly Pass", counterparty_name="TTC"))

    # Bills
    for d in [80, 50, 20]:
        add(_txn(priya, "withdrawal", "chequing", 65.0, _dt(d, 14),
                 destination="Toronto Hydro", counterparty_name="Toronto Hydro"))
    for d in [78, 48, 18]:
        add(_txn(priya, "withdrawal", "chequing", 50.0, _dt(d, 9),
                 destination="Freedom Mobile", counterparty_name="Freedom Mobile"))

    # Modest personal spending
    for name, amt, d in [("Dollarama", 22.0, 65), ("Shoppers", 38.0, 40),
                          ("Winners", 75.0, 25), ("T&T Supermarket", 110.0, 10)]:
        add(_txn(priya, "withdrawal", "chequing", amt, _dt(d, 13),
                 destination=name, counterparty_name=name))

    # INCOME INCONSISTENCY: 3 transfers from "Sharma Family Trust" in 30 days
    # Total $8,500 vs monthly income $2,917 -> ratio 2.91x
    add(_txn(priya, "e_transfer_in", "chequing", 3500.0, _dt(25, 14),
             source="Sharma Family Trust", counterparty_name="Sharma Family Trust",
             metadata={"memo": "Family support - monthly", "trust_name_matches_surname": True}))
    add(_txn(priya, "e_transfer_in", "chequing", 2500.0, _dt(15, 11),
             source="Sharma Family Trust", counterparty_name="Sharma Family Trust",
             metadata={"memo": "Family support - monthly"}))
    add(_txn(priya, "e_transfer_in", "chequing", 2500.0, _dt(5, 16),
             source="Sharma Family Trust", counterparty_name="Sharma Family Trust",
             metadata={"memo": "Family support - monthly"}))

    # ==========================================================================
    # 12. MARCUS WEBB - Early mule signals (expected: L2, score ~0.60)
    # ==========================================================================
    # FINTRAC indicators: "Large and/or frequent wire transfers between senders
    # and receivers with no apparent relationship." New account (55 days),
    # low income ($26K), 2 new CPs + crypto send to 0x8b4f cluster.
    marcus = clients["marcus"].id

    # Payroll (minimal, part-time)
    for w in [2, 4, 6, 8]:
        add(_txn(marcus, "deposit", "chequing", 1083.0, _dt(w * 7, 9),
                 source="SecureGuard Services", counterparty_name="SecureGuard Services"))

    # Rent (cheap room)
    for d in [45, 30, 3]:
        add(_txn(marcus, "e_transfer_out", "chequing", 800.0, _dt(d, 8),
                 destination="Parkview Rooms", counterparty_name="Parkview Rooms"))

    # Spending (minimal - matches low income)
    for name, amt, d in [("McDonalds", 12.50, 50), ("Walmart", 65.0, 40),
                          ("Petro-Canada", 45.0, 30), ("Dollar Tree", 18.0, 20),
                          ("Subway", 14.0, 15), ("Tim Hortons", 8.50, 8),
                          ("Dollarama", 12.0, 5)]:
        add(_txn(marcus, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))

    # Bills
    add(_txn(marcus, "withdrawal", "chequing", 45.0, _dt(35, 9),
             destination="Chatr Mobile", counterparty_name="Chatr Mobile"))
    add(_txn(marcus, "withdrawal", "chequing", 128.0, _dt(25, 8),
             destination="TTC Monthly Pass", counterparty_name="TTC"))

    # EARLY MULE SIGNALS: 2 new senders within 7 days
    add(_txn(marcus, "e_transfer_in", "chequing", 550.0, _dt(6, 11),
             source="Unknown sender 1", counterparty_name="Derek L.",
             metadata={"new_counterparty": True}))
    add(_txn(marcus, "e_transfer_in", "chequing", 720.0, _dt(4, 14),
             source="Unknown sender 2", counterparty_name="Fatima H.",
             metadata={"new_counterparty": True}))

    # Crypto buy + send to 0x8b4f cluster
    add(_txn(marcus, "crypto_buy", "crypto", 900.0, _dt(3, 16),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(marcus, "crypto_send", "crypto", 850.0, _dt(2, 10),
             destination=WALLET_CLUSTER_2,
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0x8b4f2a1c..."}))

    # ==========================================================================
    # 13. SOPHIE LAURENT - Crypto volatility, legit trader (expected: L2)
    # ==========================================================================
    # Active crypto day-trader with high volume. All trades internal to Wealthsimple
    # (no external sends). Crypto score elevated from volume/frequency but no
    # external wallet risk.
    sophie = clients["sophie"].id

    # Payroll
    for w in range(1, 13, 2):
        add(_txn(sophie, "deposit", "chequing", 2833.0, _dt(w * 7, 9),
                 source="RBC Capital Markets", counterparty_name="RBC Capital Markets"))

    # Extensive crypto trading (all internal - buy/sell pairs)
    crypto_trades = [
        ("crypto_buy", "BTC", 1500.0, 70), ("crypto_sell", "BTC", 1580.0, 68),
        ("crypto_buy", "ETH", 2000.0, 62), ("crypto_sell", "ETH", 2200.0, 58),
        ("crypto_buy", "BTC", 800.0, 52), ("crypto_sell", "BTC", 850.0, 48),
        ("crypto_buy", "ETH", 1200.0, 42), ("crypto_sell", "ETH", 1150.0, 38),
        ("crypto_buy", "SOL", 500.0, 35), ("crypto_sell", "SOL", 620.0, 32),
        ("crypto_buy", "BTC", 3000.0, 28), ("crypto_sell", "BTC", 2900.0, 22),
        ("crypto_buy", "ETH", 1800.0, 18), ("crypto_sell", "ETH", 1950.0, 12),
    ]
    for type_, asset, amt, d in crypto_trades:
        cp = "Wealthsimple Crypto"
        add(_txn(sophie, type_, "crypto", amt, _dt(d, 14 + d % 5),
                 destination=cp if "buy" in type_ else None,
                 source=cp if "sell" in type_ else None,
                 counterparty_name=cp,
                 metadata={"asset": asset}))

    # ONE LARGE crypto buy that spikes the volume
    add(_txn(sophie, "crypto_buy", "crypto", 6000.0, _dt(5, 10),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))

    # Normal spending
    for name, amt, d in [("Sephora", 85.0, 65), ("Indigo Books", 42.0, 50),
                          ("Metro", 155.0, 40), ("Uber", 28.0, 25),
                          ("Starbucks", 7.50, 15), ("Yorkville Spa", 200.0, 8)]:
        add(_txn(sophie, "withdrawal", "chequing", amt, _dt(d, 13),
                 destination=name, counterparty_name=name))

    # Rent
    for d in [60, 30, 3]:
        add(_txn(sophie, "e_transfer_out", "chequing", 1900.0, _dt(d, 8),
                 destination="Yorkville Apartments", counterparty_name="Yorkville Apartments"))

    add(_txn(sophie, "withdrawal", "chequing", 80.0, _dt(45, 9),
             destination="Rogers", counterparty_name="Rogers"))

    # ==========================================================================
    # 14. BOB KAMARA - Structuring + crypto exit (expected: L3, score ~0.90)
    # ==========================================================================
    # FINTRAC indicators: "Client appears to be structuring amounts to avoid
    # client identification or reporting thresholds." + "Rapid movement of
    # funds not commensurate with client's financial profile." + "Funds
    # transferred in and out on the same day or within a relatively short
    # period of time."
    # 3 deposits in $9K-$9.5K band within 7 days from 3 different unknown
    # senders. Total $28,100 vs monthly income $4,667. Then rapid crypto
    # conversion and external send.
    bob = clients["bob"].id

    # Regular payroll (establishing baseline)
    for w in range(2, 22, 2):
        add(_txn(bob, "deposit", "chequing", 2200.0, _dt(w * 7, 9),
                 source="Retail Corp Payroll", counterparty_name="Retail Corp Payroll"))

    # Normal spending (establishing baseline)
    for name, amt, d in [("FoodCo", 350.0, 95), ("Best Buy", 220.0, 80),
                          ("Canadian Tire", 85.0, 65), ("Metro", 145.0, 50),
                          ("Pizza Pizza", 28.0, 38), ("Shoppers", 55.0, 25),
                          ("Walmart", 120.0, 18), ("Tim Hortons", 9.50, 12)]:
        add(_txn(bob, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))

    # Rent (established)
    for d in [90, 60, 30, 3]:
        add(_txn(bob, "e_transfer_out", "chequing", 1400.0, _dt(d, 8),
                 destination="King West Rentals", counterparty_name="King West Rentals"))

    # Bills
    for d in [85, 55, 25]:
        add(_txn(bob, "withdrawal", "chequing", 75.0, _dt(d, 14),
                 destination="Bell Canada", counterparty_name="Bell Canada"))

    # STRUCTURING: 3 near-$10K deposits within 7 days from UNKNOWNS
    # Each calibrated just below $10K FINTRAC Large Cash Transaction threshold.
    # Different senders on different days = classic structuring pattern.
    add(_txn(bob, "e_transfer_in", "chequing", 9200.0, _dt(6, 14, 30),
             source="Unknown sender A", counterparty_name="Marcus T.",
             metadata={"new_counterparty": True,
                        "fintrac_indicator": "structuring_below_10k",
                        "note": "Day 1 of structuring pattern"}))
    add(_txn(bob, "e_transfer_in", "chequing", 9500.0, _dt(4, 11, 15),
             source="Unknown sender B", counterparty_name="Jordan R.",
             metadata={"new_counterparty": True,
                        "fintrac_indicator": "structuring_below_10k",
                        "note": "Day 3 - different sender, same band"}))
    add(_txn(bob, "e_transfer_in", "chequing", 9400.0, _dt(2, 16, 0),
             source="Unknown sender C", counterparty_name="Tyler M.",
             metadata={"new_counterparty": True,
                        "fintrac_indicator": "structuring_below_10k",
                        "note": "Day 5 - third sender, same band"}))

    # RAPID CRYPTO EXIT: Buy then external send within hours
    # FINTRAC indicator: "Funds transferred in and out on the same day or
    # within a relatively short period of time."
    add(_txn(bob, "crypto_buy", "crypto", 8000.0, _dt(1.5, 10, 30),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(bob, "crypto_send", "crypto", 7500.0, _dt(1.3, 14, 0),
             destination="0xd3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xd3e4f5a6...",
                        "hours_since_deposit": 3.5,
                        "fintrac_indicator": "rapid_conversion_and_exit"}))

    # Second wave - next day
    add(_txn(bob, "crypto_buy", "crypto", 12000.0, _dt(0.8, 9, 0),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    add(_txn(bob, "crypto_send", "crypto", 11500.0, _dt(0.5, 12, 0),
             destination="0xd3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1",
             counterparty_name="External Wallet",
             metadata={"asset": "USDT", "external_wallet": "0xd3e4f5a6...",
                        "fintrac_indicator": "rapid_conversion_and_exit"}))

    # ==========================================================================
    # 15. CARL MENDEZ - Crypto layering (expected: L3, score ~0.92)
    # ==========================================================================
    # FINTRAC indicator: "A series of complicated transfers of funds that seems
    # to be an attempt to hide the source and intended use of the funds."
    # Classic layering: $18K wire from offshore entity -> crypto buy 1.5hrs later
    # -> crypto send to external wallet 3hrs after deposit.
    carl = clients["carl"].id

    # Consulting payments (establishing baseline, 5 known clients)
    for name, d in [("Nexus Solutions Inc", 90), ("Apex Digital Inc", 75),
                     ("Nexus Solutions Inc", 60), ("Pinnacle Tech", 45),
                     ("Apex Digital Inc", 30)]:
        add(_txn(carl, "deposit", "chequing", 2800.0 + d * 5, _dt(d, 9),
                 source="Consulting", counterparty_name=name))

    # Rent
    for d in [85, 55, 25, 5]:
        add(_txn(carl, "e_transfer_out", "chequing", 1800.0, _dt(d, 8),
                 destination="Metro Properties", counterparty_name="Metro Properties"))

    # Normal spending
    for name, amt, d in [("Costco", 280.0, 78), ("Shell Gas", 72.0, 62),
                          ("Amazon.ca", 156.0, 48), ("Uber Eats", 42.0, 35),
                          ("Winners", 95.0, 22), ("Shoppers", 55.0, 15)]:
        add(_txn(carl, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))

    for d in [80, 50, 20]:
        add(_txn(carl, "withdrawal", "chequing", 75.0, _dt(d, 9),
                 destination="Koodo", counterparty_name="Koodo"))

    # Small legitimate crypto trades (establishes crypto usage in baseline)
    add(_txn(carl, "crypto_buy", "crypto", 500.0, _dt(40, 14),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "ETH"}))
    add(_txn(carl, "crypto_sell", "crypto", 520.0, _dt(30, 11),
             source="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "ETH"}))

    # THE SUSPICIOUS DAY: Wire deposit -> crypto buy -> external send in 3 hours
    # FINTRAC: "Atypical transfers by client on an in-and-out basis, or other
    # methods of moving funds quickly"
    add(_txn(carl, "deposit", "chequing", 18000.0, _dt(2, 9, 0),
             source="Wire Transfer", counterparty_name="Offshore Holdings Ltd",
             metadata={"flagged": True, "wire_ref": "WIRE-2024-0891",
                        "originating_country": "BZ",  # Belize - secrecy jurisdiction
                        "fintrac_indicator": "wire_from_high_risk_jurisdiction"}))
    add(_txn(carl, "crypto_buy", "crypto", 16500.0, _dt(2, 10, 30),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC", "hours_since_wire": 1.5,
                        "fintrac_indicator": "rapid_conversion"}))
    add(_txn(carl, "crypto_send", "crypto", 16200.0, _dt(2, 12, 0),
             destination="0x9f2c4a8e1b7d3f6c5a0e9d2b4f7a1c3e8b5d",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0x9f2c4a8e...",
                        "hours_since_wire": 3.0,
                        "fintrac_indicator": "layering_fiat_to_crypto_to_external"}))

    # ==========================================================================
    # 16. DANA OSEI - Coordinated group leader (expected: L3, score ~0.85)
    # ==========================================================================
    # FINTRAC: "Multiple clients have sent wire transfers over a short period
    # of time to the same recipient." + counterparty burst.
    # 4 new senders in 7 days. Crypto consolidation to 0x7a3f shared wallet.
    dana = clients["dana"].id

    # Payroll
    for w in range(1, 13, 2):
        add(_txn(dana, "deposit", "chequing", 2100.0, _dt(w * 7, 9),
                 source="City Sales Corp", counterparty_name="City Sales Corp"))

    # Rent
    for d in [60, 30, 3]:
        add(_txn(dana, "e_transfer_out", "chequing", 1400.0, _dt(d, 8),
                 destination="Urban Properties Inc", counterparty_name="Urban Properties Inc"))

    # Normal spending
    for name, amt, d in [("Dollarama", 25.0, 55), ("Popeyes", 18.0, 45),
                          ("TTC Pass", 156.0, 40), ("Shoppers", 42.0, 30),
                          ("Metro", 130.0, 20), ("Tim Hortons", 8.50, 12)]:
        add(_txn(dana, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    add(_txn(dana, "withdrawal", "chequing", 55.0, _dt(50, 9),
             destination="Fido", counterparty_name="Fido"))

    # COORDINATED PATTERN: 4 new senders within 7 days
    # FINTRAC: "Multiple persons are sending wire transfers that are similar
    # in amounts, receiver names, security questions, addresses"
    add(_txn(dana, "e_transfer_in", "chequing", 3200.0, _dt(6, 13),
             source="New sender 1", counterparty_name="Kevin B.",
             metadata={"new_counterparty": True, "cluster": "0x7a3f"}))
    add(_txn(dana, "e_transfer_in", "chequing", 2800.0, _dt(5, 10),
             source="New sender 2", counterparty_name="Priya S.",
             metadata={"new_counterparty": True, "cluster": "0x7a3f"}))
    add(_txn(dana, "e_transfer_in", "chequing", 4100.0, _dt(3, 15),
             source="New sender 3", counterparty_name="Liam W.",
             metadata={"new_counterparty": True, "cluster": "0x7a3f"}))
    add(_txn(dana, "e_transfer_in", "chequing", 3500.0, _dt(2, 11),
             source="New sender 4", counterparty_name="Zara N.",
             metadata={"new_counterparty": True, "cluster": "0x7a3f"}))

    # Crypto consolidation to shared wallet
    add(_txn(dana, "crypto_buy", "crypto", 14000.0, _dt(1.5, 9),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    add(_txn(dana, "crypto_send", "crypto", 11200.0, _dt(1, 16),
             destination=WALLET_CLUSTER_1,
             counterparty_name="Crypto Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c...",
                        "fintrac_indicator": "coordinated_network_consolidation"}))
    add(_txn(dana, "crypto_send", "crypto", 2400.0, _dt(0.5, 10),
             destination=WALLET_CLUSTER_1,
             counterparty_name="Crypto Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c..."}))

    # ==========================================================================
    # 17. EVE JOHANSSON - Coordinated participant (expected: L3, score ~0.85)
    # ==========================================================================
    # Same pattern as Dana but 3 new senders. Sends to SAME 0x7a3f wallet.
    # Cross-client correlation with Dana is the key detection.
    eve = clients["eve"].id

    for w in range(1, 13, 2):
        add(_txn(eve, "deposit", "chequing", 1850.0, _dt(w * 7, 9),
                 source="Service Plus Ltd", counterparty_name="Service Plus Ltd"))

    for d in [60, 30, 3]:
        add(_txn(eve, "e_transfer_out", "chequing", 1200.0, _dt(d, 8),
                 destination="Affordable Homes Corp", counterparty_name="Affordable Homes Corp"))

    for name, amt, d in [("Walmart", 95.0, 55), ("Tim Hortons", 8.50, 45),
                          ("Shoppers", 32.0, 35), ("No Frills", 110.0, 22),
                          ("Metro", 85.0, 12)]:
        add(_txn(eve, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    add(_txn(eve, "withdrawal", "chequing", 45.0, _dt(40, 9),
             destination="Public Mobile", counterparty_name="Public Mobile"))

    # COORDINATED: 3 new senders within 7 days (timed to overlap with Dana)
    add(_txn(eve, "e_transfer_in", "chequing", 2400.0, _dt(6, 14),
             source="New sender A", counterparty_name="Ryan C.",
             metadata={"new_counterparty": True, "cluster": "0x7a3f"}))
    add(_txn(eve, "e_transfer_in", "chequing", 1900.0, _dt(4, 11),
             source="New sender B", counterparty_name="Sofia M.",
             metadata={"new_counterparty": True, "cluster": "0x7a3f"}))
    add(_txn(eve, "e_transfer_in", "chequing", 2700.0, _dt(2, 9),
             source="New sender C", counterparty_name="Jaden T.",
             metadata={"new_counterparty": True, "cluster": "0x7a3f"}))

    add(_txn(eve, "crypto_buy", "crypto", 6800.0, _dt(1.5, 10),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    add(_txn(eve, "crypto_send", "crypto", 6400.0, _dt(1, 14),
             destination=WALLET_CLUSTER_1,
             counterparty_name="Crypto Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x7a3f8b2c...",
                        "same_wallet_as": "Dana Osei",
                        "fintrac_indicator": "coordinated_crypto_consolidation"}))

    # ==========================================================================
    # 18. GRACE OKONKWO - Severe income inconsistency (expected: L3, score ~0.88)
    # ==========================================================================
    # FINTRAC: "Transactional activity far exceeds projected activity" + "Transaction
    # involves a suspected shell entity (entity with no economical or logical
    # reason to exist)." 5 e-transfers from generic company names = $19,700 in
    # 30d vs monthly income $3,167 -> ratio 6.2x.
    grace = clients["grace"].id

    for w in range(1, 13, 2):
        add(_txn(grace, "deposit", "chequing", 1800.0, _dt(w * 7, 9),
                 source="Admin Services Corp", counterparty_name="Admin Services Corp"))

    for d in [60, 30, 3]:
        add(_txn(grace, "e_transfer_out", "chequing", 1100.0, _dt(d, 8),
                 destination="River View Apartments", counterparty_name="River View Apartments"))

    for d in [85, 70, 55, 40, 25, 10]:
        add(_txn(grace, "withdrawal", "chequing", 80.0 + d % 35, _dt(d, 12),
                 destination="No Frills", counterparty_name="No Frills"))

    for d in [80, 50, 20]:
        add(_txn(grace, "withdrawal", "chequing", 75.0, _dt(d, 14),
                 destination="Rogers", counterparty_name="Rogers"))
    for d in [75, 45, 15]:
        add(_txn(grace, "withdrawal", "chequing", 120.0, _dt(d, 14),
                 destination="Toronto Hydro", counterparty_name="Toronto Hydro"))

    # SHELL COMPANY TRANSFERS: Generic names, no apparent business relationship
    # FINTRAC: "Transaction involves a suspected shell entity"
    shell_transfers = [
        ("Coastal Import LLC", 5500.0, 28), ("Pacific Trade Group", 4200.0, 22),
        ("Northern Goods Inc", 5300.0, 15), ("Global Exports Ltd", 2800.0, 8),
        ("Global Exports Ltd", 1900.0, 3),
    ]
    for name, amt, d in shell_transfers:
        add(_txn(grace, "e_transfer_in", "chequing", amt, _dt(d, 10 + d % 6),
                 source="Unknown", counterparty_name=name,
                 metadata={"flagged": True, "new_counterparty": True,
                            "fintrac_indicator": "suspected_shell_entity",
                            "note": f"Generic import/export name, no relationship to admin assistant occupation"}))

    # ==========================================================================
    # 19. JAMES OKAFOR - Mule account (expected: L3, score ~0.92)
    # ==========================================================================
    # FINTRAC indicators: "Client sending to, or receiving wire transfers from,
    # multiple clients" + "Funds transferred in and out on the same day" +
    # "Income inconsistency." Classic money mule pattern: young person, low
    # income, new account, sudden influx from 8 unknown senders, rapid
    # crypto conversion and external send.
    # Targets: students/unemployed/economically distressed (FINTRAC guidance)
    james = clients["james"].id

    # Minimal payroll (part-time barista, new account 45 days)
    for w in [4, 6, 8]:
        add(_txn(james, "deposit", "chequing", 1500.0, _dt(w * 7, 9),
                 source="Metro Coffee Chain", counterparty_name="Metro Coffee Chain"))

    # Minimal spending (establishing very thin baseline)
    for name, amt, d in [("Subway", 12.0, 55), ("Dollar Tree", 8.0, 40),
                          ("Shoppers", 22.0, 30), ("Tim Hortons", 6.50, 20),
                          ("Walmart", 35.0, 15)]:
        add(_txn(james, "withdrawal", "chequing", amt, _dt(d, 13),
                 destination=name, counterparty_name=name))

    # MULE PATTERN: 8 new senders within 7 days
    # Each sender sends a different small amount (avoids same-amount detection)
    # FINTRAC: "Client sending to, or receiving wire transfers from, multiple clients"
    mule_senders = [
        ("Alex H.", 480.0, 6, 10, 0), ("Maria K.", 650.0, 6, 14, 0),
        ("Tom B.", 520.0, 5, 9, 0), ("Yuki S.", 780.0, 5, 15, 0),
        ("Amir P.", 440.0, 4, 11, 0), ("Leila C.", 590.0, 4, 16, 0),
        ("Owen D.", 720.0, 3, 12, 0), ("Nina R.", 520.0, 3, 14, 30),
    ]
    for name, amt, days_ago, hour, minute in mule_senders:
        add(_txn(james, "e_transfer_in", "chequing", amt, _dt(days_ago, hour, minute),
                 source=f"Interac from {name}", counterparty_name=name,
                 metadata={"new_counterparty": True,
                            "fintrac_indicator": "mule_multiple_unrelated_senders"}))

    # RAPID CRYPTO CONVERSION: buy then external send within 3hrs
    add(_txn(james, "crypto_buy", "crypto", 3500.0, _dt(3, 13),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    add(_txn(james, "crypto_send", "crypto", 4200.0, _dt(3, 15),
             destination="0xf4e2a1b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4",
             counterparty_name="Anonymous Wallet",
             metadata={"asset": "USDT", "external_wallet": "0xf4e2a1b8...",
                        "hours_since_first_deposit": 5,
                        "fintrac_indicator": "rapid_conversion_mule_pattern"}))

    # REPEAT DEPOSITS from same senders (deepens mule pattern)
    add(_txn(james, "e_transfer_in", "chequing", 520.0, _dt(2, 10),
             source="Repeat", counterparty_name="Alex H."))
    add(_txn(james, "e_transfer_in", "chequing", 680.0, _dt(2, 14),
             source="Repeat", counterparty_name="Maria K."))
    add(_txn(james, "e_transfer_in", "chequing", 450.0, _dt(1, 11),
             source="Repeat", counterparty_name="Tom B."))

    # Second crypto send
    add(_txn(james, "crypto_buy", "crypto", 1500.0, _dt(1, 14),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    add(_txn(james, "crypto_send", "crypto", 1400.0, _dt(1, 16),
             destination="0xf4e2a1b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4",
             counterparty_name="Anonymous Wallet",
             metadata={"asset": "USDT", "external_wallet": "0xf4e2a1b8..."}))

    # ==========================================================================
    # 20. WEI ZHANG - Round-tripping (expected: L3, score ~0.82)
    # ==========================================================================
    # FINTRAC: "Transaction is unnecessarily complex for its stated purpose" +
    # "Transactions displaying financial connections between persons or entities
    # that are not usually connected." Funds leave via wire to Entity A,
    # return 14 days later from Entity B at similar amount (minus ~5% fee).
    # Pattern repeats. Entities have similar generic trade names.
    wei = clients["wei"].id

    for w in range(2, 14, 2):
        add(_txn(wei, "deposit", "chequing", 3125.0, _dt(w * 7, 9),
                 source="Pacific Rim Consulting", counterparty_name="Pacific Rim Consulting"))

    for d in [90, 60, 30, 3]:
        add(_txn(wei, "e_transfer_out", "chequing", 2200.0, _dt(d, 8),
                 destination="Pacific Heights Apartments",
                 counterparty_name="Pacific Heights Apartments"))

    for name, amt, d in [("T&T Supermarket", 180.0, 85), ("Petro-Canada", 65.0, 70),
                          ("Best Buy", 350.0, 55), ("LCBO", 48.0, 42),
                          ("Home Depot", 220.0, 28), ("Metro", 95.0, 15)]:
        add(_txn(wei, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    for d in [80, 50, 20]:
        add(_txn(wei, "withdrawal", "chequing", 95.0, _dt(d, 9),
                 destination="Telus", counterparty_name="Telus"))

    # ROUND-TRIPPING CYCLE 1: wire out $12K, return $11.4K from diff entity 14d later
    # ~5% shrinkage = laundering fee
    add(_txn(wei, "e_transfer_out", "chequing", 12000.0, _dt(55, 10),
             destination="Asia Pacific Trading Ltd",
             counterparty_name="Asia Pacific Trading Ltd",
             metadata={"wire_ref": "WIRE-OUT-001",
                        "fintrac_indicator": "round_trip_outbound"}))
    add(_txn(wei, "e_transfer_in", "chequing", 11400.0, _dt(41, 11),
             source="Pacific Commerce Group",
             counterparty_name="Pacific Commerce Group",
             metadata={"wire_ref": "WIRE-IN-001", "flagged": True,
                        "fintrac_indicator": "round_trip_return",
                        "note": "Similar amount (-5%), different entity, 14 day gap"}))

    # ROUND-TRIPPING CYCLE 2: same pattern, different entities
    add(_txn(wei, "e_transfer_out", "chequing", 15000.0, _dt(30, 10),
             destination="Orient Star Holdings",
             counterparty_name="Orient Star Holdings",
             metadata={"wire_ref": "WIRE-OUT-002",
                        "fintrac_indicator": "round_trip_outbound"}))
    add(_txn(wei, "e_transfer_in", "chequing", 14200.0, _dt(16, 14),
             source="Golden Dragon Enterprises",
             counterparty_name="Golden Dragon Enterprises",
             metadata={"wire_ref": "WIRE-IN-002", "flagged": True,
                        "fintrac_indicator": "round_trip_return",
                        "note": "Similar amount (-5.3%), different entity, 14 day gap"}))

    # ROUND-TRIPPING CYCLE 3: third repetition confirms pattern
    add(_txn(wei, "e_transfer_out", "chequing", 18000.0, _dt(12, 10),
             destination="Eastern Meridian Imports",
             counterparty_name="Eastern Meridian Imports",
             metadata={"wire_ref": "WIRE-OUT-003",
                        "fintrac_indicator": "round_trip_outbound",
                        "note": "Escalating amounts across cycles"}))

    # Crypto layering on top of round-tripping (adds complexity)
    add(_txn(wei, "crypto_buy", "crypto", 5000.0, _dt(8, 15),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(wei, "crypto_sell", "crypto", 4800.0, _dt(4, 11),
             source="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))

    # ==========================================================================
    # 21. AMARA DIALLO - Multi-hop layering (expected: L3, score ~0.94)
    # ==========================================================================
    # FINTRAC: "High volume and frequency of transfers between different types
    # of VCs" + "The VC flows through a large number of intermediate addresses
    # in a very short period." Student, $18K/yr income.
    # $15K unknown -> BTC -> ETH swap -> external wallet. All within 6 hours.
    # Income ratio: astronomical ($15K deposit vs $1,500/mo income).
    amara = clients["amara"].id

    for w in [2, 4, 6, 8]:
        add(_txn(amara, "deposit", "chequing", 750.0, _dt(w * 7, 9),
                 source="Campus Bookstore", counterparty_name="Campus Bookstore"))

    for d in [60, 30, 3]:
        add(_txn(amara, "e_transfer_out", "chequing", 650.0, _dt(d, 8),
                 destination="Student Housing Co-op",
                 counterparty_name="Student Housing Co-op"))

    for name, amt, d in [("University Bookstore", 180.0, 75), ("Amazon.ca", 145.0, 55),
                          ("Tim Hortons", 15.0, 50), ("Subway", 8.0, 40),
                          ("PRESTO", 128.0, 30), ("Dollarama", 12.0, 20)]:
        add(_txn(amara, "withdrawal", "chequing", amt, _dt(d, 12),
                 destination=name, counterparty_name=name))

    # MULTI-HOP LAYERING CYCLE 1: $15K unknown -> BTC -> ETH -> external (6hrs)
    add(_txn(amara, "e_transfer_in", "chequing", 15000.0, _dt(2, 9, 0),
             source="Unknown Sender", counterparty_name="Investment Opportunity Corp",
             metadata={"flagged": True, "new_counterparty": True,
                        "income_ratio": 10.0,
                        "fintrac_indicator": "income_inconsistency_extreme"}))
    add(_txn(amara, "crypto_buy", "crypto", 14500.0, _dt(2, 10, 0),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC", "hours_since_deposit": 1.0}))
    # BTC -> ETH swap (multi-hop adds layer)
    add(_txn(amara, "crypto_sell", "crypto", 14200.0, _dt(2, 12, 0),
             source="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC", "to_asset": "ETH",
                        "fintrac_indicator": "high_frequency_vc_conversion"}))
    add(_txn(amara, "crypto_buy", "crypto", 14200.0, _dt(2, 12, 5),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "ETH"}))
    # External send
    add(_txn(amara, "crypto_send", "crypto", 13800.0, _dt(2, 15, 0),
             destination="0xa1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
             counterparty_name="External Wallet",
             metadata={"asset": "ETH", "external_wallet": "0xa1b2c3d4...",
                        "hours_since_fiat_deposit": 6.0,
                        "fintrac_indicator": "multi_hop_layering"}))

    # LAYERING CYCLE 2 (smaller, next day)
    add(_txn(amara, "e_transfer_in", "chequing", 4000.0, _dt(1, 9, 0),
             source="Unknown Sender 2", counterparty_name="Quick Returns LLC",
             metadata={"flagged": True, "new_counterparty": True}))
    add(_txn(amara, "crypto_buy", "crypto", 3800.0, _dt(1, 10, 30),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(amara, "crypto_send", "crypto", 3600.0, _dt(1, 13, 0),
             destination="0xa1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xa1b2c3d4...",
                        "same_wallet_as_cycle_1": True}))

    # ==========================================================================
    # 22. ELENA PETROVA - Pig butchering VICTIM (expected: L3)
    # ==========================================================================
    # FINTRAC indicator: "Source of funds used for the purchase of large amounts
    # of VC is unknown." + "Transactions take place at the same time of day."
    #
    # PATTERN: Victim of pig butchering / romance-investment scam.
    # Long-established account (800 days), bookkeeper, stable baseline.
    # Over 8 weeks: escalating crypto purchases sent to SAME external wallet.
    # Small initial "test" investment, then growing amounts as scammer builds
    # confidence. Victim liquidates TFSA to fund later purchases.
    # Key tell: all sends go to same wallet, amounts escalate, timing is
    # similar (evenings after work), no crypto history before this period.
    elena = clients["elena"].id

    # Long-established baseline: 2+ years of steady payroll
    for w in range(1, 21, 2):
        add(_txn(elena, "deposit", "chequing", 2000.0, _dt(w * 7 + 14, 9),
                 source="Accurate Books & Tax", counterparty_name="Accurate Books & Tax",
                 metadata={"deposit_method": "direct_deposit"}))

    # Recent payroll (continuing into suspicious period)
    for w in range(1, 9, 2):
        add(_txn(elena, "deposit", "chequing", 2000.0, _dt(w * 7, 9),
                 source="Accurate Books & Tax", counterparty_name="Accurate Books & Tax"))

    # Stable rent (years of history)
    for d in [120, 90, 60, 30, 3]:
        add(_txn(elena, "withdrawal", "chequing", 1350.0, _dt(d, 14),
                 destination="Bayview Manor", counterparty_name="Bayview Manor"))

    # Stable bills
    for d in [110, 80, 50, 20]:
        add(_txn(elena, "withdrawal", "chequing", 95.0, _dt(d, 14),
                 destination="Toronto Hydro", counterparty_name="Toronto Hydro"))
    for d in [105, 75, 45, 15]:
        add(_txn(elena, "withdrawal", "chequing", 55.0, _dt(d, 14),
                 destination="Koodo Mobile", counterparty_name="Koodo Mobile"))

    # Stable groceries
    for d in [115, 100, 85, 70, 55, 40, 25, 10]:
        add(_txn(elena, "withdrawal", "chequing", 95.0 + d % 25, _dt(d, 11),
                 destination="Loblaws", counterparty_name="Loblaws"))

    # Regular TFSA contributions (established saver)
    for d in [110, 80, 50]:
        add(_txn(elena, "deposit", "tfsa", 400.0, _dt(d, 11),
                 counterparty_name="Self Transfer"))

    # Pharmacy (regular, reinforces stable lifestyle)
    for d in [100, 65, 30]:
        add(_txn(elena, "withdrawal", "chequing", 48.0, _dt(d, 10),
                 destination="Rexall Pharmacy", counterparty_name="Rexall Pharmacy"))

    # ---- PIG BUTCHERING ESCALATION ----
    # Week 1: Small "test" investment ($500) - scammer shows fake profits
    add(_txn(elena, "crypto_buy", "crypto", 500.0, _dt(42, 19, 30),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC", "first_crypto_ever": True,
                        "fintrac_indicator": "new_product_usage",
                        "note": "First crypto purchase EVER after 800 days. Evening timing."}))
    add(_txn(elena, "crypto_send", "crypto", 480.0, _dt(42, 20, 0),
             destination="0xbb1122cc3344dd5566ee7788ff99aa00bb11cc22",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC",
                        "external_wallet": "0xbb1122cc...",
                        "note": "Pig butchering - initial small test send"}))

    # Week 2: Encouraged by fake profits, sends $1,500
    add(_txn(elena, "crypto_buy", "crypto", 1500.0, _dt(35, 19, 15),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(elena, "crypto_send", "crypto", 1450.0, _dt(35, 19, 45),
             destination="0xbb1122cc3344dd5566ee7788ff99aa00bb11cc22",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xbb1122cc...",
                        "same_wallet_as_previous": True}))

    # Week 3: $3,000 - escalating
    add(_txn(elena, "crypto_buy", "crypto", 3000.0, _dt(28, 19, 0),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(elena, "crypto_send", "crypto", 2900.0, _dt(28, 19, 30),
             destination="0xbb1122cc3344dd5566ee7788ff99aa00bb11cc22",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xbb1122cc..."}))

    # Week 4: $5,000 - significant for her income level
    add(_txn(elena, "crypto_buy", "crypto", 5000.0, _dt(21, 18, 45),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(elena, "crypto_send", "crypto", 4900.0, _dt(21, 19, 15),
             destination="0xbb1122cc3344dd5566ee7788ff99aa00bb11cc22",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xbb1122cc..."}))

    # Week 5: $8,000 - scammer pushes for bigger "investment"
    add(_txn(elena, "crypto_buy", "crypto", 8000.0, _dt(14, 19, 0),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC",
                        "fintrac_indicator": "escalating_amounts"}))
    add(_txn(elena, "crypto_send", "crypto", 7800.0, _dt(14, 19, 30),
             destination="0xbb1122cc3344dd5566ee7788ff99aa00bb11cc22",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xbb1122cc..."}))

    # Week 6: TFSA liquidation to fund more investment - draining savings
    add(_txn(elena, "withdrawal", "tfsa", 6500.0, _dt(8, 10),
             destination="Self - Chequing", counterparty_name="Self Transfer",
             metadata={"note": "TFSA liquidation - victim draining savings",
                        "fintrac_indicator": "unusual_product_liquidation"}))
    add(_txn(elena, "crypto_buy", "crypto", 6500.0, _dt(7, 19, 0),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC", "funded_by": "TFSA_liquidation"}))
    add(_txn(elena, "crypto_send", "crypto", 6300.0, _dt(7, 19, 30),
             destination="0xbb1122cc3344dd5566ee7788ff99aa00bb11cc22",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xbb1122cc..."}))

    # Week 7: Scammer demands urgency - "opportunity closing"
    add(_txn(elena, "crypto_buy", "crypto", 10000.0, _dt(3, 18, 30),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC",
                        "note": "Largest purchase yet. Account nearly depleted."}))
    add(_txn(elena, "crypto_send", "crypto", 9800.0, _dt(3, 19, 0),
             destination="0xbb1122cc3344dd5566ee7788ff99aa00bb11cc22",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xbb1122cc...",
                        "fintrac_indicator": "repeated_sends_same_external_wallet",
                        "total_sent_to_this_wallet": 34630.0,
                        "note": "7 sends to identical wallet over 6 weeks. Clear pig butchering pattern."}))

    # ==========================================================================
    # 23. KWAME ASANTE - Smurfing funnel account (expected: L3)
    # ==========================================================================
    # FINTRAC: "Client sending to, or receiving wire transfers from, multiple
    # clients" + structuring. Funnel account receives many small deposits
    # from many different people, consolidates, and sends bulk crypto out.
    # This is the collection side of a money mule network.
    kwame = clients["kwame"].id

    for w in range(2, 10, 2):
        add(_txn(kwame, "deposit", "chequing", 1333.0, _dt(w * 7, 9),
                 source="Skip The Dishes", counterparty_name="Skip The Dishes"))

    for d in [60, 30, 3]:
        add(_txn(kwame, "e_transfer_out", "chequing", 900.0, _dt(d, 8),
                 destination="Scarborough Rooms", counterparty_name="Scarborough Rooms"))

    for name, amt, d in [("McDonalds", 11.0, 55), ("Walmart", 45.0, 38),
                          ("Shoppers", 18.0, 22)]:
        add(_txn(kwame, "withdrawal", "chequing", amt, _dt(d, 13),
                 destination=name, counterparty_name=name))
    add(_txn(kwame, "withdrawal", "chequing", 35.0, _dt(45, 9),
             destination="Chatr Mobile", counterparty_name="Chatr Mobile"))

    # SMURFING: 15 small deposits from 12 different people over 10 days
    # Each under $1,000 (avoids individual attention), but volume is obvious
    smurfs = [
        ("Janet P.", 350.0, 9, 10), ("Robert K.", 420.0, 9, 14),
        ("Linda M.", 380.0, 8, 9), ("Chris W.", 550.0, 8, 13),
        ("David R.", 475.0, 7, 11), ("Sarah L.", 320.0, 7, 15),
        ("Michael T.", 600.0, 6, 10), ("Emma J.", 390.0, 6, 14),
        ("Janet P.", 280.0, 5, 12),  # repeat sender
        ("Robert K.", 510.0, 5, 16),  # repeat sender
        ("Aisha B.", 440.0, 4, 10), ("Diego F.", 370.0, 4, 14),
        ("Mei L.", 520.0, 3, 11), ("Hannah S.", 290.0, 3, 15),
        ("Chris W.", 480.0, 2, 10),  # repeat sender
    ]
    for name, amt, d, h in smurfs:
        add(_txn(kwame, "e_transfer_in", "chequing", amt, _dt(d, h),
                 source=f"Interac from {name}", counterparty_name=name,
                 metadata={"new_counterparty": True,
                            "fintrac_indicator": "smurfing_many_small_deposits",
                            "note": "Part of smurfing funnel collection"}))

    # CONSOLIDATION: Crypto buy and bulk external send to cluster wallet
    add(_txn(kwame, "crypto_buy", "crypto", 5000.0, _dt(1.5, 10),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    add(_txn(kwame, "crypto_send", "crypto", 4800.0, _dt(1, 14),
             destination=WALLET_CLUSTER_3,
             counterparty_name="Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x5c2d9a3b...",
                        "fintrac_indicator": "funnel_consolidation_to_crypto"}))
    # Second batch
    add(_txn(kwame, "crypto_buy", "crypto", 2000.0, _dt(0.5, 11),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    add(_txn(kwame, "crypto_send", "crypto", 1800.0, _dt(0.3, 15),
             destination=WALLET_CLUSTER_3,
             counterparty_name="Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x5c2d9a3b..."}))

    # ==========================================================================
    # 24. TARIQ AL-RASHIDI - Trade-based ML (expected: L3)
    # ==========================================================================
    # FINTRAC: "Transaction is unnecessarily complex for its stated purpose" +
    # "Transactions with jurisdictions known to be at a higher risk of ML/TF" +
    # shell company indicators. Trade consultant receiving wire payments that
    # don't match invoice patterns. Over-invoicing: goods worth $5K billed as $20K.
    # Payments routed through UAE, with crypto conversion layer.
    tariq = clients["tariq"].id

    for w in range(1, 13, 2):
        add(_txn(tariq, "deposit", "chequing", 3958.0, _dt(w * 7 + 30, 9),
                 source="Al-Rashidi Trade Consulting", counterparty_name="Al-Rashidi Trade Consulting",
                 metadata={"deposit_method": "business_income"}))

    for d in [120, 90, 60, 30, 3]:
        add(_txn(tariq, "e_transfer_out", "chequing", 2800.0, _dt(d, 8),
                 destination="York Mills Residences", counterparty_name="York Mills Residences"))

    # Normal business spending
    for name, amt, d in [("Air Canada", 1200.0, 95), ("Marriott Hotels", 680.0, 92),
                          ("Air Canada", 850.0, 70), ("Hilton Hotels", 520.0, 68),
                          ("WestJet", 450.0, 45), ("Delta Hotels", 380.0, 42)]:
        add(_txn(tariq, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name,
                 metadata={"category": "business_travel"}))

    # Normal personal spending
    for d in [100, 80, 60, 40, 20]:
        add(_txn(tariq, "withdrawal", "chequing", 220.0 + d % 50, _dt(d, 12),
                 destination="Whole Foods Market", counterparty_name="Whole Foods Market"))
    for d in [85, 55, 25]:
        add(_txn(tariq, "withdrawal", "chequing", 120.0, _dt(d, 14),
                 destination="Rogers Wireless", counterparty_name="Rogers Wireless"))

    # TRADE-BASED ML: Suspicious wire payments that suggest over/under invoicing
    # Wire in from UAE entity - stated as "consulting services" but amounts
    # far exceed normal consulting fees and come from multiple generic entities
    add(_txn(tariq, "deposit", "chequing", 45000.0, _dt(18, 9),
             source="Wire Transfer", counterparty_name="Gulf Star Trading FZE",
             metadata={"wire_ref": "WIRE-GULF-001", "originating_country": "AE",
                        "flagged": True,
                        "fintrac_indicator": "trade_based_ml_over_invoicing",
                        "note": "Dubai FZE company. Amount inconsistent with consulting."}))
    add(_txn(tariq, "deposit", "chequing", 32000.0, _dt(10, 14),
             source="Wire Transfer", counterparty_name="Arabian Peninsula Commodities",
             metadata={"wire_ref": "WIRE-ARAB-002", "originating_country": "AE",
                        "flagged": True,
                        "fintrac_indicator": "trade_based_ml_over_invoicing",
                        "note": "Second UAE entity, similar pattern."}))

    # Rapid outflows after suspicious inflows - splits and layers
    add(_txn(tariq, "e_transfer_out", "chequing", 20000.0, _dt(17, 10),
             destination="Meridian Import Group", counterparty_name="Meridian Import Group",
             metadata={"fintrac_indicator": "rapid_outflow_after_suspicious_inflow"}))
    add(_txn(tariq, "crypto_buy", "crypto", 15000.0, _dt(16, 14),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    add(_txn(tariq, "crypto_send", "crypto", 14500.0, _dt(15, 10),
             destination="0xee11ff22aa33bb44cc55dd66ee77ff88aa99bb00",
             counterparty_name="External Wallet",
             metadata={"asset": "USDT", "external_wallet": "0xee11ff22...",
                        "fintrac_indicator": "layering_after_trade_based_ml"}))

    # Second wire cycle
    add(_txn(tariq, "e_transfer_out", "chequing", 18000.0, _dt(9, 11),
             destination="Silk Route Ventures", counterparty_name="Silk Route Ventures",
             metadata={"fintrac_indicator": "suspected_shell_entity"}))
    add(_txn(tariq, "crypto_buy", "crypto", 10000.0, _dt(8, 15),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(tariq, "crypto_send", "crypto", 9500.0, _dt(7, 10),
             destination="0xee11ff22aa33bb44cc55dd66ee77ff88aa99bb00",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xee11ff22..."}))

    # ==========================================================================
    # 25. NADIA IVANOVA - Dormant account reactivation (expected: L3)
    # ==========================================================================
    # FINTRAC: "There is a sudden change in the client's financial profile,
    # pattern of activity or transactions."
    # 2-year-old account was active for 6 months, then dormant for 18 months.
    # Suddenly reactivated with large deposits and crypto sends.
    nadia = clients["nadia"].id

    # HISTORICAL: Active period 2+ years ago (small, normal transactions)
    for d in [720, 700, 680, 660, 640, 620, 600, 580]:
        add(_txn(nadia, "deposit", "chequing", 1833.0, _dt(d, 9),
                 source="Creative Studio Inc", counterparty_name="Creative Studio Inc"))
    for d in [715, 685, 655, 625]:
        add(_txn(nadia, "withdrawal", "chequing", 1200.0, _dt(d, 14),
                 destination="Old Landlord", counterparty_name="Old Landlord"))

    # DORMANT PERIOD: Almost nothing for ~18 months (560 to 30 days ago)
    # Only occasional small transaction
    add(_txn(nadia, "withdrawal", "chequing", 25.0, _dt(400, 14),
             destination="Tim Hortons", counterparty_name="Tim Hortons"))
    add(_txn(nadia, "withdrawal", "chequing", 15.0, _dt(250, 12),
             destination="Dollar Tree", counterparty_name="Dollar Tree"))

    # REACTIVATION BURST: Sudden heavy activity
    add(_txn(nadia, "deposit", "chequing", 8000.0, _dt(7, 10),
             source="Unknown sender", counterparty_name="Digital Commerce Group",
             metadata={"new_counterparty": True, "account_was_dormant": True,
                        "fintrac_indicator": "dormant_account_reactivation"}))
    add(_txn(nadia, "deposit", "chequing", 6500.0, _dt(5, 14),
             source="Unknown sender", counterparty_name="Tech Solutions Unlimited",
             metadata={"new_counterparty": True,
                        "fintrac_indicator": "dormant_account_reactivation"}))
    add(_txn(nadia, "deposit", "chequing", 9200.0, _dt(3, 11),
             source="Unknown sender", counterparty_name="Global Digital Services",
             metadata={"new_counterparty": True,
                        "fintrac_indicator": "dormant_account_reactivation_structuring"}))

    # Rapid crypto conversion
    add(_txn(nadia, "crypto_buy", "crypto", 12000.0, _dt(2, 10),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT", "first_crypto_usage": True}))
    add(_txn(nadia, "crypto_send", "crypto", 11500.0, _dt(2, 14),
             destination="0xdd44ee55ff66aa77bb88cc99dd00ee11ff22aa33",
             counterparty_name="External Wallet",
             metadata={"asset": "USDT", "external_wallet": "0xdd44ee55...",
                        "fintrac_indicator": "dormant_to_active_crypto_exit"}))
    add(_txn(nadia, "crypto_buy", "crypto", 8000.0, _dt(1, 10),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(nadia, "crypto_send", "crypto", 7500.0, _dt(0.5, 15),
             destination="0xdd44ee55ff66aa77bb88cc99dd00ee11ff22aa33",
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0xdd44ee55..."}))

    # ==========================================================================
    # 26. RACHEL CHEN - Romance scam VICTIM (expected: L3)
    # ==========================================================================
    # FINTRAC: "Client presents confusing details about the transaction" +
    # "Insufficient explanation for source of funds."
    # Elderly retired librarian (70 years old), 5+ year account, pension-based
    # income. Suddenly sending large e-transfers to someone she's never
    # transacted with before. Escalating pattern over weeks. Draining savings.
    # Unlike pig butchering, this is direct e-transfer to "partner" not crypto.
    rachel = clients["rachel"].id

    # Very stable pension-based baseline (years of history)
    for m in range(14):
        add(_txn(rachel, "deposit", "chequing", 1583.0, _dt(m * 30 + 5, 9),
                 source="BC Teachers Pension Plan",
                 counterparty_name="BC Teachers Pension Plan",
                 metadata={"deposit_method": "direct_deposit"}))

    # Extremely stable spending (same stores for years)
    for d in [120, 90, 60, 30, 3]:
        add(_txn(rachel, "withdrawal", "chequing", 1250.0, _dt(d, 14),
                 destination="Victoria Gardens Apartments",
                 counterparty_name="Victoria Gardens Apartments"))

    for d in [115, 95, 75, 55, 35, 15]:
        add(_txn(rachel, "withdrawal", "chequing", 75.0 + d % 20, _dt(d, 10),
                 destination="Save-On-Foods", counterparty_name="Save-On-Foods"))

    for d in [110, 80, 50, 20]:
        add(_txn(rachel, "withdrawal", "chequing", 42.0, _dt(d, 10),
                 destination="London Drugs", counterparty_name="London Drugs"))
    for d in [105, 75, 45, 15]:
        add(_txn(rachel, "withdrawal", "chequing", 55.0, _dt(d, 14),
                 destination="BC Hydro", counterparty_name="BC Hydro"))
    for d in [100, 70, 40, 10]:
        add(_txn(rachel, "withdrawal", "chequing", 35.0, _dt(d, 14),
                 destination="Telus", counterparty_name="Telus"))

    # TFSA (regular small saver)
    for d in [95, 65, 35]:
        add(_txn(rachel, "deposit", "tfsa", 250.0, _dt(d, 11),
                 counterparty_name="Self Transfer"))

    # Library book purchases (character detail)
    for d in [108, 72, 36]:
        add(_txn(rachel, "withdrawal", "chequing", 22.0, _dt(d, 14),
                 destination="Indigo Books", counterparty_name="Indigo Books"))

    # ---- ROMANCE SCAM ESCALATION ----
    # Sends to "Michael Davies" - someone she's never transacted with
    # Week 1: Small amount - "I need help with an emergency"
    add(_txn(rachel, "e_transfer_out", "chequing", 500.0, _dt(28, 11),
             destination="Michael Davies", counterparty_name="Michael Davies",
             metadata={"new_counterparty": True,
                        "fintrac_indicator": "elderly_new_counterparty",
                        "note": "First ever transfer to this person. 70yo pensioner."}))

    # Week 2: $1,500 - "medical bills overseas"
    add(_txn(rachel, "e_transfer_out", "chequing", 1500.0, _dt(21, 14),
             destination="Michael Davies", counterparty_name="Michael Davies",
             metadata={"note": "Escalating - same recipient"}))

    # Week 3: $3,000 - "customs fees to ship belongings"
    add(_txn(rachel, "e_transfer_out", "chequing", 3000.0, _dt(14, 11),
             destination="Michael Davies", counterparty_name="Michael Davies",
             metadata={"note": "Significant for pension income"}))

    # Week 4: $4,000 - "flight tickets to come visit"
    add(_txn(rachel, "e_transfer_out", "chequing", 4000.0, _dt(7, 15),
             destination="Michael Davies", counterparty_name="Michael Davies",
             metadata={"fintrac_indicator": "escalating_transfers_to_single_new_cp",
                        "note": "Monthly pension is $1,583. Sent $4K in single transfer."}))

    # TFSA liquidation to fund more transfers
    add(_txn(rachel, "withdrawal", "tfsa", 5000.0, _dt(4, 10),
             destination="Self - Chequing", counterparty_name="Self Transfer",
             metadata={"fintrac_indicator": "savings_liquidation_for_unknown_recipient"}))

    # Week 5: $5,000 - "investment opportunity, will pay you back double"
    add(_txn(rachel, "e_transfer_out", "chequing", 5000.0, _dt(2, 11),
             destination="Michael Davies", counterparty_name="Michael Davies",
             metadata={"fintrac_indicator": "romance_scam_pattern",
                        "total_sent_to_recipient": 14000.0,
                        "note": "5 transfers totaling $14K to single new CP over 4 weeks. "
                                "70yo pensioner liquidating savings. Classic romance scam victim pattern."}))

    # ==========================================================================
    # 27. VIKTOR PETROV - Extreme patterns (expected: near-L4, score ~0.95)
    # ==========================================================================
    # FINTRAC: Multiple simultaneous indicators at extreme levels.
    # Wire deposits from 3 different shell companies in high-risk jurisdictions.
    # Immediate crypto conversion. Sends to 3 DIFFERENT external wallets
    # (splitting to avoid single-wallet detection). Income ratio ~14x.
    viktor = clients["viktor"].id

    for w in [4, 8, 12]:
        add(_txn(viktor, "deposit", "chequing", 1875.0, _dt(w * 7, 9),
                 source="Eastern European Imports",
                 counterparty_name="Eastern European Imports"))

    for name, amt, d in [("Walmart", 85.0, 90), ("Petro-Canada", 60.0, 70),
                          ("No Frills", 95.0, 50), ("Tim Hortons", 12.0, 35),
                          ("Shoppers", 42.0, 20)]:
        add(_txn(viktor, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))

    add(_txn(viktor, "e_transfer_out", "chequing", 1200.0, _dt(60, 8),
             destination="Scarborough Apartments",
             counterparty_name="Scarborough Apartments"))
    add(_txn(viktor, "e_transfer_out", "chequing", 1200.0, _dt(30, 8),
             destination="Scarborough Apartments",
             counterparty_name="Scarborough Apartments"))
    add(_txn(viktor, "withdrawal", "chequing", 50.0, _dt(40, 9),
             destination="Chatr", counterparty_name="Chatr"))

    # EXTREME: 3 massive wire deposits from shell companies
    add(_txn(viktor, "deposit", "chequing", 25000.0, _dt(6, 9),
             source="Wire Transfer", counterparty_name="Baltic Shipping Consolidated",
             metadata={"flagged": True, "wire_ref": "WIRE-BALTIC-001",
                        "originating_country": "LV",  # Latvia
                        "fintrac_indicator": "large_wire_high_risk_jurisdiction"}))
    add(_txn(viktor, "deposit", "chequing", 18000.0, _dt(4, 11),
             source="Wire Transfer", counterparty_name="Eurasian Trade Holdings",
             metadata={"flagged": True, "wire_ref": "WIRE-EURAS-002",
                        "originating_country": "CY",  # Cyprus - secrecy jurisdiction
                        "fintrac_indicator": "large_wire_high_risk_jurisdiction"}))
    add(_txn(viktor, "deposit", "chequing", 22000.0, _dt(2, 14),
             source="Wire Transfer", counterparty_name="North Sea Commodities Ltd",
             metadata={"flagged": True, "wire_ref": "WIRE-NSEA-003",
                        "originating_country": "MT",  # Malta
                        "fintrac_indicator": "large_wire_multiple_jurisdictions"}))

    # Immediate crypto conversion (within hours of each deposit)
    add(_txn(viktor, "crypto_buy", "crypto", 24000.0, _dt(5.5, 15),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC", "hours_since_wire": 6}))
    add(_txn(viktor, "crypto_buy", "crypto", 17000.0, _dt(3.5, 16),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "ETH", "hours_since_wire": 5}))
    add(_txn(viktor, "crypto_buy", "crypto", 21000.0, _dt(1.5, 10),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT", "hours_since_wire": 4}))

    # Sends to 3 DIFFERENT external wallets (splitting for obfuscation)
    add(_txn(viktor, "crypto_send", "crypto", 23500.0, _dt(5, 18),
             destination="0xc1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9",
             counterparty_name="External Wallet 1",
             metadata={"asset": "BTC", "external_wallet": "0xc1d2e3f4...",
                        "fintrac_indicator": "multiple_wallet_splitting"}))
    add(_txn(viktor, "crypto_send", "crypto", 16500.0, _dt(3, 19),
             destination="0xe5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3",
             counterparty_name="External Wallet 2",
             metadata={"asset": "ETH", "external_wallet": "0xe5f6a7b8..."}))
    add(_txn(viktor, "crypto_send", "crypto", 20500.0, _dt(1, 14),
             destination="0xf7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5",
             counterparty_name="External Wallet 3",
             metadata={"asset": "USDT", "external_wallet": "0xf7a8b9c0...",
                        "total_sent_external": 60500.0,
                        "income_ratio": 14.2}))

    # ==========================================================================
    # 28. CHEN WEI LI - Account takeover (expected: near-L4, score ~0.95)
    # ==========================================================================
    # FINTRAC: "There is a sudden change in the client's financial profile."
    # 5-year account, retired teacher, pension + pharmacy + groceries.
    # Suddenly: new device, new IP, transfers to unknowns, first-ever crypto.
    # Extreme behavioral deviation from very deep baseline.
    chen = clients["chen"].id

    # Very deep pension baseline (years of data)
    for m in range(14):
        add(_txn(chen, "deposit", "chequing", 2167.0, _dt(m * 30 + 5, 9),
                 source="Ontario Teachers Pension Plan",
                 counterparty_name="Ontario Teachers Pension Plan",
                 metadata={"deposit_method": "direct_deposit",
                            "device": "iPad-Air-4", "geo": "Toronto, ON"}))

    # Pharmacy (regular, years of history)
    for d in [120, 90, 60, 30, 15]:
        add(_txn(chen, "withdrawal", "chequing", 85.0, _dt(d, 10),
                 destination="Rexall Pharmacy", counterparty_name="Rexall Pharmacy",
                 metadata={"geo": "Toronto, ON"}))

    # Groceries (same store, same day pattern)
    for d in [115, 95, 75, 55, 35, 15]:
        add(_txn(chen, "withdrawal", "chequing", 95.0 + d % 15, _dt(d, 11),
                 destination="T&T Supermarket", counterparty_name="T&T Supermarket",
                 metadata={"geo": "Toronto, ON"}))

    # TFSA (steady)
    for d in [100, 70, 40]:
        add(_txn(chen, "deposit", "tfsa", 500.0, _dt(d, 14),
                 counterparty_name="Self Transfer"))

    # Utilities (years of stable payments)
    for d in [110, 80, 50, 20]:
        add(_txn(chen, "withdrawal", "chequing", 65.0, _dt(d, 14),
                 destination="Toronto Hydro", counterparty_name="Toronto Hydro"))
    for d in [105, 75, 45, 15]:
        add(_txn(chen, "withdrawal", "chequing", 50.0, _dt(d, 14),
                 destination="Enbridge Gas", counterparty_name="Enbridge Gas"))

    # Tim Hortons (creature of habit)
    for d in [108, 88, 68, 48, 28, 8]:
        add(_txn(chen, "withdrawal", "chequing", 4.50, _dt(d, 8, 30),
                 destination="Tim Hortons", counterparty_name="Tim Hortons",
                 metadata={"geo": "Toronto, ON"}))

    # ACCOUNT TAKEOVER: Sudden device change + behavioral explosion
    add(_txn(chen, "e_transfer_out", "chequing", 4000.0, _dt(2, 11),
             destination="Unknown Recipient", counterparty_name="Jason R.",
             metadata={"new_device": True, "device": "Android-Unknown",
                        "ip": "185.220.101.xx", "geo": "Unknown",
                        "new_counterparty": True,
                        "fintrac_indicator": "account_takeover_device_change"}))
    add(_txn(chen, "e_transfer_out", "chequing", 4000.0, _dt(2, 14),
             destination="Unknown Recipient 2", counterparty_name="Nicole P.",
             metadata={"new_device": True, "device": "Android-Unknown",
                        "new_counterparty": True}))
    add(_txn(chen, "e_transfer_out", "chequing", 4000.0, _dt(1, 9),
             destination="Unknown Recipient 3", counterparty_name="Brandon K.",
             metadata={"new_device": True, "device": "Android-Unknown",
                        "new_counterparty": True}))
    # First-ever crypto purchase (67 year old retiree)
    add(_txn(chen, "crypto_buy", "crypto", 8000.0, _dt(1, 15),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC", "first_crypto_ever": True,
                        "device": "Android-Unknown",
                        "fintrac_indicator": "account_takeover_new_product",
                        "note": "67yo retiree buys crypto for first time from unknown device"}))

    # ==========================================================================
    # 29. YUKI TANAKA - Cluster 2 participant (expected: L3, score ~0.85)
    # ==========================================================================
    yuki = clients["yuki"].id

    for name, d in [("Wedding Photo Co", 80), ("Portrait Studio", 65),
                     ("Event Planners Inc", 50), ("Magazine Weekly", 35),
                     ("Wedding Photo Co", 20), ("Portrait Studio", 8)]:
        add(_txn(yuki, "e_transfer_in", "chequing", 1500.0 + (d * 13 % 1000), _dt(d, 10),
                 source=name, counterparty_name=name))

    for d in [75, 45, 15, 3]:
        add(_txn(yuki, "e_transfer_out", "chequing", 1300.0, _dt(d, 8),
                 destination="Kensington Market Lofts",
                 counterparty_name="Kensington Market Lofts"))

    for name, amt, d in [("Henry's Photo", 320.0, 70), ("Amazon.ca", 85.0, 55),
                          ("Uber", 22.0, 40), ("Metro", 110.0, 25),
                          ("Starbucks", 7.50, 12)]:
        add(_txn(yuki, "withdrawal", "chequing", amt, _dt(d, 14),
                 destination=name, counterparty_name=name))
    add(_txn(yuki, "withdrawal", "chequing", 55.0, _dt(60, 9),
             destination="Koodo", counterparty_name="Koodo"))

    # COORDINATED: 3 new senders within 7 days
    add(_txn(yuki, "e_transfer_in", "chequing", 1800.0, _dt(6, 11),
             source="New sender 1", counterparty_name="Ravi M.",
             metadata={"new_counterparty": True, "cluster": "0x8b4f"}))
    add(_txn(yuki, "e_transfer_in", "chequing", 2500.0, _dt(4, 14),
             source="New sender 2", counterparty_name="Andrea S.",
             metadata={"new_counterparty": True, "cluster": "0x8b4f"}))
    add(_txn(yuki, "e_transfer_in", "chequing", 1500.0, _dt(2, 10),
             source="New sender 3", counterparty_name="Kofi A.",
             metadata={"new_counterparty": True, "cluster": "0x8b4f"}))

    add(_txn(yuki, "crypto_buy", "crypto", 5500.0, _dt(1.5, 15),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "BTC"}))
    add(_txn(yuki, "crypto_send", "crypto", 5800.0, _dt(1, 11),
             destination=WALLET_CLUSTER_2,
             counterparty_name="External Wallet",
             metadata={"asset": "BTC", "external_wallet": "0x8b4f2a1c...",
                        "same_wallet_as": "Marcus Webb",
                        "fintrac_indicator": "coordinated_crypto_consolidation"}))

    # ==========================================================================
    # 30. KOFI MENSAH - Cluster 3 participant (expected: L3)
    # ==========================================================================
    # Second node in smurfing network with Kwame Asante.
    # Same pattern: many small deposits, crypto consolidation to same wallet.
    kofi = clients["kofi"].id

    for w in range(2, 10, 2):
        add(_txn(kofi, "deposit", "chequing", 1250.0, _dt(w * 7, 9),
                 source="Uber Technologies", counterparty_name="Uber Technologies"))

    for d in [60, 30, 3]:
        add(_txn(kofi, "e_transfer_out", "chequing", 850.0, _dt(d, 8),
                 destination="Jane-Finch Rooms", counterparty_name="Jane-Finch Rooms"))

    for name, amt, d in [("Popeyes", 14.0, 55), ("Dollar Tree", 8.0, 38),
                          ("No Frills", 65.0, 22), ("Tim Hortons", 6.50, 10)]:
        add(_txn(kofi, "withdrawal", "chequing", amt, _dt(d, 13),
                 destination=name, counterparty_name=name))

    # SMURFING: 10 small deposits from 8 different people (overlapping timing with Kwame)
    kofi_smurfs = [
        ("Hannah S.", 420.0, 9, 11), ("Mei L.", 380.0, 9, 15),
        ("Diego F.", 510.0, 8, 10), ("Aisha B.", 340.0, 8, 14),
        ("Trevor N.", 450.0, 7, 12), ("Lisa Q.", 390.0, 7, 16),
        ("Hannah S.", 280.0, 6, 11),  # repeat
        ("Trevor N.", 520.0, 5, 10),  # repeat
        ("Janet P.", 410.0, 4, 14),   # same sender as Kwame's network!
        ("Chris W.", 360.0, 3, 11),   # same sender as Kwame's network!
    ]
    for name, amt, d, h in kofi_smurfs:
        add(_txn(kofi, "e_transfer_in", "chequing", amt, _dt(d, h),
                 source=f"Interac from {name}", counterparty_name=name,
                 metadata={"new_counterparty": True,
                            "fintrac_indicator": "smurfing_funnel_collection",
                            "shared_senders_with": "Kwame Asante" if name in ["Janet P.", "Chris W."] else None}))

    # Crypto consolidation to SAME wallet as Kwame
    add(_txn(kofi, "crypto_buy", "crypto", 3500.0, _dt(2, 10),
             destination="Wealthsimple Crypto", counterparty_name="Wealthsimple Crypto",
             metadata={"asset": "USDT"}))
    add(_txn(kofi, "crypto_send", "crypto", 3300.0, _dt(1.5, 14),
             destination=WALLET_CLUSTER_3,
             counterparty_name="Consolidation Wallet",
             metadata={"asset": "USDT", "external_wallet": "0x5c2d9a3b...",
                        "same_wallet_as": "Kwame Asante",
                        "fintrac_indicator": "coordinated_smurfing_network"}))

    # ======================================================================
    # BULK ADD
    # ======================================================================
    for t in txns:
        db.add(t)
    db.flush()

    print(f"  Total transactions created: {len(txns)}")


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

    # Print summary
    tiers = {
        "L0 Auto-Resolve": ["alice", "henry", "natasha", "raj", "maria"],
        "L1 Monitor": ["david", "lisa", "omar"],
        "L2 Guardrail": ["isabel", "frank", "priya", "marcus", "sophie"],
        "L3 Investigation": ["bob", "carl", "dana", "eve", "grace", "james",
                              "wei", "amara", "elena", "kwame", "tariq", "nadia", "rachel"],
        "Near-L4 Extreme": ["viktor", "chen"],
        "Cluster Members": ["yuki", "kofi"],
    }
    for tier, names in tiers.items():
        print(f"\n  {tier}:")
        for name in names:
            if name in clients:
                c = clients[name]
                print(f"    {c.name:22} | income ${c.stated_income:>8,.0f}/yr | "
                      f"KYC: {c.kyc_level:8} | {len(c.products_held)} products")
            else:
                # Try alternate key formats
                for key, c in clients.items():
                    if key.startswith(name):
                        print(f"    {c.name:22} | income ${c.stated_income:>8,.0f}/yr | "
                              f"KYC: {c.kyc_level:8} | {len(c.products_held)} products")
                        break


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()