# Reproduction

1. python Scripts/prepare_cutscene_full_review.py
2. pwsh -NoProfile -File Scripts/export_cutscene_full_review.ps1
3. python Scripts/audit_cutscene_full_review.py

Requires existing local audited archives, catalog, font, Converse and original scene sequence XML. Outputs: Build/CutsceneFullReview-20260914. Human review adjudications are recorded in README-KO.md and summary.json. No game writes or publishing.
