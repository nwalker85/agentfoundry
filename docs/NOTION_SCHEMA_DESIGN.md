# Engineering Department - Notion Database Schema

## Philosophy

Minimal but professional schema that demonstrates sophisticated project
management without recreating Jira. Focus on essential fields that show
AI-driven story creation and tracking.

## Epics Database Schema

### Properties

| Property       | Type             | Description                 | Options/Format                                                 |
| -------------- | ---------------- | --------------------------- | -------------------------------------------------------------- |
| Title          | Title            | Epic name                   | -                                                              |
| Description    | Text             | High-level epic description | -                                                              |
| Status         | Select           | Current epic status         | Planning, Active, On Hold, Complete                            |
| Priority       | Select           | Epic priority               | P0 (Critical), P1 (High), P2 (Medium), P3 (Low)                |
| Target Quarter | Select           | Target completion quarter   | Q1 2025, Q2 2025, Q3 2025, Q4 2025                             |
| Business Value | Select           | Business impact level       | High, Medium, Low                                              |
| Technical Area | Multi-select     | Technical domains           | Frontend, Backend, Infrastructure, Data, Security, API, DevOps |
| Created By     | Select           | Who created this            | PM Agent, Human                                                |
| Created Date   | Created time     | Auto-generated              | -                                                              |
| Updated Date   | Last edited time | Auto-generated              | -                                                              |

## Stories Database Schema

### Properties

| Property            | Type             | Description                           | Options/Format                                        |
| ------------------- | ---------------- | ------------------------------------- | ----------------------------------------------------- |
| Title               | Title            | Story title                           | -                                                     |
| Epic                | Relation         | Link to parent epic                   | Relation to Epics                                     |
| User Story          | Text             | "As a... I want... So that..." format | -                                                     |
| Description         | Text             | Detailed requirements                 | -                                                     |
| Acceptance Criteria | Text             | Testable success criteria             | Bullet points                                         |
| Status              | Select           | Current story status                  | Backlog, Ready, In Progress, In Review, Done, Blocked |
| Priority            | Select           | Story priority                        | P0 (Critical), P1 (High), P2 (Medium), P3 (Low)       |
| Story Points        | Select           | Complexity estimate                   | 1, 2, 3, 5, 8, 13                                     |
| Sprint              | Select           | Sprint assignment                     | Backlog, Sprint 1, Sprint 2, Sprint 3, Sprint 4       |
| Technical Type      | Select           | Type of work                          | Feature, Bug Fix, Tech Debt, Research, Documentation  |
| GitHub Issue        | URL              | Link to GitHub issue                  | -                                                     |
| GitHub PR           | URL              | Link to pull request                  | -                                                     |
| Assignee            | Text             | Who's working on this                 | -                                                     |
| AI Generated        | Checkbox         | Created by PM Agent                   | -                                                     |
| Created Date        | Created time     | Auto-generated                        | -                                                     |
| Updated Date        | Last edited time | Auto-generated                        | -                                                     |

## Why This Schema Works

1. **Lightweight**: Only essential fields, no bureaucracy
2. **AI-Friendly**: Fields that the PM Agent can intelligently populate
3. **Demo-Ready**: Shows sophistication without complexity
4. **Traceable**: Links between epics, stories, and GitHub
5. **Measurable**: Points, priorities, and quarters for planning
6. **Professional**: Industry-standard terminology and practices
