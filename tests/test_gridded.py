import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import xarray as xr

from weathernext_download import gridded
from weathernext_download.cli import main


class GriddedTests(unittest.TestCase):
    def test_arguments(self):
        self.assertEqual(gridded.parse_years("2022,2023"), (2022, 2023))
        self.assertEqual(gridded.parse_variables("sst,msl,z300"), ("sst", "msl", "z300"))
        for value in ("z", "z301", "10u", "2t", "sst,"):
            with self.assertRaises(argparse.ArgumentTypeError):
                gridded.parse_variables(value)
        with self.assertRaises(argparse.ArgumentTypeError):
            gridded.parse_years("2025")
        for arguments in (["--gridded"], ["--weight", "list", "--var", "sst"],
                          ["--gridded", "--var", "sst", "--both"]):
            with self.assertRaises(SystemExit) as error:
                main(arguments)
            self.assertEqual(error.exception.code, 2)

    def test_zarr_roundtrip_and_skip(self):
        ds = xr.Dataset({"geopotential": (("level", "lat"), np.array([[6.], [5.], [3.]]))},
                        coords={"level": [600, 500, 300], "lat": [0.]})
        with tempfile.TemporaryDirectory() as root:
            args = ["--gridded", "--year", "2022,2023", "--var", "z500", "--output-dir", root]
            with patch.object(xr, "open_zarr", side_effect=lambda *a, **k: ds.copy()) as opened:
                self.assertEqual(main(args), 0)
                self.assertEqual(opened.call_count, 2)
                self.assertIn("2022_to_2023", opened.call_args_list[0].args[0])
            with xr.open_zarr(Path(root) / "z500_2022_to_2023.zarr") as saved:
                self.assertEqual(saved.geopotential_500hPa.compute().item(), 5.)
            with patch.object(xr, "open_zarr") as opened:
                self.assertEqual(main(args), 0)
                opened.assert_not_called()

    def test_default_years_and_failure(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(xr, "open_zarr", side_effect=OSError("unavailable")) as opened:
                self.assertEqual(main(["--gridded", "--var", "sst", "--output-dir", root]), 1)
                self.assertEqual(opened.call_count, 3)


if __name__ == "__main__":
    unittest.main()
