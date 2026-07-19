import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.q24_fable5_master_ingest_install import (
    FILE_MAP,
    install_q24,
    load_slim,
    verify_digest,
)


ROOT = Path(__file__).resolve().parents[1]
SLIM = ROOT / "shadow_garden_handoff" / "bridges" / "q24_fable5_master_ingest.slim.json"


class Q24Fable5MasterIngestInstallTests(unittest.TestCase):
    def test_slim_pointer_parses(self):
        slim = load_slim(SLIM)
        self.assertEqual(
            slim["format"],
            "shadow_garden.q24_fable5_master_ingest_digest.slim.v1",
        )
        self.assertTrue(slim["local_only"])

    def test_verify_digest_matches_shadow_garden(self):
        slim = load_slim(SLIM)
        digest = verify_digest(slim)
        self.assertTrue(digest["ok"], digest.get("detail"))

    def test_install_copies_expected_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            import_root = Path(tmp) / "import"
            dest = Path(tmp) / "q24"
            for rel_src, rel_dest in FILE_MAP:
                src = import_root / rel_src
                src.parent.mkdir(parents=True, exist_ok=True)
                src.write_text(f"fixture:{rel_src}", encoding="utf-8")

            result = install_q24(import_root, dest)
            self.assertTrue(result["ok"])
            self.assertEqual(result["files_copied"], len(FILE_MAP))
            self.assertTrue((dest / "autoload/GameSession.gd").is_file())
            self.assertTrue((dest / "canon/q24_canonical.yaml").is_file())


if __name__ == "__main__":
    unittest.main()
