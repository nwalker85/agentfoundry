#!/usr/bin/env python3
"""
Add Industry Platform Tools

Adds major industry-specific core systems for Utilities, Airlines, Hotels, and Healthcare.
"""

import json
from pathlib import Path

MANIFEST_PATH = "/app/mcp/integration_server/config/integrations.manifest.json"

industry_tools_manifest = [
    # ============================================================================
    # UTILITIES
    # ============================================================================
    {
        "toolName": "oracle.utilities",
        "displayName": "Oracle Utilities",
        "description": "Enterprise Customer Information System (CIS) and customer care solutions for utilities. Comprehensive billing, metering, and customer service platform.",
        "category": "Utilities",
        "logo": "oracle",
        "icon": "oracle",
        "tags": ["utilities", "cis", "billing", "metering", "customer-service"],
        "metadata": {
            "version": 1,
            "source": "industry-platforms",
            "node_type": "custom.OracleUtilities",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/oracle-utilities-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "sap.utilities",
        "displayName": "SAP for Utilities",
        "description": "SAP Industry Cloud for utilities provides end-to-end solutions for customer engagement, billing, and operations management.",
        "category": "Utilities",
        "logo": "sap",
        "icon": "sap",
        "tags": ["utilities", "cis", "billing", "erp", "enterprise"],
        "metadata": {
            "version": 1,
            "source": "industry-platforms",
            "node_type": "custom.SAPUtilities",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/sap-utilities-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "abb.ability",
        "displayName": "ABB Ability",
        "description": "Enterprise Asset Management (EAM) and digital solutions for utilities. Industrial automation and electrification technology platform.",
        "category": "Utilities",
        "logo": "abb",
        "icon": "abb",
        "tags": ["utilities", "eam", "asset-management", "automation", "iot"],
        "metadata": {
            "version": 1,
            "source": "industry-platforms",
            "node_type": "custom.ABBAbility",
            "authType": "apikey",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/abb-ability-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "siemens.energy",
        "displayName": "Siemens Energy Platform",
        "description": "Digital solutions and Enterprise Asset Management for utilities. Grid automation, asset performance, and energy management systems.",
        "category": "Utilities",
        "logo": "siemens",
        "icon": "siemens",
        "tags": ["utilities", "eam", "grid-management", "energy", "automation"],
        "metadata": {
            "version": 1,
            "source": "industry-platforms",
            "node_type": "custom.SiemensEnergy",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/siemens-energy-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    # ============================================================================
    # AIRLINES
    # ============================================================================
    {
        "toolName": "amadeus.pss",
        "displayName": "Amadeus",
        "description": "Leading Passenger Service System (PSS) and Operations Control platform. Comprehensive airline reservation, inventory, and departure control solutions.",
        "category": "Airlines",
        "logo": "amadeus",
        "icon": "amadeus",
        "tags": ["airlines", "pss", "reservations", "operations", "travel"],
        "metadata": {"version": 1, "source": "industry-platforms", "node_type": "custom.Amadeus", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/amadeus-pss-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "sabre.pss",
        "displayName": "Sabre",
        "description": "Global Passenger Service System and travel technology platform. Powering reservations, operations, and revenue optimization for airlines worldwide.",
        "category": "Airlines",
        "logo": "sabre",
        "icon": "sabre",
        "tags": ["airlines", "pss", "gds", "reservations", "travel"],
        "metadata": {"version": 1, "source": "industry-platforms", "node_type": "custom.Sabre", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/sabre-pss-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "travelport.pss",
        "displayName": "Travelport",
        "description": "Travel commerce platform providing PSS and distribution solutions. Connects airlines with travel agencies and corporate buyers globally.",
        "category": "Airlines",
        "logo": "travelport",
        "icon": "travelport",
        "tags": ["airlines", "pss", "gds", "distribution", "travel"],
        "metadata": {
            "version": 1,
            "source": "industry-platforms",
            "node_type": "custom.Travelport",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/travelport-pss-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "sita.aero",
        "displayName": "SITA",
        "description": "Aviation IT solutions provider. Offers Passenger Service Systems, baggage management, and airport operations platforms for airlines worldwide.",
        "category": "Airlines",
        "logo": "sita",
        "icon": "sita",
        "tags": ["airlines", "pss", "operations", "baggage", "aviation-it"],
        "metadata": {"version": 1, "source": "industry-platforms", "node_type": "custom.SITA", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/sita-aero-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    # ============================================================================
    # HOTELS
    # ============================================================================
    {
        "toolName": "oracle.opera",
        "displayName": "Oracle Hospitality (OPERA)",
        "description": "Leading Property Management System (PMS) for hotels. Comprehensive solution for reservations, front desk, housekeeping, and guest services.",
        "category": "Hotels",
        "logo": "oracle",
        "icon": "oracle",
        "tags": ["hotels", "pms", "hospitality", "reservations", "property-management"],
        "metadata": {
            "version": 1,
            "source": "industry-platforms",
            "node_type": "custom.OracleOPERA",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/oracle-opera-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "mews.pms",
        "displayName": "Mews",
        "description": "Cloud-native Property Management System for modern hotels. Open API platform for reservations, operations, and guest experience management.",
        "category": "Hotels",
        "logo": "mews",
        "icon": "mews",
        "tags": ["hotels", "pms", "cloud-native", "api-first", "hospitality"],
        "metadata": {"version": 1, "source": "industry-platforms", "node_type": "custom.Mews", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/mews-pms-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "cloudbeds.pms",
        "displayName": "Cloudbeds",
        "description": "All-in-one Property Management System for hotels, hostels, and vacation rentals. Cloud-based platform with integrated channel management.",
        "category": "Hotels",
        "logo": "cloudbeds",
        "icon": "cloudbeds",
        "tags": ["hotels", "pms", "cloud-based", "channel-manager", "hospitality"],
        "metadata": {
            "version": 1,
            "source": "industry-platforms",
            "node_type": "custom.Cloudbeds",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/cloudbeds-pms-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "shiji.pms",
        "displayName": "Shiji Group",
        "description": "Global hospitality technology provider. Offers PMS, point-of-sale, distribution, and guest engagement solutions for hotels worldwide.",
        "category": "Hotels",
        "logo": "shiji",
        "icon": "shiji",
        "tags": ["hotels", "pms", "pos", "hospitality", "global"],
        "metadata": {"version": 1, "source": "industry-platforms", "node_type": "custom.Shiji", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/shiji-pms-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    # ============================================================================
    # HEALTHCARE
    # ============================================================================
    {
        "toolName": "epic.ehr",
        "displayName": "Epic",
        "description": "Leading Electronic Health Records (EHR) system. Comprehensive EMR platform used by major health systems and hospitals worldwide.",
        "category": "Healthcare",
        "logo": "epic",
        "icon": "epic",
        "tags": ["healthcare", "ehr", "emr", "patient-records", "clinical"],
        "metadata": {"version": 1, "source": "industry-platforms", "node_type": "custom.Epic", "authType": "oauth2"},
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/epic-ehr-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "oracle.health",
        "displayName": "Oracle Health (Cerner)",
        "description": "Enterprise Electronic Medical Records platform. Comprehensive EHR/EMR solutions for hospitals, clinics, and health systems globally.",
        "category": "Healthcare",
        "logo": "oracle",
        "icon": "oracle",
        "tags": ["healthcare", "ehr", "emr", "cerner", "clinical"],
        "metadata": {
            "version": 1,
            "source": "industry-platforms",
            "node_type": "custom.OracleHealth",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/oracle-health-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "meditech.ehr",
        "displayName": "MEDITECH",
        "description": "Electronic Health Records platform for hospitals and healthcare organizations. Integrated EHR, revenue cycle, and patient engagement solutions.",
        "category": "Healthcare",
        "logo": "meditech",
        "icon": "meditech",
        "tags": ["healthcare", "ehr", "emr", "hospital-systems", "clinical"],
        "metadata": {
            "version": 1,
            "source": "industry-platforms",
            "node_type": "custom.MEDITECH",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/meditech-ehr-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
    {
        "toolName": "athenahealth.ehr",
        "displayName": "athenahealth",
        "description": "Cloud-based Electronic Health Records and practice management platform. Integrated EHR, revenue cycle management, and patient engagement for ambulatory care.",
        "category": "Healthcare",
        "logo": "athenahealth",
        "icon": "athenahealth",
        "tags": ["healthcare", "ehr", "cloud-based", "practice-management", "ambulatory"],
        "metadata": {
            "version": 1,
            "source": "industry-platforms",
            "node_type": "custom.athenahealth",
            "authType": "oauth2",
        },
        "n8n": {"type": "webhook", "url": "http://n8n:5678/webhook/athenahealth-ehr-execute"},
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "outputSchema": {"type": "object", "properties": {"success": {"type": "boolean"}, "data": {"type": "object"}}},
    },
]


def add_industry_platforms():
    """Add industry platform tools to the integration manifest"""
    manifest_file = Path(MANIFEST_PATH)

    # Load existing manifest
    with open(manifest_file) as f:
        manifest = json.load(f)

    print(f"📦 Current manifest has {len(manifest)} tools")

    # Check which tools already exist
    existing_tool_names = {tool["toolName"] for tool in manifest}
    new_tools = [tool for tool in industry_tools_manifest if tool["toolName"] not in existing_tool_names]

    if not new_tools:
        print("⚠️  All industry platform tools already exist in manifest")
        return

    # Add new tools
    manifest.extend(new_tools)

    # Save updated manifest
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"✅ Added {len(new_tools)} new industry platform tools")
    print(f"📦 Updated manifest now has {len(manifest)} tools")

    # Group by category
    by_category = {}
    for tool in new_tools:
        category = tool["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(tool["displayName"])

    print("\nAdded platforms by industry:")
    for category, tools in sorted(by_category.items()):
        print(f"\n{category}:")
        for tool_name in tools:
            print(f"  - {tool_name}")


if __name__ == "__main__":
    add_industry_platforms()
