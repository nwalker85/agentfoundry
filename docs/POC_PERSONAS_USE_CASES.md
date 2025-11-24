# Engineering Department — POC User Personas & Use Cases

## Document Information

**Version:** 1.0  
**Date:** November 9, 2025  
**Scope:** Proof of Concept (Phase 1-3)  
**Focus:** Conversational task creation and management

---

## POC User Personas

### Persona 1: Sarah - Startup Founder/Product Manager

**Background:**

- Non-technical or semi-technical background
- Understands business requirements deeply
- Limited knowledge of Agile terminology
- Manages product roadmap and priorities

**Goals:**

- Quickly translate business ideas into development tasks
- Ensure nothing gets lost between meetings and implementation
- Track what's being worked on without learning complex tools

**Pain Points:**

- Jira/Azure DevOps too complex and time-consuming
- Developers misunderstand requirements
- Loses track of decisions made in meetings

**Language Patterns:**

- "We need a way for users to..."
- "Can we add a feature that..."
- "The customers are asking for..."
- "This should work like [competitor/analog]"

---

### Persona 2: Mike - Solo Developer/Small Team Lead

**Background:**

- Full-stack developer with 5+ years experience
- Works on multiple projects simultaneously
- Comfortable with technical requirements
- Wants to minimize process overhead

**Goals:**

- Quickly capture technical requirements while coding
- Create properly formatted stories without context switching
- Maintain velocity without process burden

**Pain Points:**

- Context switching between IDE and task management
- Writing detailed stories takes too much time
- Forgetting implementation details discussed in standups

**Language Patterns:**

- "Add auth endpoint, P1, needs JWT and refresh tokens"
- "Refactor the user service to handle..."
- "Bug: memory leak in the worker process"
- Technical acronyms and library names

---

### Persona 3: Lisa - Business Analyst

**Background:**

- Bridge between business and technical teams
- Strong understanding of both domains
- Detail-oriented documentation skills
- Process-focused mindset

**Goals:**

- Ensure requirements are complete and unambiguous
- Create consistent, well-structured stories
- Track requirements from source to implementation

**Pain Points:**

- Inconsistent story formats across team
- Missing acceptance criteria
- Requirements lost in translation

**Language Patterns:**

- "Create stories for the payment integration epic based on..."
- "The acceptance criteria should include..."
- "Per the requirements document..."
- Structured, formal language

---

## POC Use Cases

### UC-POC-001: Quick Story Creation

**Primary Actor:** Sarah (Product Manager)  
**Frequency:** 10-20 times per week

**Conversation Flow:**

```
Sarah: "Create a story for password reset functionality where users can reset via email"

Agent: "I'll create that story. Which epic should this belong to - Authentication or User Management?"

Sarah: "Authentication"

Agent: "What priority should this have?"

Sarah: "High priority - we're getting support tickets about this"

Agent: "I've created the story with priority P1:
- Notion Story: [link]
- GitHub Issue #234: [link]

The story includes standard password reset acceptance criteria. Would you like to add anything specific?"

Sarah: "Add that it should work with SSO accounts too"

Agent: "Updated! The story now includes SSO compatibility in the acceptance criteria."
```

**Success Criteria:**

- Story created in under 30 seconds
- Maximum 2 clarifying questions
- Links provided immediately
- Can add details post-creation

---

### UC-POC-002: Technical Story with Details

**Primary Actor:** Mike (Developer)  
**Frequency:** 5-10 times per week

**Conversation Flow:**

```
Mike: "New story: Add Redis cache layer for user sessions. P1, part of Performance epic.
      Need to support 10k concurrent sessions, 24hr TTL, automatic failover"

Agent: "Creating a technical story for Redis cache layer:
- Epic: Performance
- Priority: P1
- Key requirements: 10k concurrent, 24hr TTL, failover

I'll add these acceptance criteria:
- Redis cluster supports 10k concurrent sessions
- Session TTL configurable (default 24hr)
- Automatic failover to replica
- Monitoring and alerting configured
- Performance tests demonstrate <10ms latency

Should I include any specific Redis configuration requirements?"

Mike: "Add Redis 7+ and use Redis Streams for session events"

Agent: "Technical requirements added. Story created:
- Notion Story: [link]
- GitHub Issue #235: [link]
The issue includes implementation notes about Redis 7+ and Streams."
```

**Success Criteria:**

- Recognizes technical terminology
- Generates appropriate technical AC
- Includes implementation notes
- Links to existing technical docs

---

### UC-POC-003: Requirement Extraction from Description

**Primary Actor:** Lisa (Business Analyst)  
**Frequency:** 3-5 times per week

**Conversation Flow:**

```
Lisa: "Based on the customer feedback meeting, we need a story for improving the search feature.
      Users want to filter by date range, price, and category, and be able to save their searches.
      They also mentioned wanting to export search results."

Agent: "I'll break down these search improvements into a comprehensive story:

Main Features Identified:
1. Filter by date range
2. Filter by price range
3. Filter by category
4. Save search configurations
5. Export search results

Should this be one large story or would you prefer to split these into separate stories?"

Lisa: "Split the export into a separate story, keep the filters and save functionality together"

Agent: "I've created two stories:

Story 1: 'Enhanced Search Filters with Save Functionality'
- Includes date, price, category filters
- Save search feature
- Notion: [link] | GitHub #236: [link]

Story 2: 'Search Results Export Feature'
- Export to CSV/PDF
- Follows data export standards
- Notion: [link] | GitHub #237: [link]

Both are linked to the 'Search Improvements' epic."
```

**Success Criteria:**

- Extracts multiple requirements from paragraph
- Suggests logical story splits
- Maintains requirement traceability
- Uses consistent formatting

---

### UC-POC-004: Status Query and Reporting

**Primary Actor:** Sarah (Product Manager)  
**Frequency:** Daily

**Conversation Flow:**

```
Sarah: "What are our P0 and P1 stories this week?"

Agent: "Here are your high-priority stories for this week:

**P0 (Critical) - 2 stories:**
1. Fix payment processing error
   - Status: In Progress
   - Assigned: Mike
   - [Notion](link) | [GitHub #230](link)

2. Security patch for authentication
   - Status: In Review
   - Assigned: Team Alpha
   - [Notion](link) | [GitHub #231](link)

**P1 (High) - 5 stories:**
1. Password reset functionality
   - Status: To Do
   - Unassigned
   - [Notion](link) | [GitHub #234](link)

2. Redis cache layer
   - Status: In Progress
   - Assigned: Mike
   - [Notion](link) | [GitHub #235](link)

[... 3 more stories ...]

Would you like to see more details about any of these?"
```

**Success Criteria:**

- Returns current data from Notion
- Shows status and assignees
- Provides direct links
- Offers drill-down options

---

### UC-POC-005: Story Clarification and Refinement

**Primary Actor:** Mike (Developer)  
**Frequency:** Several times per sprint

**Conversation Flow:**

```
Mike: "I need more details on the Redis cache story. What about data persistence?"

Agent: "Looking at the Redis cache story (#235)...

Current requirements include 10k concurrent sessions and 24hr TTL.

For data persistence, would you like me to add acceptance criteria for:
- RDB snapshots configuration?
- AOF (Append Only File) settings?
- Backup strategy?
- Recovery time objectives?"

Mike: "Add RDB hourly snapshots and AOF with everysec policy. RTO should be under 5 minutes"

Agent: "I've updated the story with persistence requirements:
- RDB snapshots every hour
- AOF persistence with 'everysec' fsync policy
- Recovery Time Objective: < 5 minutes
- Added configuration templates to the story description

The story now includes a technical note about data durability tradeoffs."
```

**Success Criteria:**

- Retrieves existing story context
- Suggests relevant technical additions
- Updates story maintaining consistency
- Provides technical guidance

---

### UC-POC-006: Bulk Story Creation

**Primary Actor:** Lisa (Business Analyst)  
**Frequency:** Sprint planning (bi-weekly)

**Conversation Flow:**

```
Lisa: "I need to create stories for the new user onboarding flow. We need:
      1. Welcome email after signup
      2. Tutorial walkthrough on first login
      3. Profile completion reminder after 3 days
      4. Achievement badges for completing onboarding steps"

Agent: "I'll create 4 stories for the user onboarding flow. Let me confirm the details:

1. Welcome Email - triggered immediately after signup
2. Tutorial Walkthrough - interactive guide on first login
3. Profile Reminder - automated reminder after 3 days
4. Achievement Badges - gamification for onboarding completion

What epic should these belong to, and what priority?"

Lisa: "Put them under 'User Engagement' epic, all P2 except the welcome email which should be P1"

Agent: "Created 4 stories in the User Engagement epic:

1. ✅ Welcome Email (P1) - [Notion](link) | [GitHub #238](link)
2. ✅ Tutorial Walkthrough (P2) - [Notion](link) | [GitHub #239](link)
3. ✅ Profile Reminder (P2) - [Notion](link) | [GitHub #240](link)
4. ✅ Achievement Badges (P2) - [Notion](link) | [GitHub #241](link)

All stories include standard acceptance criteria for user communications.
Would you like to add specific requirements to any of them?"
```

**Success Criteria:**

- Handles multiple stories in one request
- Maintains context across all stories
- Applies different priorities correctly
- Groups related stories appropriately

---

### UC-POC-007: Error Recovery and Correction

**Primary Actor:** Sarah (Product Manager)  
**Frequency:** As needed

**Conversation Flow:**

```
Sarah: "Create a story for subscription billing"

Agent: "I'll help you create a subscription billing story. I need a few details:
- Which epic should this belong to?
- What type of billing: monthly, annual, or both?
- Any specific payment providers?"

Sarah: "Actually wait, we already have a billing story. Can you check if one exists?"

Agent: "Let me search for existing billing stories...

Found 2 existing stories related to billing:
1. 'Implement Stripe subscription billing' (P1) - Created 3 days ago
   - Status: In Progress
   - [Notion](link) | [GitHub #225](link)

2. 'Add billing history page' (P2) - Created last week
   - Status: To Do
   - [Notion](link) | [GitHub #220](link)

Would you like to update one of these or create a new specific story?"

Sarah: "Oh right! Can you add PayPal as an option to the Stripe story?"

Agent: "I've updated the Stripe subscription billing story (#225):
- Added 'Support PayPal as alternative payment method' to acceptance criteria
- Updated description to mention multi-provider support
- Added a note about payment provider abstraction layer

The changes are reflected in both Notion and GitHub."
```

**Success Criteria:**

- Can abort story creation
- Searches before creating duplicates
- Updates existing stories when appropriate
- Maintains conversation context through corrections

---

## POC Success Metrics

### Quantitative Metrics

- **Conversation Success Rate:** >85% complete without human intervention
- **Average Clarification Rounds:** ≤2 per story
- **Story Creation Time:** <60 seconds from request to links
- **Duplicate Prevention Rate:** >95% (via idempotency and search)
- **User Retention:** >80% weekly active users after 1 month

### Qualitative Metrics

- **Language Understanding:** Handles natural business language
- **Context Preservation:** Maintains context within conversation
- **Error Recovery:** Gracefully handles mistakes and corrections
- **Appropriate Defaults:** Generates sensible AC and DoD
- **User Satisfaction:** >4/5 rating on usefulness

---

## POC Boundaries

### In Scope

- Single-turn and multi-turn conversations
- Story CRUD operations via chat
- Basic queries and reporting
- Clarification dialogues
- Error correction

### Out of Scope

- Complex workflow automation
- Multi-user collaborative editing
- Real-time notifications
- AI-generated implementation
- Predictive analytics

### Technical Constraints

- English language only
- Single tenant (no user isolation)
- No conversation history persistence (session only)
- Limited to Notion and GitHub integrations
- No file attachment processing

---

## Conversation Design Principles

### 1. Progressive Disclosure

- Don't ask for all information upfront
- Request clarification only when needed
- Provide smart defaults

### 2. Confirmation, Not Interrogation

- Maximum 2 clarifying questions
- Bundle related questions
- Accept partial information

### 3. Recovery and Correction

- Allow users to change their mind
- Search before creating
- Update rather than duplicate

### 4. Context Awareness

- Remember information within conversation
- Reference recent stories
- Suggest based on patterns

### 5. Appropriate Language

- Match user's technical level
- Sarah: Business language
- Mike: Technical terminology
- Lisa: Formal structure

---

## Appendix: Sample Conversation Corpus

### Business Language (Sarah)

- "We need a way to track customer complaints"
- "Users are asking for dark mode"
- "The checkout process is too complicated"
- "Can we make the search faster?"

### Technical Language (Mike)

- "Implement OAuth2 with PKCE flow"
- "Add Redis cache with 5 minute TTL"
- "Refactor user service to use repository pattern"
- "Debug memory leak in worker process"

### Formal Language (Lisa)

- "Create user stories for the payment integration epic"
- "Document acceptance criteria for the API endpoints"
- "As a user, I want to export my data"
- "The story should include performance requirements"

---

_Document Version 1.0 - POC Personas and Use Cases_  
_Last Updated: November 9, 2025_
