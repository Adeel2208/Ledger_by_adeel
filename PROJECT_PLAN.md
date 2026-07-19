# The VC Brain - Production-Ready Project Plan

## Executive Summary

**Project Name:** The VC Brain  
**Client:** Maschmeyer Group  
**Objective:** Build an AI-powered venture capital deal flow and evaluation system that democratizes access to capital by identifying and evaluating strong founders before they start fundraising, reducing decision time from weeks to 24 hours.

**Core Value Proposition:** Give a single investor (or small team) the reach and analytical power of an entire investment organization.

---

## Problem Statement

### Current State Pain Points
1. **Relationship-Gated Capital Flow**: Capital flows to founders with networks, not necessarily the strongest builders
2. **Invisible Founders**: Strong founders remain hidden until someone spots them
3. **Scattered Information**: Founder stories fragmented across pitch decks, GitHub, social posts
4. **Slow Diligence**: Traditional process takes weeks, causing strong founders to give up
5. **Cold-Start Founder Disadvantage**: No funding history/GitHub/network = invisible to traditional VC

### Solution
An intelligent system that:
- Finds strong founders **before** they start fundraising
- Evaluates consistently and transparently using multi-dimensional scoring
- Delivers decision-ready $100K investment recommendations within **24 hours**
- Supports both **inbound** (founder-initiated) and **outbound** (system-discovered) deal flow

---

## System Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXPERIENCE LAYER                          │
│              (Investor-Facing Dashboard)                     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                   INTELLIGENCE LAYER                         │
│    (Thesis Engine, Screening, Reasoning, Trust Scoring)     │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│                     MEMORY LAYER                             │
│         (Data Ingestion, Deduplication, Enrichment)         │
└─────────────────────────────────────────────────────────────┘
```

### Four-Stage Pipeline

**Sourcing → Screening → Diligence → Decision**

---

## Detailed Requirements

### 1. MEMORY LAYER (Data Foundation)

#### 1.1 Data Ingestion System
**Priority:** P0 (Critical Path)

**Requirements:**
- Ingest heterogeneous data sources:
  - Pitch decks (PDF, PPT, DOCX)
  - GitHub activity (commits, repos, stars, contributions)
  - Product launches (Product Hunt, Hacker News, TechCrunch)
  - Social traction (Twitter/X, LinkedIn)
  - Research papers and patents
  - Interview transcripts (video/audio → text)
  - Accelerator cohort data (Y Combinator, Techstars, etc.)
  - News articles and press mentions

**Technical Specifications:**
- Support file upload (drag-drop, API)
- OCR for scanned documents
- Audio/video transcription pipeline
- Web scraping with rate limiting and ethical boundaries
- Real-time API integrations (GitHub API, Product Hunt API)
- Batch processing for historical data loads

**Acceptance Criteria:**
- [ ] Successfully parse 95%+ of pitch decks automatically
- [ ] GitHub integration fetches data within 5 seconds
- [ ] Audio transcription accuracy >90%
- [ ] Handle 10,000+ documents per day

---

#### 1.2 Deduplication & Entity Resolution
**Priority:** P0

**Requirements:**
- Identify same founder across multiple startups/applications
- Merge duplicate company entries
- Handle name variations, aliases, username changes
- Maintain audit trail of all merges

**Technical Specifications:**
- Fuzzy matching algorithms (Levenshtein distance, phonetic matching)
- Email-based identity resolution
- GitHub username → Real name mapping
- Company domain verification
- Manual review queue for ambiguous cases

**Acceptance Criteria:**
- [ ] 95%+ accuracy in founder deduplication
- [ ] <5% false positive merge rate
- [ ] Support manual override/split capabilities

---

#### 1.3 Data Enrichment & Timestamping
**Priority:** P0

**Requirements:**
- Automatic enrichment from public sources
- Timestamp all data points with source attribution
- Tag data by source reliability (verified, scraped, user-provided)
- Track data freshness and staleness

**Technical Specifications:**
- Integration with data enrichment APIs (Clearbit, Apollo.io, etc.)
- Metadata schema: `{data_point, timestamp, source, confidence_score}`
- Automatic refresh schedules for aging data
- Version control for enriched data

**Acceptance Criteria:**
- [ ] Every data point has timestamp + source
- [ ] Enrichment completes within 2 minutes of ingestion
- [ ] Data freshness indicator visible in UI

---

#### 1.4 Persistent Founder Score
**Priority:** P0

**Requirements:**
- **Unique Feature:** Score follows founder across different startups/applications
- Never resets between ventures
- Tracks **trend** (momentum) not just snapshot
- Historical score trajectory visible
- Transparent score composition

**Technical Specifications:**
- Founder-centric data model (not company-centric)
- Time-series database for score history
- Separate scores for: Technical Ability, Execution, Communication, Vision, Resilience
- Composite algorithm that weights recency and momentum
- Score decay function for inactive periods

**Acceptance Criteria:**
- [ ] Founder score persists across 100% of applications
- [ ] Score history accessible for 10+ year timeframe
- [ ] Momentum indicator (↑↓→) calculated accurately
- [ ] Score breakdown visible with drill-down capability

---

### 2. INTELLIGENCE LAYER (Reasoning Engine)

#### 2.1 Thesis Engine
**Priority:** P0

**Requirements:**
- Configurable investment thesis parameters:
  - Sectors (e.g., AI, FinTech, HealthTech, Climate, etc.)
  - Stage (pre-seed, seed, Series A)
  - Geography (headquarters, target markets)
  - Check size ($50K-$500K range)
  - Ownership targets (5%-20%)
  - Risk appetite (conservative, moderate, aggressive)
- Every recommendation scored against thesis fit
- Support multiple parallel theses

**Technical Specifications:**
- Rules engine with boolean + weighted logic
- Version-controlled thesis configurations
- A/B testing capability for thesis variations
- Thesis fit score (0-100) per opportunity

**Acceptance Criteria:**
- [ ] Non-technical investor can configure thesis in <10 minutes
- [ ] Thesis changes apply to pipeline in real-time
- [ ] Historical opportunities re-scorable against new thesis

---

#### 2.2 Inbound Screening (Fast First-Pass Filter)
**Priority:** P0

**Requirements:**
- Founder applies with **minimal input**: pitch deck + company name
- Automated first-pass filter removes non-viable ideas
- Pass/Fail + explanation within 15 minutes
- **Not** a full evaluation (just gating to reduce noise)

**Screening Criteria (Auto-Evaluated):**
- Market size minimum threshold
- Problem clarity and urgency
- Basic team viability checks
- Red flags: illegal, unethical, saturated markets with no differentiation
- Thesis alignment (preliminary)

**Technical Specifications:**
- LLM-based document analysis (GPT-4, Claude)
- Structured output schema for screening decision
- Confidence score on screening decision
- Human review queue for borderline cases (40-60% confidence)

**Acceptance Criteria:**
- [ ] 90%+ clear passes/fails automated
- [ ] <5% false rejection rate (validated quarterly)
- [ ] Processing time <15 minutes
- [ ] Founder receives clear rejection reasons (when rejected)

---

#### 2.3 Outbound Sourcing (Proactive Discovery)
**Priority:** P0 (Differentiator)

**Requirements:**
- **Continuously scan** for strong founders **before** they fundraise:
  - GitHub: commit frequency, repo stars, contribution quality
  - Product launches: Product Hunt, Hacker News front page
  - Hackathon winners and participants
  - Research papers with commercial potential
  - Patents filed by individuals (not corporations)
  - Accelerator cohorts (YC, Techstars, etc.)
- Trigger **automated outreach** to convert discovery → application
- Outbound and inbound **converge** into same screening funnel

**Technical Specifications:**
- GitHub activity scorer (commit quality > quantity)
- Natural language processing for launch descriptions
- Patent classification and commercial viability scoring
- Automated email sequencing for outreach
- CRM integration for tracking outreach status
- Unsubscribe and compliance management (GDPR, CAN-SPAM)

**Acceptance Criteria:**
- [ ] Scan 1,000+ GitHub profiles daily
- [ ] Identify 10-50 high-potential founders weekly
- [ ] 15%+ conversion rate from outreach → application
- [ ] Zero spam complaints

---

#### 2.4 Multi-Attribute Reasoning (Natural Language Queries)
**Priority:** P1

**Requirements:**
- Support complex natural language queries in a single pass:
  - Example: *"technical founder, Berlin, AI infra, enterprise traction, no prior VC backing, top-tier accelerator"*
- No manual multi-step filtering required
- Results ranked by relevance

**Technical Specifications:**
- Vector database (Pinecone, Weaviate, Qdrant) for semantic search
- Query understanding via LLM
- Structured query generation from natural language
- Result explanation (why each result matched)

**Acceptance Criteria:**
- [ ] 90%+ query accuracy vs. manual filtering
- [ ] Query response time <3 seconds
- [ ] Support 5+ simultaneous query conditions

---

#### 2.5 Multi-Axis Screening (Three Independent Scores)
**Priority:** P0

**Requirements:**
- **Critical Feature:** Three independent, **non-averaged** scores per opportunity:
  1. **Founder Score** (traits, track record, execution ability)
  2. **Market Score** (sizing, competitors, SWAT analysis → Bullish/Neutral/Bearish)
  3. **Idea vs. Market Score** (does idea survive scrutiny? Is team strong enough to pivot?)
- Each axis shows **trend direction** (↑↓→)
- Scores feed back into Memory Layer for persistent Founder Score

**Technical Specifications:**
- Separate evaluation pipelines per axis
- No score averaging or single composite number
- Historical trend calculation (30/60/90 day windows)
- Visual representation: radar chart or triple bar chart
- Score versioning (track how scores change over time)

**Acceptance Criteria:**
- [ ] All three scores visible independently
- [ ] Trend indicators accurate to actual momentum
- [ ] Investor can drill into score components
- [ ] Scores update within 24 hours of new data

---

#### 2.6 Trust Score & Evidence Tracing
**Priority:** P0 (Critical for Decision Quality)

**Requirements:**
- **Every claim** in investment memo traces to source evidence with confidence level:
  - Traction metrics (MRR, ARR, user count) → screenshot, analytics API, bank statement
  - Revenue claims → financial documents
  - Team background → LinkedIn, GitHub, previous company exits
  - Market size → research reports, analyst data
- **Contradictions flagged** before reaching investor
- **Data gaps explicitly disclosed** (never fabricated)
- Red flag indicators for unverifiable claims

**Technical Specifications:**
- Citation management system
- Confidence scoring algorithm (verified > corroborated > claimed)
- Contradiction detection via fact-checking pipeline
- Missing data inventory per memo
- Traffic light system: 🟢 Verified | 🟡 Partial | 🔴 Unverified

**Acceptance Criteria:**
- [ ] 100% of quantitative claims have citations
- [ ] Contradictions detected with 95%+ accuracy
- [ ] Data gaps visible in executive summary
- [ ] Trust Score (0-100) calculated per memo section

---

### 3. EXPERIENCE LAYER (Investor-Facing UX)

#### 3.1 Dashboard (Founder List + Momentum)
**Priority:** P0

**Requirements:**
- Ranked list of founders with visual momentum indicators
- Filterable by stage (Sourced, Screening, Diligence, Decision)
- Sortable by: Founder Score, Market Score, Idea Score, Trust Score, Recency
- Search and natural language query bar
- Quick actions: View Memo, Request More Info, Schedule Call, Pass

**Technical Specifications:**
- Real-time updates (WebSocket or SSE)
- Responsive design (desktop + tablet)
- Data export (CSV, PDF)
- Customizable columns and saved views

**Acceptance Criteria:**
- [ ] Dashboard loads in <2 seconds
- [ ] Supports 1,000+ founders in list
- [ ] No technical support needed for basic use

---

#### 3.2 Investment Memo (Decision-Ready Output)
**Priority:** P0

**Requirements:**
- **Structured sections (required)**:
  1. Executive Summary (1 paragraph)
  2. Company Snapshot (name, sector, stage, location, ask)
  3. Investment Hypotheses (3-5 bullish hypotheses)
  4. Adversarial/Risk View (3-5 bearish points + mitigation)
  5. SWOT Analysis (Strengths, Weaknesses, Opportunities, Threats)
  6. Problem & Product (problem statement, solution, differentiation)
  7. Traction & KPIs (metrics with citations)
  8. Founder Deep Dive (background, skills, red flags)
  9. Market Analysis (TAM/SAM/SOM, competitors, positioning)
  10. Three Independent Scores (Founder, Market, Idea vs. Market)
  11. Trust Score Summary (data quality assessment)
  12. Recommendation (Invest / Pass / Need More Info)

**Technical Specifications:**
- LLM-generated prose with human-in-the-loop editing
- Version history and collaborative editing
- PDF export with branding
- Inline citations with hover-over source preview
- Comment threads per section

**Acceptance Criteria:**
- [ ] Memo generated within 24 hours of screening pass
- [ ] 90%+ investor satisfaction with memo quality
- [ ] <10 minutes reading time for busy investor
- [ ] Print-ready formatting

---

#### 3.3 Adversarial/Risk View
**Priority:** P0

**Requirements:**
- Explicit section challenging the investment case
- Articulates failure modes and worst-case scenarios
- Identifies assumption-heavy components
- Competitive threats and market timing risks

**Technical Specifications:**
- Devil's advocate LLM prompt engineering
- Red team validation of risk assessment
- Risk severity scoring (Low/Medium/High/Critical)

**Acceptance Criteria:**
- [ ] Every memo includes 3-5 substantive risks
- [ ] Risks not generic (tailored to specific opportunity)
- [ ] Investor can add/edit risks

---

#### 3.4 Cold-Start Founder Support
**Priority:** P0 (Mission-Critical Differentiator)

**Requirements:**
- **Explicit design goal:** System must work for founders with:
  - No funding history
  - No GitHub activity
  - No established network
- Use alternate signals:
  - Public footprint (blog posts, Twitter, YouTube)
  - Hackathon participation (even if not winning)
  - Side projects and portfolio sites
  - Community contributions (Stack Overflow, open source issues)
  - Self-taught indicators (online courses, certifications)

**Technical Specifications:**
- Alternate data source connectors
- Lower confidence threshold acceptance (with explicit flag)
- Qualitative assessment rubrics
- Bias detection (ensure not penalizing underrepresented founders)

**Acceptance Criteria:**
- [ ] 30%+ of successful evaluations are cold-start founders
- [ ] System does not default to "pass" on missing GitHub
- [ ] Alternate signals valued equally to traditional signals

---

## Explicit Scope Boundaries

### ✅ In Scope (This Build)
- Sourcing (Inbound + Outbound)
- Screening (First-pass filter)
- Diligence (Memo generation, scoring)
- Decision support (Recommendation output)

### ❌ Out of Scope (Future Stages)
- Portfolio monitoring (post-investment tracking)
- Follow-on investment decisions (Series A, B, etc.)
- Fund operations (legal, compliance, LP reporting)
- Exit planning and liquidity events
- Founder communication platform (deal room)

---

## Technical Stack Recommendations

### Backend
- **Framework:** Python (FastAPI) or Node.js (NestJS)
- **Database:** PostgreSQL (relational) + TimescaleDB (time-series for scores)
- **Vector Database:** Pinecone or Weaviate (semantic search)
- **Queue:** Redis + Bull/BullMQ (async processing)
- **Storage:** AWS S3 or Google Cloud Storage (documents, media)

### AI/ML
- **LLM:** OpenAI GPT-4 / Anthropic Claude 3.5 (memo generation, analysis)
- **Embeddings:** OpenAI text-embedding-3 (semantic search)
- **Document Parsing:** LangChain + Unstructured.io
- **Transcription:** Whisper API (audio/video)

### Frontend
- **Framework:** React or Next.js
- **UI Library:** shadcn/ui or Ant Design
- **State Management:** Zustand or Redux Toolkit
- **Data Visualization:** Recharts or D3.js

### Infrastructure
- **Cloud:** AWS or Google Cloud Platform
- **Orchestration:** Docker + Kubernetes (or AWS ECS/Fargate)
- **CI/CD:** GitHub Actions or GitLab CI
- **Monitoring:** Datadog or New Relic
- **Logging:** ELK Stack or CloudWatch

### Integrations
- **GitHub API:** Official REST/GraphQL API
- **LinkedIn:** Unofficial scraping (ethical boundaries)
- **Product Hunt API:** Official API
- **Email:** SendGrid or AWS SES (outbound outreach)
- **CRM:** HubSpot or Airtable (deal tracking)

---

## Development Phases

### Phase 1: Foundation (Months 1-3)
**Goal:** Core infrastructure + Inbound screening

**Deliverables:**
- Memory Layer MVP (pitch deck ingestion, basic enrichment)
- Persistent Founder Score database
- Inbound screening pipeline (fast filter)
- Basic dashboard (founder list)
- Simple investment memo generation

**Milestone:** Process first 10 real founder applications end-to-end

---

### Phase 2: Intelligence (Months 4-6)
**Goal:** Multi-axis scoring + Trust scoring

**Deliverables:**
- Three independent scoring pipelines (Founder, Market, Idea)
- Trust Score with evidence tracing
- Thesis Engine configuration UI
- Enhanced memo with all required sections
- Adversarial/Risk view

**Milestone:** Deliver first decision-ready memo within 24 hours

---

### Phase 3: Outbound Sourcing (Months 7-9)
**Goal:** Proactive founder discovery

**Deliverables:**
- GitHub activity scanner
- Product Hunt/Hacker News integration
- Automated outreach system
- Outbound → Inbound funnel convergence
- Cold-start founder alternate signals

**Milestone:** Source 50 founders proactively per month

---

### Phase 4: Scale & Optimize (Months 10-12)
**Goal:** Production hardening + Scale to 100s of deals/month

**Deliverables:**
- Multi-attribute natural language search
- Performance optimization (sub-second dashboard)
- Advanced deduplication (95%+ accuracy)
- Investor collaboration features
- Comprehensive analytics and reporting

**Milestone:** Handle 500+ applications/month with <1% error rate

---

## Success Metrics (KPIs)

### System Performance
- ⏱️ Memo generation time: <24 hours (target: 12 hours)
- 🎯 Screening accuracy: >90% (validated by investor feedback)
- 📊 Trust Score accuracy: >95% citation correctness
- 🚀 Dashboard load time: <2 seconds
- 📈 Uptime: 99.9%

### Deal Flow Quality
- 🔍 Outbound conversion rate: >15% (discovery → application)
- ✅ False rejection rate: <5% (founders incorrectly filtered out)
- 🌟 Cold-start founder representation: >30% of pipeline
- 📉 Time to decision: 80% reduction vs. traditional process

### Investor Adoption
- 😊 User satisfaction: >4.5/5 (quarterly survey)
- 🔄 Daily active use: >80% of workdays
- ⚡ Decisions per week: 3x increase vs. manual process
- 💡 Unaided feature discovery: >70% (usable without training)

---

## Risk Management

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM hallucination in memos | High | Critical | Trust Score, human review, citation tracing |
| GitHub API rate limits | Medium | High | Caching, distributed scrapers, paid tier |
| Data quality (garbage in → garbage out) | High | Critical | Multi-source validation, confidence scoring |
| Scalability bottlenecks | Medium | High | Load testing, horizontal scaling, queue-based architecture |

### Business Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Investor distrust of AI decisions | Medium | Critical | Human-in-the-loop, explainability, transparency |
| Bias against underrepresented founders | Medium | Critical | Bias audits, cold-start support, diverse training data |
| Ethical concerns (privacy, outreach) | Low | High | GDPR compliance, opt-out mechanisms, ethical guidelines |
| Competitive moat | Medium | Medium | Proprietary Founder Score, network effects, speed advantage |

---

## Security & Compliance

### Data Protection
- 🔒 Encryption at rest (AES-256) and in transit (TLS 1.3)
- 🛡️ Role-based access control (RBAC)
- 📝 Audit logging for all data access
- 🔑 Multi-factor authentication (MFA)

### Privacy Compliance
- ✅ GDPR compliant (EU data residency if needed)
- ✅ CCPA compliant (California)
- 📧 CAN-SPAM compliant (email outreach)
- 🚫 Right to be forgotten (data deletion)

### Ethical Guidelines
- 🤝 Transparent scoring criteria
- ⚖️ Bias detection and mitigation
- 🎯 Founder consent for data usage
- 📋 Regular ethics audits

---

## Team Requirements

### Core Team (Phase 1)
- **1x Tech Lead / Architect** (full-stack, AI/ML experience)
- **2x Backend Engineers** (Python/Node.js, API design)
- **1x Frontend Engineer** (React, data visualization)
- **1x ML Engineer** (LLM prompt engineering, RAG pipelines)
- **1x Product Manager** (VC domain knowledge)
- **1x QA Engineer** (testing, validation)

### Extended Team (Phase 2+)
- **1x Data Engineer** (ETL pipelines, data quality)
- **1x DevOps Engineer** (infrastructure, scaling)
- **1x UX Designer** (investor experience optimization)
- **Part-time:** Legal/Compliance advisor

---

## Budget Estimate (12-Month MVP)

### Personnel
- Core team (7 FTE × $120K avg) = **$840K**
- Extended team (3 FTE × $120K × 6 months) = **$180K**
- **Subtotal: $1,020K**

### Infrastructure & Tools
- Cloud hosting (AWS/GCP) = **$60K/year**
- LLM API costs (OpenAI/Anthropic) = **$120K/year** (high usage)
- Data enrichment APIs = **$36K/year**
- SaaS tools (monitoring, logging, CRM) = **$24K/year**
- **Subtotal: $240K**

### **Total 12-Month Budget: ~$1.26M**

*(This is a Tier-1 city, experienced team estimate. Adjust for location/seniority.)*

---

## Next Steps

1. **✅ Requirements Review** — Validate this spec with Maschmeyer Group stakeholders
2. **🎨 Design Phase** — Create technical architecture and UX wireframes
3. **🛠️ Technology Evaluation** — Proof-of-concept for LLM memo generation
4. **👥 Team Formation** — Recruit core team (Tech Lead, Engineers, PM)
5. **🏗️ Phase 1 Kickoff** — Sprint planning and development start

---

## Appendix: Key Differentiators

### What Makes The VC Brain Unique?
1. **Persistent Founder Score** — Follows founders across ventures, never resets
2. **Outbound Sourcing** — Finds founders before they start fundraising
3. **Multi-Axis Scoring** — Three independent scores (not averaged)
4. **Trust Score** — Every claim traced to evidence, gaps disclosed
5. **Cold-Start Support** — Designed for founders without networks/history
6. **24-Hour Decision** — From first contact to investment recommendation
7. **Single-Investor Scale** — One person gets organizational-level reach

---

**Document Version:** 1.0  
**Last Updated:** 2026-07-19  
**Status:** Draft for Review  
**Owner:** Development Team

