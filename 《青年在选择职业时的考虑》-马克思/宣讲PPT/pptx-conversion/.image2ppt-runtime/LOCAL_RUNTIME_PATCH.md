# Task-local original asset reuse exception

The user answered **“全部原样复用（推荐）”** to reuse all original HTML images and SVG icons (news/excerpt screenshots, career illustrations, direction icons), rebuilding only text, tables and layout. This copy implements that explicit task scope without changing the installed skill.

`visual_inventory` can label these foreground visuals `representation: user-provided-original`. Matching provenance must truthfully use `source_type: user-provided`, `user_approved_reuse: true`, a nonempty approval note quoting the user and scope, and `source_sha256` matching the original file inside the owning page. The placed asset must match the same hash. The only permitted format normalization is `normalization: svg-to-png`: its original SVG must match `source_sha256`, and the placed PNG must match a separate `asset_sha256`. Visual fidelity remains subject to rendered page and final QA.

The validator receives the owning page directory for both page and deck validation. Missing approval, missing hashes, changed bytes, unknown normalization and path escapes fail. Existing foreground separation contracts, full-slide image restrictions, build/finalize lifecycle, note preservation and rendered review gates remain unchanged. Source screenshots used for input normalization are not editable final output.

Changed files: `cli/image2ppt/runtime/validate_pptx.py`, `schemas/page-manifest-v2.schema.json`. Regression coverage: `tests/test_original_asset_reuse.py`; existing quality-contract tests also run.
