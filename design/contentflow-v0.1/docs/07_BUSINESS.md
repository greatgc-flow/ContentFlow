# 07 — Monetization, experimentation and analytics

## 1. Revenue capability model

Revenue is a separate bounded context. Content can map to one or more campaigns/offers with declared disclosures. Route types: `AD, PLATFORM_REWARD, AFFILIATE_CPA, AFFILIATE_CPS, SPONSORSHIP, DONATION, MEMBERSHIP, DIGITAL_GOOD, COURSE, LICENSE, SERVICE, LEAD, SAAS, PHYSICAL_GOOD`. Each route has owner/account, eligibility status (`UNKNOWN, INELIGIBLE, ELIGIBLE, ACTIVE, SUSPENDED`), region, effective policy, contract terms, price/commission, currency, returns and payout schedule. No system auto-signs contracts or assumes eligibility. Account-specific proof required. For SaaS/payment, design ledger and webhook contract now; real integration P3 only after security, tax, refund and consumer compliance.

| Route | Measure / evidence | Typical caveat |
|---|---|---|
| Ads/rewards | qualified metric + statement, estimate vs settlement | eligibility, different denominators |
| CPA/CPS | approved action, order ID, rate, refund | canceled/denied not earned |
| Sponsorship | contract milestones, invoice/receipt | obligations, disclosure, rights |
| Subscription | active paid subscriber, MRR, churn | free trial excluded, refunds |
| Product/course/license | order, tax, platform fee, refund | inventory/entitlement separate |
| Service/lead | qualified lead, accepted invoice/payment | lead ≠ revenue |
| Donation | platform receipt, fee, payout | no entitlement assumed |
| SaaS/API | contracted units/plan, metered bill | data rights, support cost |

YouTube effective date rules are external configuration (R01): new entry criteria change 2027-02-01; do not use thresholds to predict approval. Track Shorts qualified-view maintenance separately from other YPP earning types. Revenue observation may be unavailable even when public views exist. No universal Instagram/X/TikTok RPM, no fixed promised earnings. Scenario assumptions stored with date/source and explicitly labeled estimates, never posted as actual income.

## 2. Metrics and ledger

Metric observation stores platform/account/content/remote ID, metric name, semantic definition/revision, start/end inclusive convention, timezone, dimensions, fetched_at, state (`OBSERVED, ESTIMATED, UNAVAILABLE, SUPPRESSED`), nullable value, units/source and retention. No comparison between public views, engaged views, qualified views, unique viewers, impressions without semantic alignment. YouTube Analytics includes views, engagedViews, estimatedRevenue; estimated revenue can adjust (R07). Store authorized data per provider terms (R08). No mixing denominators. For missing metrics show null and reason, not zero. Imports validate CSV mapping and provenance, dedup external ID/time/metric dimensions, handle restatements with revisions. Use platform account timezone for source reports and UTC interval normalization. Avoid joining identifiable cross-platform users.

Ledger event append-only with external event key, type `ESTIMATE, EARNED, ADJUSTMENT, REFUND, FEE, TAX_WITHHELD, PAYOUT, COST`, source, amount minor units, currency, settlement group, date, campaign, content allocation optional, correction_of. Explicit sign convention: revenue positive, fees/refunds/cost negative, payout is cash transfer not new revenue; display estimated and settled separately, reconcile adjustment rather than overwrite. Don't double count estimate and earned, or gross and net from same statement. Keep currency groups until FX conversion with explicit date/source/decimal rate; rounding half-even per aggregate unless provider specifies. Not accounting/tax software. CSV export supports manual accountant review. Webhooks future: verify signature/raw body/timestamp, replay prevention unique event ID, out-of-order corrections, unknown account rejection; no secrets in logs.

### Formulas

- Scenario ad revenue = eligible qualified views / 1,000 × assumed RPM; if eligibility unknown show conditional scenario, not forecast. RPM actual = recognized revenue / matching view count × 1,000; denominator 0 → null.
- Affiliate scenario = clicks × conversion rate × approval rate × net commission/order; refunds reduce settled values.
- Contribution margin = settled recognized revenue − attributable variable production/distribution/payment costs (do not subtract already netted fees twice). Operating result subtract shared fixed costs separately. Labor time tracked and optional shadow hourly cost reported separately, not double counted.
- CAC = acquisition cost / newly acquired paying customers when trackable. MRR = normalized recurring contract value excluding nonrecurring charges, free trial, refunds as policy. Churn = lost paying customers / beginning cohort; LTV estimate labeled assumptions. ROI = contribution after cost / cost, zero cost → null. Cost per accepted asset excludes rejected from numerator? No: include failed/rejected spend in batch cost, divide by accepted count. Time per accepted asset includes review and failure recovery.

### Synthetic economics (not market estimates)

Scenario: 100,000 qualified views at KRW 300/1,000 → KRW 30,000; 500 clicks × 4% × 80% approval × KRW 2,000 → KRW 32,000; 10 digital products × KRW 19,000 → KRW 190,000 gross before fee/refund; production cost KRW 45,000. Report separate routes, assumed eligible, no claim of actual earnings. Compare with zero-revenue case, higher-cost cloud case and failed production. Data model includes scenarios low/base/high, inputs explicit, no hidden defaults. Break-even qualified views = remaining cost / RPM × 1,000 when RPM >0; otherwise undefined.

## 3. Campaign and experiment design

Each brief identifies one audience and one primary outcome (qualified attention, signups, sales, retention, lead). Define experiment hypothesis, variants, assignment (random only where supported/ethical), window, sample criteria and confounders (topic, audience, time, channel). Track thumbnails/titles via supported platform tools, do not repeatedly upload near-duplicates. UTM only for owner-controlled destinations and permitted affiliate links; disclose affiliate/sponsorship; avoid cross-platform fingerprinting. First-touch/last-touch models clearly labeled, one conversion credited once per chosen model, direct/unattributed bucket. No claim of causal lift without valid design. Collect only necessary aggregate metrics. Compare production effort, rights risk and retention; owner chooses niche after real pilot.

## 4. Dashboard and reports

Pipeline funnel: discovered → accepted brief → render pass → approved export → verified published → eligible metrics → conversion → settled revenue. Cohort by project, niche, format, locale, destination; segment time window and metric version. Display planned/actual spend, unknown charge exposure, margin and cash payouts separately. Compare direct product vs audience advertising without assuming rate. Recommendations are advisory, never automatically change publishing volume or budget. Alert when cost cap, rights expiry, source correction, missing metrics/settlement or abnormal duplicate. CSV + JSON + human report. No external accounts or revenue activity in pre-TDD package.
