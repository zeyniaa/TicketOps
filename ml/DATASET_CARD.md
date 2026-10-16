# TicketOps Synthetic Bootstrap v1

## Provenance

All texts and labels are fictional and authored by an AI coding agent. None are customer records and none have been reviewed by a human. A generated label is a reference label for this bootstrap experiment, not verified ground truth. The software and original synthetic material are provided under the repository MIT license.

## Composition

Eight categories: account, damaged product, wrong product, other, cancellation/change before shipment, payment, returns/refunds, and delivery status. Indonesian texts include some informal language. Coverage of dialect, natural typos, code switching, and genuinely ambiguous complaints is limited.

| Split | Rows | Distinct scenario families |
|---|---:|---:|
| Train | 1,600 | 80 |
| Development | 200 | 40 |
| Calibration | 200 | 40 |
| Test | 320 | 64 |

`seed_data.py` owns distinct scenario sentences for each split. `build_dataset.py` assigns families before augmentation and creates prefix/suffix surface variants. This prevents exact family reuse between splits; it does not prove semantic independence. Similar topics across splits are intentional.

The 320 test rows contain only 64 independent scenario families. Do not compute naive confidence intervals as though every row were independent. Bootstrap by family when reporting uncertainty. The counts match the planned volume, but the provenance and variety do NOT replace the planned human-authored evaluation set.

## Annotation policy

Single primary intent. Prefer the explicit desired outcome. Cancellation includes pre-shipment changes. A report of damaged or mismatched goods retains its product issue category even when the person also mentions return; a generic return-process question is `retur_refund`. Unclear or out-of-scope cases are `lainnya`. This distinction needs human annotation review before any use with real support cases.

## Before stronger portfolio claims

Replace dev/calibration/test with independently written, human-reviewed examples, preserve family IDs, collect permission for any real records, mask identifiers, and record review status. Review contradictory and multi-intent cases with a written rubric. Freeze the test set before changing the model or prompt. Publish class and family counts, not only aggregate accuracy.

Corrections made in the application are stored as feedback candidates; they are never automatically treated as verified labels or used for online retraining.
