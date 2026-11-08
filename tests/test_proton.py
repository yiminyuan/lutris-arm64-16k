import os
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from lutris.exceptions import MissingExecutableError
from lutris.util.wine import proton


class TestGetProtonWinePath(TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.proton_path = self.temp_dir.name
        versions_patcher = patch.object(proton, "get_proton_versions", return_value={"Proton": self.proton_path})
        versions_patcher.start()
        self.addCleanup(versions_patcher.stop)

    def create_wine(self, bin_dir):
        wine_path = os.path.join(self.proton_path, bin_dir, "wine")
        os.makedirs(os.path.dirname(wine_path))
        open(wine_path, "w", encoding="utf-8").close()
        return wine_path

    def get_wine_path(self, machine):
        with patch("platform.machine", return_value=machine):
            return proton.get_proton_wine_path("Proton")

    def test_dist_bin(self):
        wine_path = self.create_wine("dist/bin")
        self.assertEqual(self.get_wine_path("x86_64"), wine_path)

    def test_files_bin(self):
        wine_path = self.create_wine("files/bin")
        self.assertEqual(self.get_wine_path("x86_64"), wine_path)
        self.assertEqual(self.get_wine_path("aarch64"), wine_path)

    def test_files_bin_arm64_on_aarch64(self):
        wine_path = self.create_wine("files/bin-arm64")
        self.assertEqual(self.get_wine_path("aarch64"), wine_path)

    def test_files_bin_arm64_preferred_on_aarch64(self):
        self.create_wine("files/bin")
        wine_path = self.create_wine("files/bin-arm64")
        self.assertEqual(self.get_wine_path("aarch64"), wine_path)

    def test_files_bin_arm64_ignored_on_x86_64(self):
        wine_path = self.create_wine("files/bin")
        self.create_wine("files/bin-arm64")
        self.assertEqual(self.get_wine_path("x86_64"), wine_path)

    def test_files_bin_arm64_only_on_x86_64(self):
        self.create_wine("files/bin-arm64")
        with self.assertRaises(MissingExecutableError):
            self.get_wine_path("x86_64")

    def test_missing_version(self):
        with self.assertRaises(MissingExecutableError):
            proton.get_proton_wine_path("Missing")
