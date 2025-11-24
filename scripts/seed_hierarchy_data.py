#!/usr/bin/env python3
"""
Seed Hierarchy Data

Populates the database with test organizations, projects, domains, and users
for development and testing.
"""

import sqlite3
import uuid

DATABASE_PATH = "/app/data/foundry.db"


def seed_data():
    """Seed the database with test data"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Organizations
    org_id_acme = str(uuid.uuid4())
    org_id_demo = str(uuid.uuid4())

    cursor.execute(
        "INSERT OR IGNORE INTO organizations (id, name, tier) VALUES (?, ?, ?)",
        (org_id_acme, "Acme Corporation", "enterprise"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO organizations (id, name, tier) VALUES (?, ?, ?)",
        (org_id_demo, "Demo Organization", "standard"),
    )

    # Projects for Acme Corp
    project_id_banking = str(uuid.uuid4())
    project_id_crm = str(uuid.uuid4())

    cursor.execute(
        """
        INSERT OR IGNORE INTO projects (id, organization_id, name, display_name, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            project_id_banking,
            org_id_acme,
            "banking",
            "Banking Platform",
            "Core banking services and customer management",
        ),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO projects (id, organization_id, name, display_name, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (project_id_crm, org_id_acme, "crm", "Customer Relationship Management", "Sales and customer support platform"),
    )

    # Projects for Demo Org
    project_id_demo = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT OR IGNORE INTO projects (id, organization_id, name, display_name, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (project_id_demo, org_id_demo, "demo", "Demo Project", "Sample project for testing"),
    )

    # Domains for Banking Project
    domain_id_accounts = str(uuid.uuid4())
    domain_id_loans = str(uuid.uuid4())

    cursor.execute(
        """
        INSERT OR IGNORE INTO domains (id, organization_id, project_id, name, display_name, version)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (domain_id_accounts, org_id_acme, project_id_banking, "accounts", "Account Management", "1.0.0"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO domains (id, organization_id, project_id, name, display_name, version)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (domain_id_loans, org_id_acme, project_id_banking, "loans", "Loan Services", "1.0.0"),
    )

    # Domains for CRM Project
    domain_id_sales = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT OR IGNORE INTO domains (id, organization_id, project_id, name, display_name, version)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (domain_id_sales, org_id_acme, project_id_crm, "sales", "Sales Pipeline", "1.0.0"),
    )

    # Domains for Demo Project
    domain_id_demo = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT OR IGNORE INTO domains (id, organization_id, project_id, name, display_name, version)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (domain_id_demo, org_id_demo, project_id_demo, "demo", "Demo Domain", "0.1.0"),
    )

    # Users
    user_id_admin = str(uuid.uuid4())
    user_id_developer = str(uuid.uuid4())

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, organization_id, email, name, role)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id_admin, org_id_acme, "admin@acme.com", "Admin User", "admin"),
    )
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (id, organization_id, email, name, role)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id_developer, org_id_acme, "developer@acme.com", "Developer User", "user"),
    )

    conn.commit()
    conn.close()

    print("✅ Seed data created successfully!")
    print("\nOrganizations:")
    print(f"  - Acme Corporation (ID: {org_id_acme})")
    print(f"  - Demo Organization (ID: {org_id_demo})")
    print("\nProjects:")
    print(f"  - Banking Platform (ID: {project_id_banking})")
    print(f"  - CRM (ID: {project_id_crm})")
    print(f"  - Demo Project (ID: {project_id_demo})")
    print("\nDomains:")
    print(f"  - Account Management (ID: {domain_id_accounts})")
    print(f"  - Loan Services (ID: {domain_id_loans})")
    print(f"  - Sales Pipeline (ID: {domain_id_sales})")
    print(f"  - Demo Domain (ID: {domain_id_demo})")
    print("\nUsers:")
    print(f"  - admin@acme.com (ID: {user_id_admin})")
    print(f"  - developer@acme.com (ID: {user_id_developer})")


if __name__ == "__main__":
    seed_data()
