"""Tests for archive confidentiality, determinism and cryptographic integrity."""
import hashlib
import importlib.util
import pathlib
import tempfile
import unittest
import zipfile

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "submission" / "build_master_archive.py"
spec = importlib.util.spec_from_file_location("build_master_archive", SCRIPT)
archive_builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive_builder)


class MasterArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name) / "project"
        self.root.mkdir()
        for filename in archive_builder.ROOT_FILES:
            (self.root / filename).write_text("sample content\n", encoding="utf-8")
        for dirname in archive_builder.DIRECTORIES:
            (self.root / dirname).mkdir()
            (self.root / dirname / "sample.txt").write_text(dirname, encoding="utf-8")
        (self.root / "submission" / "dist").mkdir()
        (self.root / "submission" / "dist" / "stale.zip").write_bytes(b"stale")
        (self.root / "app" / "__pycache__").mkdir()
        (self.root / "app" / "__pycache__" / "secret.pyc").write_bytes(b"stale")

    def test_reproducible_package_and_verified_digest(self):
        archive, checksums = archive_builder.build_archive(self.root)
        first = archive.read_bytes()
        expected = hashlib.sha256(first).hexdigest()
        self.assertEqual(checksums.read_text(), f"{expected}  {archive_builder.ARCHIVE_NAME}\n")
        with zipfile.ZipFile(archive) as zipfile_obj:
            members = zipfile_obj.namelist()
            self.assertIn("nous-intelligence-rooms/MANIFEST_SHA256.txt", members)
            self.assertIn("nous-intelligence-rooms/README.md", members)
            self.assertFalse(any("dist/" in member or "__pycache__" in member for member in members))
            manifest = zipfile_obj.read("nous-intelligence-rooms/MANIFEST_SHA256.txt").decode()
            for line in manifest.splitlines():
                if line.startswith("#"):
                    continue
                digest, member = line.split("  ", 1)
                self.assertEqual(digest, hashlib.sha256(zipfile_obj.read(member)).hexdigest())
        archive_builder.build_archive(self.root)
        self.assertEqual(first, archive.read_bytes())

    def test_environment_secret_is_not_included(self):
        (self.root / ".env").write_text("OPENAI_API_KEY=private\n", encoding="utf-8")
        archive, _ = archive_builder.build_archive(self.root)
        with zipfile.ZipFile(archive) as zipfile_obj:
            self.assertFalse(any(member.endswith("/.env") for member in zipfile_obj.namelist()))

    def test_missing_required_file_is_rejected(self):
        (self.root / "LICENSE").unlink()
        with self.assertRaises(FileNotFoundError):
            archive_builder.build_archive(self.root)

    def test_symlink_is_rejected(self):
        (self.root / "app" / "alias").symlink_to(self.root / "README.md")
        with self.assertRaises(ValueError):
            archive_builder.build_archive(self.root)


if __name__ == "__main__":
    unittest.main()
