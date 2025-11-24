"""
N8N API Client

Queries n8n REST API to discover available integrations and workflows.
"""

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class N8NClient:
    """Client for interacting with n8n REST API"""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        self.base_url = (base_url or os.getenv("N8N_BASE_URL", "http://n8n:5678")).rstrip("/")
        self.api_key = api_key or os.getenv("N8N_API_KEY")
        self.username = username or os.getenv("N8N_BASIC_AUTH_USER")
        self.password = password or os.getenv("N8N_BASIC_AUTH_PASSWORD")

        self.client = httpx.Client(timeout=30.0)

    def _get_headers(self) -> dict[str, str]:
        """Build request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers

    def _get_auth(self) -> httpx.BasicAuth | None:
        """Build basic auth if configured"""
        if self.username and self.password:
            return httpx.BasicAuth(self.username, self.password)
        return None

    def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make HTTP request to n8n API"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        auth = self._get_auth()

        try:
            response = self.client.request(
                method,
                url,
                headers=headers,
                auth=auth,
                **kwargs,
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except httpx.HTTPError as exc:
            logger.error("N8N API request failed: %s", exc)
            raise

    def get_node_types(self) -> list[dict[str, Any]]:
        """
        Get all available node types (integrations) from n8n.

        Returns list of node type definitions with:
        - name: Node type name (e.g., "n8n-nodes-base.slack")
        - displayName: Human-readable name
        - description: Description
        - properties: Input parameters
        - outputs: Output parameters
        """
        try:
            # Try the public types endpoint first (doesn't require auth in some versions)
            data = self._request("GET", "/types/nodes.json")

            # n8n returns node types as an object keyed by node name
            if isinstance(data, dict):
                node_types = []
                for node_name, node_def in data.items():
                    node_types.append(
                        {
                            "name": node_name,
                            "displayName": node_def.get("displayName", node_name),
                            "description": node_def.get("description", ""),
                            "group": node_def.get("group", []),
                            "version": node_def.get("version", 1),
                            "properties": node_def.get("properties", []),
                            "outputs": node_def.get("outputs", []),
                            "credentials": node_def.get("credentials", []),
                        }
                    )
                return node_types
            return []
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                # n8n requires auth - return a curated list of popular integrations
                logger.warning("N8N requires authentication. Using curated list of popular integrations.")
                return self._get_curated_node_list()
            logger.warning("Failed to fetch node types from n8n: %s", exc)
            return self._get_curated_node_list()
        except Exception as exc:
            logger.warning("Failed to fetch node types from n8n: %s", exc)
            # Return curated list as fallback
            return self._get_curated_node_list()

    def _get_curated_node_list(self) -> list[dict[str, Any]]:
        """
        Return a curated list of 150+ popular n8n integrations.
        This is used when the n8n API is not accessible.
        """
        return [
            # Communication (15)
            {
                "name": "n8n-nodes-base.slack",
                "displayName": "Slack",
                "description": "Communicate via Slack",
                "group": ["communication"],
                "version": 2,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.discord",
                "displayName": "Discord",
                "description": "Communicate via Discord",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.telegram",
                "displayName": "Telegram",
                "description": "Communicate via Telegram",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.microsoftTeams",
                "displayName": "Microsoft Teams",
                "description": "Communicate via MS Teams",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.gmail",
                "displayName": "Gmail",
                "description": "Send and receive email via Gmail",
                "group": ["communication"],
                "version": 2,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.twilio",
                "displayName": "Twilio",
                "description": "Send SMS via Twilio",
                "group": ["communication"],
                "version": 2,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.sendGrid",
                "displayName": "SendGrid",
                "description": "Send email via SendGrid",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.whatsApp",
                "displayName": "WhatsApp",
                "description": "Send WhatsApp messages",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.mattermost",
                "displayName": "Mattermost",
                "description": "Communicate via Mattermost",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.rocketchat",
                "displayName": "Rocket.Chat",
                "description": "Communicate via Rocket.Chat",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.intercom",
                "displayName": "Intercom",
                "description": "Customer messaging platform",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.drift",
                "displayName": "Drift",
                "description": "Conversational marketing",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.frontegg",
                "displayName": "Front",
                "description": "Team inbox",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.smtp",
                "displayName": "SMTP",
                "description": "Send email via SMTP",
                "group": ["communication"],
                "version": 2,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.imap",
                "displayName": "IMAP",
                "description": "Receive email via IMAP",
                "group": ["communication"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # Project Management (12)
            {
                "name": "n8n-nodes-base.jira",
                "displayName": "Jira Software",
                "description": "Manage Jira issues",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.asana",
                "displayName": "Asana",
                "description": "Manage Asana tasks",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.trello",
                "displayName": "Trello",
                "description": "Manage Trello boards",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.clickUp",
                "displayName": "ClickUp",
                "description": "Manage ClickUp tasks",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.monday",
                "displayName": "Monday.com",
                "description": "Work with Monday boards",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.baserow",
                "displayName": "Baserow",
                "description": "Work with Baserow databases",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.linear",
                "displayName": "Linear",
                "description": "Manage Linear issues",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.shortcut",
                "displayName": "Shortcut",
                "description": "Manage Shortcut stories",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.height",
                "displayName": "Height",
                "description": "Manage Height tasks",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.wrike",
                "displayName": "Wrike",
                "description": "Manage Wrike tasks",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.teamwork",
                "displayName": "Teamwork",
                "description": "Manage Teamwork tasks",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.smartsheet",
                "displayName": "Smartsheet",
                "description": "Work with Smartsheet",
                "group": ["project"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # CRM (10)
            {
                "name": "n8n-nodes-base.salesforce",
                "displayName": "Salesforce",
                "description": "Work with Salesforce CRM",
                "group": ["crm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.hubspot",
                "displayName": "HubSpot",
                "description": "Work with HubSpot CRM",
                "group": ["crm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.pipedrive",
                "displayName": "Pipedrive",
                "description": "Work with Pipedrive CRM",
                "group": ["crm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.zoho",
                "displayName": "Zoho CRM",
                "description": "Work with Zoho CRM",
                "group": ["crm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.copper",
                "displayName": "Copper",
                "description": "Work with Copper CRM",
                "group": ["crm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.capsule",
                "displayName": "Capsule CRM",
                "description": "Work with Capsule CRM",
                "group": ["crm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.activeCampaign",
                "displayName": "ActiveCampaign",
                "description": "Marketing automation",
                "group": ["crm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.close",
                "displayName": "Close",
                "description": "Sales CRM",
                "group": ["crm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.nimble",
                "displayName": "Nimble",
                "description": "Social CRM",
                "group": ["crm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.microsoftDynamics",
                "displayName": "Microsoft Dynamics",
                "description": "Work with Dynamics CRM",
                "group": ["crm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # ITSM & Support (8)
            {
                "name": "n8n-nodes-base.servicenow",
                "displayName": "ServiceNow",
                "description": "Manage ServiceNow tickets",
                "group": ["itsm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.zendesk",
                "displayName": "Zendesk",
                "description": "Manage Zendesk tickets",
                "group": ["itsm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.freshservice",
                "displayName": "Freshservice",
                "description": "Manage Freshservice tickets",
                "group": ["itsm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.freshdesk",
                "displayName": "Freshdesk",
                "description": "Customer support",
                "group": ["itsm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.helpScout",
                "displayName": "Help Scout",
                "description": "Customer support platform",
                "group": ["itsm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.jira.serviceDesk",
                "displayName": "Jira Service Desk",
                "description": "IT service desk",
                "group": ["itsm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.pagerduty",
                "displayName": "PagerDuty",
                "description": "Incident management",
                "group": ["itsm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.opsgenie",
                "displayName": "Opsgenie",
                "description": "Alert and incident management",
                "group": ["itsm"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # Productivity & Storage (15)
            {
                "name": "n8n-nodes-base.notion",
                "displayName": "Notion",
                "description": "Work with Notion databases",
                "group": ["productivity"],
                "version": 2,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.googleDrive",
                "displayName": "Google Drive",
                "description": "Work with Google Drive files",
                "group": ["productivity"],
                "version": 3,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.googleSheets",
                "displayName": "Google Sheets",
                "description": "Work with Google Sheets",
                "group": ["productivity"],
                "version": 4,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.googleDocs",
                "displayName": "Google Docs",
                "description": "Work with Google Docs",
                "group": ["productivity"],
                "version": 2,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.googleCalendar",
                "displayName": "Google Calendar",
                "description": "Manage Google Calendar",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.dropbox",
                "displayName": "Dropbox",
                "description": "Work with Dropbox files",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.airtable",
                "displayName": "Airtable",
                "description": "Work with Airtable bases",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.box",
                "displayName": "Box",
                "description": "Cloud content management",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.oneDrive",
                "displayName": "Microsoft OneDrive",
                "description": "Cloud storage",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.sharepoint",
                "displayName": "SharePoint",
                "description": "Collaboration platform",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.microsoftExcel",
                "displayName": "Microsoft Excel",
                "description": "Work with Excel files",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.microsoftOutlook",
                "displayName": "Microsoft Outlook",
                "description": "Email and calendar",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.evernote",
                "displayName": "Evernote",
                "description": "Note taking",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.confluence",
                "displayName": "Confluence",
                "description": "Team collaboration",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.coda",
                "displayName": "Coda",
                "description": "Collaborative docs",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # Cloud Services (12)
            {
                "name": "n8n-nodes-base.github",
                "displayName": "GitHub",
                "description": "Work with GitHub repos",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.gitlab",
                "displayName": "GitLab",
                "description": "Work with GitLab projects",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.bitbucket",
                "displayName": "Bitbucket",
                "description": "Work with Bitbucket repos",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.aws",
                "displayName": "AWS",
                "description": "Work with AWS services",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.awsS3",
                "displayName": "AWS S3",
                "description": "Object storage",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.awsLambda",
                "displayName": "AWS Lambda",
                "description": "Serverless functions",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.googleCloud",
                "displayName": "Google Cloud",
                "description": "Work with GCP services",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.gcpStorage",
                "displayName": "GCP Storage",
                "description": "Cloud storage",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.azure",
                "displayName": "Microsoft Azure",
                "description": "Work with Azure services",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.digitalOcean",
                "displayName": "DigitalOcean",
                "description": "Cloud infrastructure",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.heroku",
                "displayName": "Heroku",
                "description": "Cloud platform",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.vercel",
                "displayName": "Vercel",
                "description": "Deployment platform",
                "group": ["cloud"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # Databases (10)
            {
                "name": "n8n-nodes-base.postgres",
                "displayName": "PostgreSQL",
                "description": "Work with PostgreSQL database",
                "group": ["database"],
                "version": 2,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.mysql",
                "displayName": "MySQL",
                "description": "Work with MySQL database",
                "group": ["database"],
                "version": 2,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.mongodb",
                "displayName": "MongoDB",
                "description": "Work with MongoDB database",
                "group": ["database"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.redis",
                "displayName": "Redis",
                "description": "Work with Redis cache",
                "group": ["database"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.microsoftSql",
                "displayName": "Microsoft SQL",
                "description": "Work with MS SQL Server",
                "group": ["database"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.questDb",
                "displayName": "QuestDB",
                "description": "Time-series database",
                "group": ["database"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.supabase",
                "displayName": "Supabase",
                "description": "Backend as a service",
                "group": ["database"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.firebase",
                "displayName": "Firebase",
                "description": "Google's app platform",
                "group": ["database"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.elasticsearch",
                "displayName": "Elasticsearch",
                "description": "Search and analytics",
                "group": ["database"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.influxDb",
                "displayName": "InfluxDB",
                "description": "Time-series database",
                "group": ["database"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # AI & ML (8)
            {
                "name": "n8n-nodes-base.openAi",
                "displayName": "OpenAI",
                "description": "Work with OpenAI API",
                "group": ["ai"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.anthropic",
                "displayName": "Anthropic",
                "description": "Work with Anthropic Claude",
                "group": ["ai"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.cohere",
                "displayName": "Cohere",
                "description": "NLP AI platform",
                "group": ["ai"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.huggingFace",
                "displayName": "Hugging Face",
                "description": "AI model hub",
                "group": ["ai"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.stabilityAi",
                "displayName": "Stability AI",
                "description": "Image generation",
                "group": ["ai"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.elevenlabs",
                "displayName": "ElevenLabs",
                "description": "Text to speech",
                "group": ["ai"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.assemblyAi",
                "displayName": "AssemblyAI",
                "description": "Speech to text",
                "group": ["ai"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.pinecone",
                "displayName": "Pinecone",
                "description": "Vector database",
                "group": ["ai"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # E-commerce & Payments (10)
            {
                "name": "n8n-nodes-base.stripe",
                "displayName": "Stripe",
                "description": "Process payments with Stripe",
                "group": ["commerce"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.shopify",
                "displayName": "Shopify",
                "description": "Work with Shopify store",
                "group": ["commerce"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.wooCommerce",
                "displayName": "WooCommerce",
                "description": "WordPress e-commerce",
                "group": ["commerce"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.square",
                "displayName": "Square",
                "description": "Payment processing",
                "group": ["commerce"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.paypal",
                "displayName": "PayPal",
                "description": "Online payments",
                "group": ["commerce"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.magento",
                "displayName": "Magento",
                "description": "E-commerce platform",
                "group": ["commerce"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.bigCommerce",
                "displayName": "BigCommerce",
                "description": "E-commerce platform",
                "group": ["commerce"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.prestashop",
                "displayName": "PrestaShop",
                "description": "E-commerce solution",
                "group": ["commerce"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.chargebee",
                "displayName": "Chargebee",
                "description": "Subscription billing",
                "group": ["commerce"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.paddle",
                "displayName": "Paddle",
                "description": "Payment platform",
                "group": ["commerce"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # Marketing & Analytics (12)
            {
                "name": "n8n-nodes-base.mailchimp",
                "displayName": "Mailchimp",
                "description": "Manage Mailchimp campaigns",
                "group": ["marketing"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.googleAnalytics",
                "displayName": "Google Analytics",
                "description": "Web analytics",
                "group": ["analytics"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.segment",
                "displayName": "Segment",
                "description": "Customer data platform",
                "group": ["analytics"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.mixpanel",
                "displayName": "Mixpanel",
                "description": "Product analytics",
                "group": ["analytics"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.amplitude",
                "displayName": "Amplitude",
                "description": "Product analytics",
                "group": ["analytics"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.posthog",
                "displayName": "PostHog",
                "description": "Product analytics",
                "group": ["analytics"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.constantContact",
                "displayName": "Constant Contact",
                "description": "Email marketing",
                "group": ["marketing"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.convertKit",
                "displayName": "ConvertKit",
                "description": "Email marketing",
                "group": ["marketing"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.klaviyo",
                "displayName": "Klaviyo",
                "description": "Marketing automation",
                "group": ["marketing"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.brevo",
                "displayName": "Brevo",
                "description": "Email marketing",
                "group": ["marketing"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.drip",
                "displayName": "Drip",
                "description": "Email automation",
                "group": ["marketing"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.customerIo",
                "displayName": "Customer.io",
                "description": "Messaging automation",
                "group": ["marketing"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # Social Media (8)
            {
                "name": "n8n-nodes-base.linkedIn",
                "displayName": "LinkedIn",
                "description": "Work with LinkedIn",
                "group": ["social"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.twitter",
                "displayName": "Twitter",
                "description": "Work with Twitter/X",
                "group": ["social"],
                "version": 2,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.facebook",
                "displayName": "Facebook",
                "description": "Social media platform",
                "group": ["social"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.instagram",
                "displayName": "Instagram",
                "description": "Photo sharing",
                "group": ["social"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.youtube",
                "displayName": "YouTube",
                "description": "Video platform",
                "group": ["social"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.reddit",
                "displayName": "Reddit",
                "description": "Social news platform",
                "group": ["social"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.tiktok",
                "displayName": "TikTok",
                "description": "Short video platform",
                "group": ["social"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.mastodon",
                "displayName": "Mastodon",
                "description": "Federated social network",
                "group": ["social"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # Developer Tools & APIs (10)
            {
                "name": "n8n-nodes-base.httpRequest",
                "displayName": "HTTP Request",
                "description": "Make HTTP requests",
                "group": ["other"],
                "version": 4,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.webhook",
                "displayName": "Webhook",
                "description": "Receive webhooks",
                "group": ["other"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.graphql",
                "displayName": "GraphQL",
                "description": "Execute GraphQL queries",
                "group": ["other"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.ssh",
                "displayName": "SSH",
                "description": "Execute SSH commands",
                "group": ["other"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.ftp",
                "displayName": "FTP",
                "description": "File transfer",
                "group": ["other"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.apiTemplateIo",
                "displayName": "API Template",
                "description": "Generate PDFs and images",
                "group": ["other"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.postman",
                "displayName": "Postman",
                "description": "API development",
                "group": ["other"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.algolia",
                "displayName": "Algolia",
                "description": "Search as a service",
                "group": ["other"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.cloudflare",
                "displayName": "Cloudflare",
                "description": "CDN and security",
                "group": ["other"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.datadog",
                "displayName": "Datadog",
                "description": "Monitoring and analytics",
                "group": ["other"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            # Forms & Surveys (6)
            {
                "name": "n8n-nodes-base.typeform",
                "displayName": "Typeform",
                "description": "Online forms",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.googleForms",
                "displayName": "Google Forms",
                "description": "Create surveys",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.jotform",
                "displayName": "JotForm",
                "description": "Form builder",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.surveyMonkey",
                "displayName": "SurveyMonkey",
                "description": "Survey platform",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.formIo",
                "displayName": "Form.io",
                "description": "Form platform",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
            {
                "name": "n8n-nodes-base.cognito",
                "displayName": "Cognito Forms",
                "description": "Online forms",
                "group": ["productivity"],
                "version": 1,
                "properties": [],
                "outputs": [],
                "credentials": [],
            },
        ]

    def get_workflows(self) -> list[dict[str, Any]]:
        """
        Get all workflows from n8n.

        Returns list of workflows with:
        - id: Workflow ID
        - name: Workflow name
        - active: Whether workflow is active
        - nodes: List of nodes in workflow
        - connections: Node connections
        """
        try:
            data = self._request("GET", "/api/v1/workflows")
            return data.get("data", [])
        except Exception as exc:
            logger.warning("Failed to fetch workflows from n8n: %s", exc)
            return []

    def get_workflow(self, workflow_id: str) -> dict[str, Any] | None:
        """Get a specific workflow by ID"""
        try:
            return self._request("GET", f"/api/v1/workflows/{workflow_id}")
        except Exception as exc:
            logger.warning("Failed to fetch workflow %s: %s", workflow_id, exc)
            return None

    def close(self):
        """Close HTTP client"""
        self.client.close()


def categorize_node(node_name: str, node_def: dict[str, Any]) -> str:
    """
    Categorize a node based on its name and group.

    Returns category like: Communication, CRM, Productivity, etc.
    """
    # Extract groups from node definition
    groups = node_def.get("group", [])

    # Category mapping based on n8n groups and common patterns
    if "communication" in groups or any(
        x in node_name.lower() for x in ["slack", "discord", "telegram", "teams", "mail", "smtp"]
    ):
        return "Communication"

    if "crm" in groups or any(x in node_name.lower() for x in ["salesforce", "hubspot", "pipedrive", "zoho"]):
        return "CRM"

    if "project" in groups or any(x in node_name.lower() for x in ["jira", "asana", "trello", "notion", "clickup"]):
        return "Project Management"

    if "itsm" in groups or any(x in node_name.lower() for x in ["servicenow", "freshservice", "zendesk"]):
        return "ITSM"

    if "analytics" in groups or any(x in node_name.lower() for x in ["google.analytics", "mixpanel", "segment"]):
        return "Analytics"

    if "cloud" in groups or any(x in node_name.lower() for x in ["aws", "gcp", "azure", "s3", "lambda"]):
        return "Cloud Services"

    if "database" in groups or any(
        x in node_name.lower() for x in ["postgres", "mysql", "mongodb", "redis", "supabase"]
    ):
        return "Database"

    if "ai" in groups or any(x in node_name.lower() for x in ["openai", "anthropic", "cohere", "huggingface"]):
        return "AI & ML"

    if "productivity" in groups or any(
        x in node_name.lower() for x in ["google.drive", "dropbox", "airtable", "sheets"]
    ):
        return "Productivity"

    # Default category
    return "Other"


def extract_logo_name(node_name: str) -> str:
    """
    Extract a simplified logo name from node type name.

    Example: "n8n-nodes-base.slack" -> "slack"
    """
    # Remove common prefixes
    name = node_name.replace("n8n-nodes-base.", "")
    name = name.replace("n8n-nodes-", "")

    # Split by dots and take first part
    parts = name.split(".")
    if len(parts) > 0:
        return parts[0].lower()

    return name.lower()


if __name__ == "__main__":
    # Test the client
    logging.basicConfig(level=logging.INFO)

    client = N8NClient()

    print("Fetching node types from n8n...")
    node_types = client.get_node_types()

    print(f"\nFound {len(node_types)} node types")

    # Show sample
    if node_types:
        print("\nSample node types:")
        for node in node_types[:5]:
            category = categorize_node(node["name"], node)
            logo = extract_logo_name(node["name"])
            print(f"  - {node['displayName']} ({category}) [logo: {logo}]")

    client.close()
