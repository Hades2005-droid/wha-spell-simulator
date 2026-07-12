import tempfile
import unittest
from pathlib import Path

from tools.eden_ingest import EdenMetadataCatalog, EdenPolicy, classify_path


class EdenIngestTests(unittest.TestCase):
    def test_classifies_land_astro_and_data_lanes(self):
        self.assertEqual(classify_path("land/region-map.json"), "land")
        self.assertEqual(classify_path("lunar/astro-node.json"), "astro_node")
        self.assertEqual(classify_path("inbox/notes.json"), "data")

    def test_absorbs_metadata_without_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            land = root / "land"
            astro = land / "astro"
            astro.mkdir(parents=True)
            (land / "region-map.json").write_text('{"terrain":"local"}', encoding="utf-8")
            (astro / "moon-node.json").write_text('{"target":18}', encoding="utf-8")

            payload = EdenMetadataCatalog(
                policy=EdenPolicy(max_depth=2, allowed_roots=(root,))
            ).absorb([root]).snapshot()

        self.assertEqual(payload["accepted"], 2)
        self.assertEqual(payload["counts"], {"land": 1, "astro_node": 1, "data": 0})
        self.assertFalse(payload["controls"]["payloads_stored"])
        self.assertTrue(payload["lunar"]["moon_18"]["sealed"])
        self.assertNotIn("terrain", payload["records"][0])

    def test_rejects_remote_secret_and_outside_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            safe = root / "safe.json"
            safe.write_text("safe", encoding="utf-8")
            secret = root / "api_key.json"
            secret.write_text("do-not-ingest", encoding="utf-8")
            outside = Path(directory).parent / f"{root.name}-outside.json"
            outside.write_text("outside", encoding="utf-8")
            try:
                payload = EdenMetadataCatalog(
                    policy=EdenPolicy(allowed_roots=(root,))
                ).absorb(
                    [
                        safe,
                        secret,
                        outside,
                        "https://example.invalid/data.json",
                    ]
                ).snapshot()
            finally:
                outside.unlink()

        self.assertEqual(payload["accepted"], 1)
        reasons = {entry["reason"] for entry in payload["rejections"]}
        self.assertIn("secret_named_path_rejected", reasons)
        self.assertIn("outside_allowlisted_root", reasons)
        self.assertIn("remote_source_rejected", reasons)
        self.assertTrue(
            all("[REMOTE" not in record["path"] for record in payload["records"])
        )

    def test_enforces_depth_entry_and_byte_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "one" / "two" / "three"
            nested.mkdir(parents=True)
            (root / "first.json").write_text("1", encoding="utf-8")
            (root / "second.json").write_text("2", encoding="utf-8")
            (nested / "too-deep.json").write_text("3", encoding="utf-8")
            payload = EdenMetadataCatalog(
                policy=EdenPolicy(
                    max_depth=2,
                    max_entries=1,
                    max_bytes=1,
                    max_record_bytes=1,
                )
            ).absorb([root]).snapshot()

        self.assertEqual(payload["accepted"], 1)
        self.assertLessEqual(payload["bytes"], 1)
        reasons = {entry["reason"] for entry in payload["rejections"]}
        self.assertTrue(
            reasons.intersection(
                {
                    "entry_limit_exceeded",
                    "total_byte_limit_exceeded",
                    "depth_limit_exceeded",
                }
            )
        )


if __name__ == "__main__":
    unittest.main()
