# Offline signed Engram pairing

The local adapter serves the frozen v1 TEST_ONLY health, checkpoint and restore operations. It binds the request to the host-supplied installation, generation, plan and workspace identities, verifies the requested effect scope and deadline, and stays inside the fixed ContentFlow slot. Health reads directory state. Checkpoint and restore require explicit fixture authority. Existing targets return UNKNOWN / RECONCILE. Restore projects current content and pending-effect evidence without acquiring execution authority.

## Reproduce

From this repository, build the dependency-free wheel using reviewed local build tools with package-index access disabled. From the same checkout, run:

```sh
python -B -m pip wheel --no-index --no-build-isolation --no-deps --wheel-dir build-wheel .
python -B tools/probe_signed_engram.py --engram /path/to/engram-checkout \
  --wheel /path/to/built-wheel.whl --wheel-sha256 REVIEWED_WHEEL_SHA256 \
  --openssl /absolute/path/to/openssl
```

The two product trees remain independent. The command uses Engram's development fixture APIs only during pairing. In scratch it creates an ephemeral Ed25519 signer, verifies the staged release and runs the installed wheel as a child with an exact local interpreter. It verifies a health receipt, writes and reopens a signed checkpoint, tests duplicate reconciliation, retires one source in the live ledger, restores a review, interrupts a signed update, rolls it back, and repeats the brief after renaming the system root. The Linux run occurred in an isolated network namespace. The bundle is transient. The probe requires a local trusted OpenSSL installation and a caller-reviewed wheel hash.

## TDD and limits

Adapter RED tests initially failed at the missing module. GREEN accepted exact health, checkpoint and restore exchanges, rejected changed identity and duplicate JSON keys, and returned reconciliation for a repeated effect. The paired command initially failed at the missing probe. The successful paired run used wheel SHA-256 `3326b071b5ef832692face9739be34a55dd770550344873f291502a3a61e0a1d`. It calculated 25% from the installed wheel, excluded the retired source, preserved UNKNOWN in the local review, and executed the previous verified release after rollback and rename. The independent CPU media and workspace recovery receipts remain applicable to their individual scopes.

This proof uses a disposable fixture signer and a same-volume move. Production key approval and revocation, redistribution SBOM and licenses, standard-user Windows cross-volume rebuild, lifetime-managed uninstall and the complete migration acceptance are separate gates. The frozen v0.3 requirement catalogs retain their original bytes.
