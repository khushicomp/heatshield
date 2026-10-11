import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from scripts.package_frontend import package_frontend, verify_zip_paths


class FrontendPackagingTests(unittest.TestCase):
    def setUp(self):
        output = Path(__file__).resolve().parents[1] / 'outputs'
        output.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=output)
        self.root = Path(self.temporary.name)
        self.dist = self.root / 'dist'
        (self.dist / 'assets').mkdir(parents=True)
        (self.dist / 'index.html').write_text('<script src="/assets/main.js"></script><link rel="stylesheet" href="/assets/main.css">')
        (self.dist / 'assets/main.js').write_text('console.log("fixture")')
        (self.dist / 'assets/main.css').write_text('body{}')

    def tearDown(self):
        self.temporary.cleanup()

    def test_portable_headers_root_inventory_and_exact_bytes(self):
        zip_path = package_frontend(self.dist, self.root / 'frontend.zip')
        verify_zip_paths(zip_path)
        with ZipFile(zip_path) as archive:
            self.assertEqual(set(archive.namelist()), {'index.html', 'assets/main.js', 'assets/main.css'})
            for name in archive.namelist():
                self.assertEqual(archive.read(name), (self.dist / name).read_bytes())

    def test_rejects_windows_local_header_even_with_correct_directory_listing(self):
        zip_path = self.root / 'broken.zip'
        with ZipFile(zip_path, 'w') as archive:
            archive.writestr('assets/main.js', 'fixture')
        raw = bytearray(zip_path.read_bytes())
        raw[30:44] = b'assets\\main.js'
        zip_path.write_bytes(raw)
        with ZipFile(zip_path) as archive:
            self.assertEqual(archive.namelist(), ['assets/main.js'])
        with self.assertRaisesRegex(ValueError, 'Nonportable ZIP path'):
            verify_zip_paths(zip_path)

    def test_missing_asset_and_nested_zip_output_fail(self):
        with self.assertRaises(ValueError):
            package_frontend(self.dist, self.dist / 'inside.zip')
        (self.dist / 'assets/main.css').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing or empty'):
            package_frontend(self.dist, self.root / 'frontend.zip')
