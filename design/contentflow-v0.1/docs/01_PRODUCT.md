# 01 — Product requirements and scope

## 1. Mission and success

Convert authorized inputs into useful original multimedia and measure their business outcomes. Automate mechanical work, not editorial responsibility. Support a person experimenting with several revenue models without assuming an existing audience, niche, monetization entitlement, GPU size, or subscription allowance. A channel that earns no ad revenue can still test direct product demand.

Primary persona: solo technical operator on Windows, optionally WSL/Linux, Korean and English. Secondary personas: creator, researcher, agency, enterprise training owner. One local workspace first; multiple isolated channels/projects second; hosted multi-tenant product only after a separate security and legal gate. Design for one source packet → multiple distinct content variants, not near-identical mass distribution.

### Success measurements

- Offline MVP: from fixture to an original short video and article, with evidence and rights ledger, approval and export, repeatable job recovery; no credentials or network required. Fake media paths may be used in unit tests only, not as an accepted real render.
- Human pilot: two independently selected niches, 3–5 original briefs per niche; time and cost logged, human quality review. No automatic public posting. Compare measured results rather than promise income.
- Economic signal: actual contribution margin and creator time per accepted asset; retention, click, conversion, and settled revenue. Unknown values remain null. No revenue guarantee.

## 2. Profiles (orthogonal axes)

A workspace can contain multiple projects. Each project sets a versioned editorial charter, allowed source scopes, target audiences, language, destinations, revenue routes, review rules, budget, visual style and permitted providers. Content profiles are declarative data, not special branches in Core.

| Profile | Inputs | Original value | Outputs | Possible revenue |
|---|---|---|---|---|
| TECH | releases, docs, own benchmark | reproduce, compare, explain | tutorial, short, article, repo link | ads, affiliate, software, support |
| DATA | official statistical series, public data | normalize, calculate, chart and limitations | explainer, chart, newsletter | ads, paid reports, lead |
| EDUCATION | authored syllabus, licensed sources | worked example, practice, pedagogy | lessons, quiz, long/short | course, membership |
| REVIEW | product specs, own test notes | comparison method and tradeoffs | video, comparison table | affiliate, sponsorship |
| NEWS_CONTEXT | official statement, independent reporting | timeline and analysis, not reading articles | article, explainer | ads, subscriptions |
| STORY | original script, licensed art | original plot and performance | narrated video, audio | ads, licensing |
| BUSINESS_DOC | authorized internal manual | training scenario, step demonstration | private training, subtitles | B2B production |
| RESEARCH | paper metadata, authorized full text | synthesis with uncertainty | explainer, report, newsletter | paid research, consulting |
| OWN_MEDIA | rights-owned video/audio | select coherent segments and context | short clips, chapters, blog | audience funnel |

Profile risk rules: health/legal/financial/politics, minors, identifiable people, crisis news and safety-critical instruction require specialized human review; disable high-risk automated publication. No scraping paywalls/private data, impersonation, vote or engagement manipulation, deceptive endorsements, unauthorized voices. Private/enterprise documents never leave local trust boundary without explicit permission and provider policy check. Source of truth is not equivalent to redistribution permission.

### Revenue routes (can be combined)

Advertising (qualified views/impressions), platform incentives, sponsorship (contract/delivery), affiliate CPA/CPS (approved conversions), fan support, membership, digital goods, courses, asset licensing, service/lead generation, SaaS/API, physical goods referral/own margin. Track platform eligibility separately from the right to publish. The engine prepares campaigns and records attributable events; it does not autonomously enter contracts, spend money, make tax filings, issue refunds, or open accounts.

### Output profiles

- P0: evidence brief Markdown/JSON, article Markdown, vertical 1080x1920 MP4 with separate SRT and preview, thumbnail, metadata and manifest.
- P1: horizontal 1920x1080, 1:1/4:5 variants, long-form chapters, cards, newsletter, own-video clipping, multilingual dubs/subtitles.
- P2: avatar, image-to-video, generative clips, interactive HTML, course package, platform adapters, revenue dashboard; separate commercial entitlement checks.
- User-defined sizes and durations are capabilities of an adapter; published platform constraints are versioned rules. A 65–90 s vertical preset is not automatically eligible for all platform rewards.

## 3. Priorities and non-goals

P0 = must work offline, smallest viable vertical slice. P1 = optional local/hybrid production and authorized channels. P2 = experiments/advanced services; disabled unless evidence of demand. P3 = SaaS multitenancy and payment integration, after threat/legal review. All stages are designed now; not all implemented now.

Non-goals: generic web browser automation to bypass account restrictions; bulk engagement; guaranteed revenue or monetization; copying editorial articles into voiceover; fully autonomous high-risk advice; universal DRM bypass; collection of private platform transcripts; automatically logging in to consumer AI UI; account sharing; storing third-party API data forever; training on confidential content; replacing professional legal/accounting judgment.

## 4. User journeys

Owner creates project with no paid access → imports offline document or public feed → candidate brief → source/evidence review → author adds original insight → selects content variant → budget estimate → generates assets → checks rights and facts → renders → previews and approves export → manual upload or separately approved authorized publisher → imports metrics and reconciles revenue → compares experiments. Owner may stop/resume/edit/reject/retire/retract any step. Editing changes immutable revisions and invalidates downstream approvals. A project can remain purely private and never publish.

## 5. Product defaults

Korean UI and English engineering docs; ko-KR/en-US presets; local timezone Asia/Seoul for reporting, UTC storage. Export-only, zero external spend, no external network by default in initial profile. Optional pilot envelope KRW 50,000/month requires explicit owner opt-in, not pre-authorized. Single operator, one GPU slot, no hidden provider fallback, no auto-update of providers during run. Defaults configurable and validated. No real data or accounts are required for TDD.

## 6. Portable-first product requirement

P0 Windows x64 portable Lite and Linux archive are release targets; P1 optional Studio/GPU packs, P2 installed/remote worker, P3 hosted. No admin or global interpreter assumption; clean-host offline test required before claiming portability. See 14 for prerequisites, modes, data movement and constraints.
