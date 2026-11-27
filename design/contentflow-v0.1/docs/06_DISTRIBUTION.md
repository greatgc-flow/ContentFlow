# 06 — Distribution, publishing and platform capabilities

## 1. Mode separation

`EXPORT_ONLY` default: create local package (MP4, SRT, metadata, thumbnail, source/rights manifest, review summary). `APPROVAL_REQUIRED`: prepare intent, user consents to exact destination and visibility then official API if capability permits. `AUTO_PUBLISH`: disabled in v0.x; possible only after separate policy review, explicit bounded standing authorization, platform permission and owner opt-in; never for sensitive categories or where user consent is required per post. No browser automation for restricted posting, no cross-account spam. Exporting does not grant permission to publish; package marks blocked rights/review and only publish-ready export is allowed after gate; draft preview remains private and watermarked/labelled if appropriate.

## 2. Capability registry (as of 2026-11-28)

| Destination | Planned action | Default | Activation condition |
|---|---|---|---|
| YouTube | official Data API upload, status, metadata; Analytics API read | export | OAuth scope/account, terms, explicit privacy, quota, approved intent |
| TikTok | manual export; possible compliant product-level Content Posting API | export | official guidelines explicitly disallow own/team-only utility use; audit, UX consent and app eligibility for broader product |
| Instagram | export; official professional-account content publishing adapter candidate | export | verify current API route, permissions/account type/review and media hosting constraints |
| Facebook | export; Page/authorized Graph API candidate | export | account/Page access and scope review |
| Naver Clip/Blog | export | export | no assumed public posting API; only enable verified official capability |
| X/Threads/LinkedIn | text/video export; official API candidates | export | terms, account/app permissions, price and limits checked |
| WordPress | REST candidate, draft only initially | export | site owner auth and scoped credentials |
| Newsletter | draft export; approved sender API candidate | export | opt-in, sender/domain, unsubscribe, list consent |
| Private/LMS | local package; authorized internal import | export | data boundary and owner approval |

See reference IDs R01–R08, R15. YouTube API revision history states 2026-11-02 reversal of prior unaudited-project private-only upload restriction; explicitly set `private` in any initial real upload regardless of defaults, recheck endpoint and account requirements. Public upload needs separate approval. This is not permission to skip OAuth/security/terms. TikTok's Direct Post rules are stricter; no self-use workaround. Eligibility, public publishing capability and actual revenue are distinct state machines. Official API metrics/limits can change; versioned rule records include effective dates and account-specific overrides only from trustworthy evidence.

## 3. Publication transaction

1. Validate export hash, rights expiry and gate; create immutable intent with content rev, media/metadata hashes, platform, account ID, visibility, scheduled instant, disclosure and policy revision. Duplicate same content/account/variant is blocked unless explicit replacement workflow.
2. Show preview, title, target account, cost and exact visibility; owner approves action, expiry and intent digest. No implied permission from prior content approval. Recheck account ownership and auth immediately before side effect; scheduled operation revalidates rules/rights/approval.
3. Insert unique intent, audit event and outbox transactionally. Worker claims lease, revalidates and records attempt before network. If provider supports idempotency, pass operation key; resumable upload stores encrypted session metadata with expiry. On successful receipt store remote ID/status and timestamps. For asynchronous processing, poll within allowed rate limit and mark status based on actual response; never infer public visibility.
4. Network timeout after send → `REMOTE_UNKNOWN`; freeze retries. Reconcile through provider lookup or account dashboard/user confirmation. If no safe lookup, explicit human resolution; no blind retry or auto-delete. Remote duplicate remediation requires owner approval. Confirm remote status, correct metadata and privacy; update manual receipts with evidence. `PUBLISHED` only after remote verification (manual attestation distinguished). Failed upload and succeeded render separate.

Publication states `DRAFT -> PREPARED -> APPROVED -> SUBMITTING -> PROCESSING | REMOTE_UNKNOWN | FAILED -> PUBLISHED | FAILED`; PROCESSING may become REMOTE_UNKNOWN; reconciliation can transition unknown to verified result, or terminal `ABANDONED` without claiming absence. Explicit `CANCEL_REQUESTED` for unresolved remote; local cancel before submit -> CANCELED. Post-publication `CORRECTION_PENDING -> CORRECTED | RETRACTED` only with confirmed action. Remote deletion/visibility changes separate approved actions. No irreversible external action implied by local delete. Schedule respects DST/UTC; deadline or stale approval blocks execution.

## 4. Platform metadata and policy changes

Each destination profile: video dimensions/length/size, supported codecs, caption format, safe areas, title/description length, audience classification, AI disclosure, paid promotion, music rights, publish permissions, API cost/quota, metrics definitions, policy revision/expiry. Rules not hardcoded in Core; fresh official source and account checks. Missing/expired profile defaults export-only or blocks publish. Developer terms can restrict storing API data; YouTube rules require delete/refresh many categories after 30 days, with specific exceptions (R08). Apply per data category and consent; do not assume all raw data permanent. User consent withdrawal schedules purge/refresh disable. For manual export, provide disclosure checklist, copyright attribution, suggested caption and account-specific instructions, not upload bypass.

## 5. Correction loop

Changed source, revoked asset rights, complaint, strike or policy revision → dependency query → mark affected publications/variants as review required → freeze new use → owner reviews correction, private/unlist or takedown; publish approved action via official API or manual checklist; record receipt and evidence. Preserve lawful audit history with retention restrictions. Do not automatically re-upload disputed content. Channel-level similarity/spam review and rate caps configurable. No engagement automation, fake subscribers or purchase of traffic.
