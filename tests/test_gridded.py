import argparse
import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from weathernext_download import gridded

try:
    import numpy as np
    import xarray as xr
    import dask.diagnostics  # noqa: F401
    import zarr  # noqa: F401
    import gcsfs  # noqa: F401

    GRIDDED_LIBRARIES_AVAILABLE = True
except ImportError:
    GRIDDED_LIBRARIES_AVAILABLE = False

SKIP_REASON = "xarray, dask[array], zarr, and gcsfs are required for these tests"


class ParseYearsTests(unittest.TestCase):
    def test_single_year(self):
        self.assertEqual(gridded.parse_years("2022"), (2022,))

    def test_multiple_years_preserve_order_and_dedupe(self):
        self.assertEqual(gridded.parse_years("2023, 2022, 2023"), (2023, 2022))

    def test_rejects_unsupported_year(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            gridded.parse_years("2025")

    def test_rejects_empty_value(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            gridded.parse_years("")


class VariableSpecTests(unittest.TestCase):
    def test_surface_alias(self):
        self.assertEqual(gridded.variable_spec("sst"), ("sea_surface_temperature", None))

    def test_pressure_level_alias(self):
        self.assertEqual(gridded.variable_spec("z300"), ("geopotential", 300))

    def test_rejects_unsupported_level(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            gridded.variable_spec("z999")

    def test_rejects_missing_level(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            gridded.variable_spec("z")

    def test_rejects_unknown_alias(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            gridded.variable_spec("bogus")


class ParseVariablesTests(unittest.TestCase):
    def test_dedupes_case_insensitively_preserving_first_order(self):
        self.assertEqual(gridded.parse_variables("SST,sst,msl"), ("sst", "msl"))

    def test_propagates_invalid_alias_error(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            gridded.parse_variables("sst,bogus")


class MissingLibrariesTests(unittest.TestCase):
    def test_reports_all_missing_libraries_with_quoted_install_command(self):
        args = argparse.Namespace(output_dir=None, year=None, variables=("sst",))

        def fake_import_module(name):
            raise ImportError(f"no module named {name}")

        stderr = io.StringIO()
        with mock.patch.object(gridded.importlib, "import_module", side_effect=fake_import_module):
            with contextlib.redirect_stderr(stderr):
                result = gridded.run(args)

        self.assertEqual(result, 1)
        message = stderr.getvalue()
        self.assertIn("xarray", message)
        self.assertIn("'dask[array]'", message)
        self.assertIn("zarr", message)
        self.assertIn("gcsfs", message)

    @unittest.skipUnless(GRIDDED_LIBRARIES_AVAILABLE, SKIP_REASON)
    def test_reports_only_the_libraries_that_are_missing(self):
        import importlib as importlib_module

        args = argparse.Namespace(output_dir=None, year=None, variables=("sst",))
        real_import_module = importlib_module.import_module

        def fake_import_module(name):
            if name == "zarr":
                raise ImportError("no module named zarr")
            return real_import_module(name)

        stderr = io.StringIO()
        with mock.patch.object(gridded.importlib, "import_module", side_effect=fake_import_module):
            with contextlib.redirect_stderr(stderr):
                result = gridded.run(args)

        self.assertEqual(result, 1)
        message = stderr.getvalue()
        self.assertIn("Missing libraries for --gridded: zarr.", message)
        self.assertNotIn("xarray,", message)


@unittest.skipUnless(GRIDDED_LIBRARIES_AVAILABLE, SKIP_REASON)
class SelectVariableTests(unittest.TestCase):
    def setUp(self):
        self.dataset = xr.Dataset(
            {
                "sea_surface_temperature": (("time", "lat", "lon"), np.zeros((2, 3, 4))),
                "geopotential": (("time", "level", "lat", "lon"), np.zeros((2, 2, 3, 4))),
            },
            coords={
                "time": np.arange(2),
                "level": [300, 500],
                "lat": np.linspace(-90, 90, 3),
                "lon": np.linspace(0, 270, 4),
            },
        )

    def test_surface_variable_keeps_name(self):
        selected = gridded.select_variable(self.dataset, "sst")
        self.assertIn("sea_surface_temperature", selected.variables)
        self.assertNotIn("level", selected.dims)

    def test_pressure_level_variable_is_selected_and_renamed(self):
        selected = gridded.select_variable(self.dataset, "z300")
        self.assertIn("geopotential_300hPa", selected.variables)
        self.assertNotIn("geopotential", selected.variables)
        self.assertNotIn("level", selected.dims)


@unittest.skipUnless(GRIDDED_LIBRARIES_AVAILABLE, SKIP_REASON)
class RunLayoutTests(unittest.TestCase):
    """Exercise run() against a synthetic in-memory dataset instead of the network."""

    def _fake_dataset(self):
        return xr.Dataset(
            {
                "sea_surface_temperature": (("time", "lat", "lon"), np.zeros((2, 3, 4))),
                "mean_sea_level_pressure": (("time", "lat", "lon"), np.zeros((2, 3, 4))),
            },
            coords={
                "time": np.arange(2),
                "lat": np.linspace(-90, 90, 3),
                "lon": np.linspace(0, 270, 4),
            },
        )

    def _make_temp_dir(self):
        tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(tmp_dir, ignore_errors=True))
        return tmp_dir

    def test_creates_one_var_zarr_directory_per_variable_and_period(self):
        tmp_dir = self._make_temp_dir()
        args = argparse.Namespace(output_dir=str(tmp_dir), year=(2022,), variables=("sst", "msl"))

        with mock.patch.object(xr, "open_zarr", return_value=self._fake_dataset()):
            result = gridded.run(args)

        self.assertEqual(result, 0)
        self.assertTrue((tmp_dir / "sst_zarr" / "2022_to_2023.zarr").is_dir())
        self.assertTrue((tmp_dir / "msl_zarr" / "2022_to_2023.zarr").is_dir())

    def test_skips_existing_destination_without_opening_the_source(self):
        tmp_dir = self._make_temp_dir()
        existing = tmp_dir / "sst_zarr" / "2022_to_2023.zarr"
        existing.mkdir(parents=True)
        args = argparse.Namespace(output_dir=str(tmp_dir), year=(2022,), variables=("sst",))

        with mock.patch.object(xr, "open_zarr", return_value=self._fake_dataset()) as open_zarr:
            result = gridded.run(args)

        self.assertEqual(result, 0)
        open_zarr.assert_not_called()


if __name__ == "__main__":
    unittest.main()
