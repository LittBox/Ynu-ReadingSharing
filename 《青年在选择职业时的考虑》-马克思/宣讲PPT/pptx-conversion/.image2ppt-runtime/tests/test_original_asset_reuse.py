import hashlib
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cli/image2ppt/runtime"))
from validate_pptx import foreground_asset_contract_violations


class OriginalAssetReuseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.page = Path(self.temp.name)
        self.asset = self.page / "original.png"
        self.asset.write_bytes(b"test original image")
        self.manifest = {
            "schema_version": 2,
            "visual_inventory": [{"id": "original", "kind": "foreground-asset", "representation": "user-provided-original", "path": "original.png"}],
            "asset_provenance": [{"path": "original.png", "source": "original.png", "source_type": "user-provided", "user_approved_reuse": True, "approval_note": "全部原样复用（推荐）；范围：全部原始图片和SVG图标（新闻/原文截图、职业插图、方向图标），只重建文字、表格和布局。", "source_sha256": hashlib.sha256(self.asset.read_bytes()).hexdigest()}],
        }

    def check(self, manifest=None):
        return foreground_asset_contract_violations(manifest or self.manifest, self.page)

    def test_explicit_approval_and_unchanged_original_pass(self):
        self.assertEqual([], self.check())

    def test_missing_approval_rejected(self):
        for key in ("user_approved_reuse", "approval_note", "source_sha256"):
            with self.subTest(key=key):
                altered = deepcopy(self.manifest)
                del altered["asset_provenance"][0][key]
                self.assertTrue(self.check(altered))

    def test_changed_source_rejected(self):
        self.asset.write_bytes(b"different")
        self.assertTrue(self.check())

    def test_no_page_directory_rejected(self):
        self.assertTrue(foreground_asset_contract_violations(self.manifest))

    def test_escape_rejected(self):
        self.manifest["asset_provenance"][0]["source"] = "../outside.png"
        self.assertTrue(self.check())

    def test_svg_normalization_requires_both_hashes(self):
        source = self.page / "original.svg"
        source.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        provenance = self.manifest["asset_provenance"][0]
        provenance.update(source="original.svg", normalization="svg-to-png", source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), asset_sha256=hashlib.sha256(self.asset.read_bytes()).hexdigest())
        self.assertEqual([], self.check())
        self.asset.write_bytes(b"changed normalized image")
        self.assertTrue(self.check())

    def test_does_not_relabel_asset_sheet(self):
        self.manifest["visual_inventory"][0]["representation"] = "asset-sheet-separated"
        self.assertTrue(self.check())


if __name__ == "__main__":
    unittest.main()
