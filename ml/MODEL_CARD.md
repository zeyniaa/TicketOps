# TicketOps baseline model

## Implemented and measured

Word TF-IDF (1–2 grams) and character TF-IDF (3–5 grams), with Logistic Regression. C is selected from 0.5, 1, 2 on development macro-F1. A separate sigmoid calibration uses the calibration split. The final configuration is frozen before held-out test evaluation.

Every prediction requires operator review because the bootstrap dataset is synthetic and has no human review. The calibrated probabilities are not a guarantee of real-world reliability. The deployment manifest records the fitted C, calibration losses, selected development threshold, and dataset version.

Run `python ml/train_baseline.py` to reproduce. Hardware-specific latency is measured, not promised. Exported reports retain their original host, sample count, and date.

## Results from the initial run

The actual values are in `ml/artifacts/evaluation-tfidf-calibrated-v1.json` and the showcase snapshot. Initial calibrated macro-F1 is approximately 0.744 on 320 correlated synthetic rows (64 test families). This is below the design target of 0.80. Do not present the target as an achieved result.

## IndoBERT candidate

`train_indobert.py` and `TicketOps_Training.ipynb` provide Colab fine-tuning, development selection, and temperature scaling. Training is not claimed as completed in this delivery. No fabricated IndoBERT score is shown. The base model is `indobenchmark/indobert-base-p1`; retain its MIT license and model citation. Record its resolved revision for each run.

After development selection, evaluate the frozen candidate with `evaluate_indobert.py`. Transfer the candidate into this project's `ml/artifacts` directory and run `promote_model.py` on the target laptop. Promotion requires >=0.02 development macro-F1 improvement and CPU p95 <=3,000 ms. It retains mandatory operator review.

## Generation

Qwen3 4B through Ollama drafts replies using retrieved policy versions and fictional order facts. The model is not fine-tuned. JSON-schema validation checks shape and allowed references, with additional narrow checks for unsupported transactional claims. These checks do not prove semantic entailment. Human review remains necessary.

The live smoke result is stored in `docs/local-smoke.json`. This is one integration example, not a quality benchmark. A full zero-shot classification comparison is runnable via `benchmark_qwen.py`, and is not shown as completed until its report exists.

## Intended use and limitations

Portfolio research and demonstration only. No automatic customer messages, financial actions, real order integration, or production readiness claim. Memory, language robustness, calibration, and human draft quality need representative evaluation before a real deployment.

Primary model sources:

- https://huggingface.co/indobenchmark/indobert-base-p1
- https://huggingface.co/Qwen/Qwen3-4B
- https://ollama.com/library/qwen3
