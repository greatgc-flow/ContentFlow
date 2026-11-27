# Synthetic contract fixtures

All JSON objects use fixture_only=true. Artifact hashes/signature/approval/receipt values are placeholders for design shape, not cryptographic proofs, executable payloads or real authorization. Files `*.invalid.json` must fail structural schema validation. `*.semantic-negative.json` deliberately pass structural validation but violate cross-field/cross-object rules; production admission must reject them. `wrong-echo` must be compared to `cf.request.json`. No actual package, archive, model, secret or executable is present. Structural validation is not TDD.
