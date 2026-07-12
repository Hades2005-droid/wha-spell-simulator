import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.document_ingest import (
    DocumentIngestError,
    load_document,
    load_documents,
    main,
)


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakeReader:
    def __init__(self, _path):
        self.pages = [
            FakePage("Technical recommendation\napi_key=not-a-real-secret"),
            FakePage("Second page"),
        ]


class DocumentIngestTests(unittest.TestCase):
    def test_text_document_is_bounded_and_redacted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.md"
            path.write_text("api_key=not-a-real-secret\n" + ("x" * 40), encoding="utf-8")
            document = load_document(path, max_chars=20)

        self.assertEqual(document.source_type, "text")
        self.assertTrue(document.truncated)
        self.assertNotIn("not-a-real-secret", document.text)
        self.assertIn("[REDACTED]", document.text)

    def test_pdf_is_converted_to_text_without_native_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recommendation.pdf"
            path.write_bytes(b"%PDF-1.4 fake fixture")
            with patch("tools.document_ingest.PdfReader", FakeReader):
                document = load_document(path)

        self.assertEqual(document.source_type, "pdf_text")
        self.assertEqual(document.pages, 2)
        self.assertIn("Technical recommendation", document.text)
        self.assertNotIn("not-a-real-secret", document.text)

    def test_duplicate_documents_are_loaded_once(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.txt"
            path.write_text("hello", encoding="utf-8")
            documents = load_documents([path, path])

        self.assertEqual(len(documents), 1)

    def test_pdf_requires_text_extractor(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "recommendation.pdf"
            path.write_bytes(b"%PDF-1.4 fake fixture")
            with patch("tools.document_ingest.PdfReader", None):
                with self.assertRaises(DocumentIngestError):
                    load_document(path)

    def test_cli_writes_text_only_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "notes.txt"
            output = Path(directory) / "bundle.json"
            source.write_text("Reference text", encoding="utf-8")
            result = main(["--input", str(source), "--output", str(output)])
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertFalse(payload["native_pdf_input"])
        self.assertEqual(payload["documents"][0]["source_type"], "text")


if __name__ == "__main__":
    unittest.main()
