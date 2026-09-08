import argparse
import io
import shutil
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError

from weathernext_download import cli


class ParseTimeTests(unittest.TestCase):
    def test_valid_time(self):
        self.assertEqual(cli.parse_time("2022070100"), datetime(2022, 7, 1, 0))

    def test_rejects_wrong_length(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            cli.parse_time("202207010")

    def test_rejects_non_digits(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            cli.parse_time("2022ab0100")

    def test_rejects_invalid_calendar_date(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            cli.parse_time("2022023000")

    def test_rejects_hour_not_in_forecast_hours(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            cli.parse_time("2022070105")


class ParseDatePrefixTests(unittest.TestCase):
    def test_accepts_year(self):
        self.assertEqual(cli.parse_date_prefix("2022"), "2022")

    def test_accepts_year_month(self):
        self.assertEqual(cli.parse_date_prefix("202207"), "202207")

    def test_accepts_year_month_day(self):
        self.assertEqual(cli.parse_date_prefix("20220701"), "20220701")

    def test_rejects_invalid_length(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            cli.parse_date_prefix("202")

    def test_rejects_invalid_calendar_date(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            cli.parse_date_prefix("20220230")


class DatesForPrefixTests(unittest.TestCase):
    def test_year_prefix_spans_full_year(self):
        dates = list(cli.dates_for_prefix("2022"))
        self.assertEqual(dates[0], date(2022, 1, 1))
        self.assertEqual(dates[-1], date(2022, 12, 31))
        self.assertEqual(len(dates), 365)

    def test_month_prefix_spans_full_month(self):
        dates = list(cli.dates_for_prefix("202202"))
        self.assertEqual(dates[0], date(2022, 2, 1))
        self.assertEqual(dates[-1], date(2022, 2, 28))

    def test_day_prefix_is_single_date(self):
        dates = list(cli.dates_for_prefix("20220701"))
        self.assertEqual(dates, [date(2022, 7, 1)])

    def test_end_limit_clamps_range(self):
        dates = list(cli.dates_for_prefix("2022", end_limit=date(2022, 1, 5)))
        self.assertEqual(dates, list(cli.date_range(date(2022, 1, 1), date(2022, 1, 5))))


class DateRangeTests(unittest.TestCase):
    def test_inclusive_range(self):
        result = list(cli.date_range(date(2022, 1, 1), date(2022, 1, 3)))
        self.assertEqual(result, [date(2022, 1, 1), date(2022, 1, 2), date(2022, 1, 3)])

    def test_single_day_range(self):
        result = list(cli.date_range(date(2022, 1, 1), date(2022, 1, 1)))
        self.assertEqual(result, [date(2022, 1, 1)])


class ForecastTimesForDatesTests(unittest.TestCase):
    def test_expands_each_date_to_four_cycles(self):
        times = list(cli.forecast_times_for_dates([date(2022, 1, 1)]))
        self.assertEqual(
            times,
            [
                datetime(2022, 1, 1, 0),
                datetime(2022, 1, 1, 6),
                datetime(2022, 1, 1, 12),
                datetime(2022, 1, 1, 18),
            ],
        )


class RestrictToModelCoverageTests(unittest.TestCase):
    def test_excludes_times_before_coverage_start(self):
        times = [datetime(2021, 12, 31, 18), datetime(2022, 1, 1, 0)]
        result = list(cli.restrict_to_model_coverage(times, "FNV3P2"))
        self.assertEqual(result, [datetime(2022, 1, 1, 0)])

    def test_excludes_times_after_coverage_end(self):
        times = [datetime(2026, 5, 28, 12), datetime(2026, 5, 28, 18)]
        result = list(cli.restrict_to_model_coverage(times, "FNV3P0"))
        self.assertEqual(result, [datetime(2026, 5, 28, 12)])

    def test_wnv3_2025_restricted_to_06_and_18_utc(self):
        times = [datetime(2025, 6, 1, 0), datetime(2025, 6, 1, 6), datetime(2025, 6, 1, 18)]
        result = list(cli.restrict_to_model_coverage(times, "WNV3"))
        self.assertEqual(result, [datetime(2025, 6, 1, 6), datetime(2025, 6, 1, 18)])

    def test_wnv3_2024_keeps_all_four_cycles(self):
        times = [datetime(2024, 6, 1, 0), datetime(2024, 6, 1, 6)]
        result = list(cli.restrict_to_model_coverage(times, "WNV3"))
        self.assertEqual(result, times)


class FilenameForTests(unittest.TestCase):
    def test_csv_filename(self):
        name = cli.filename_for(datetime(2022, 7, 1, 0), "csv", "OPER")
        self.assertEqual(name, "OPER_2022_07_01T00_00_paired.csv")

    def test_atcf_filename(self):
        name = cli.filename_for(datetime(2022, 7, 1, 0), "atcf", "OPER")
        self.assertEqual(name, "OPER_2022_07_01T00_00_atcf_a_deck.txt")


class FormattingHelperTests(unittest.TestCase):
    def test_format_size(self):
        self.assertEqual(cli.format_size(1024 * 1024), "1.0 MiB")

    def test_format_rate(self):
        self.assertEqual(cli.format_rate(2 * 1024 * 1024), "2.0 MiB/s")

    def test_format_duration_under_an_hour(self):
        self.assertEqual(cli.format_duration(125), "02:05")

    def test_format_duration_with_hours(self):
        self.assertEqual(cli.format_duration(3725), "1:02:05")

    def test_format_duration_clamps_negative_to_zero(self):
        self.assertEqual(cli.format_duration(-5), "00:00")


class CycloneOnlyOptionsSelectedTests(unittest.TestCase):
    def _namespace(self, **overrides):
        base = dict(
            time=None,
            date=None,
            ensemble_mean=False,
            ensemble=False,
            both=False,
            file_format=None,
            cyclone_model=None,
        )
        base.update(overrides)
        return argparse.Namespace(**base)

    def test_false_when_nothing_set(self):
        self.assertFalse(cli.cyclone_only_options_selected(self._namespace()))

    def test_true_when_time_set(self):
        self.assertTrue(cli.cyclone_only_options_selected(self._namespace(time=datetime(2022, 1, 1))))

    def test_true_when_model_set(self):
        self.assertTrue(cli.cyclone_only_options_selected(self._namespace(cyclone_model="OPER")))


class SelectedProductsTests(unittest.TestCase):
    def _namespace(self, **overrides):
        base = dict(ensemble_mean=False, ensemble=False, both=False)
        base.update(overrides)
        return argparse.Namespace(**base)

    def test_defaults_to_both_products(self):
        products = cli.selected_products(self._namespace())
        self.assertEqual([product.name for product in products], ["ensemble_mean", "ensemble"])

    def test_ensemble_mean_only(self):
        products = cli.selected_products(self._namespace(ensemble_mean=True))
        self.assertEqual([product.name for product in products], ["ensemble_mean"])

    def test_ensemble_only(self):
        products = cli.selected_products(self._namespace(ensemble=True))
        self.assertEqual([product.name for product in products], ["ensemble"])


class ArgumentValidationTests(unittest.TestCase):
    def _run_main(self, argv):
        stderr = io.StringIO()
        with mock.patch("sys.stderr", stderr):
            with self.assertRaises(SystemExit) as context:
                cli.main(argv)
        return context.exception.code, stderr.getvalue()

    def test_gridded_requires_var(self):
        code, message = self._run_main(["--gridded", "--year", "2022"])
        self.assertEqual(code, 2)
        self.assertIn("--gridded requires --var", message)

    def test_gridded_and_cyclone_are_mutually_exclusive(self):
        code, message = self._run_main(["--gridded", "--var", "sst", "--cyclone"])
        self.assertEqual(code, 2)
        self.assertIn("not allowed with argument", message)

    def test_year_without_gridded_is_rejected(self):
        code, message = self._run_main(["--cyclone", "--year", "2022"])
        self.assertEqual(code, 2)
        self.assertIn("--year, --var and --output-dir require --gridded", message)

    def test_rename_without_weight_is_rejected(self):
        code, message = self._run_main(["--cyclone", "--rename"])
        self.assertEqual(code, 2)
        self.assertIn("--rename may only be used together with --weight", message)

    def test_hf_without_weight_is_rejected(self):
        code, message = self._run_main(["--cyclone", "--hf"])
        self.assertEqual(code, 2)
        self.assertIn("--hf may only be used together with --weight", message)

    def test_cyclone_options_with_weight_are_rejected(self):
        code, message = self._run_main(["--weight", "list", "--time", "2022070100"])
        self.assertEqual(code, 2)
        self.assertIn("cyclone forecast options may only be used together with --cyclone", message)

    def test_negative_timeout_is_rejected(self):
        code, message = self._run_main(["--weight", "list", "--timeout", "0"])
        self.assertEqual(code, 2)
        self.assertIn("--timeout must be greater than zero", message)

    def test_negative_retries_is_rejected(self):
        code, message = self._run_main(["--weight", "list", "--retries", "-1"])
        self.assertEqual(code, 2)
        self.assertIn("--retries cannot be negative", message)

    def test_unknown_weight_abbreviation_is_rejected(self):
        code, message = self._run_main(["--weight", "not-a-real-weight"])
        self.assertEqual(code, 2)
        self.assertIn("unknown weight abbreviation", message)

    def test_static_requires_a_value(self):
        code, message = self._run_main(["--static"])
        self.assertEqual(code, 2)
        self.assertIn("expected one argument", message)

    def test_static_and_weight_are_mutually_exclusive(self):
        code, message = self._run_main(["--static", "zs", "--weight", "list"])
        self.assertEqual(code, 2)
        self.assertIn("not allowed with argument", message)

    def test_cyclone_options_with_static_are_rejected(self):
        code, message = self._run_main(["--static", "zs", "--time", "2022070100"])
        self.assertEqual(code, 2)
        self.assertIn("cyclone forecast options may only be used together with --cyclone", message)

    def test_rename_with_static_is_rejected(self):
        code, message = self._run_main(["--static", "zs", "--rename"])
        self.assertEqual(code, 2)
        self.assertIn("--rename and --hf may only be used together with --weight", message)

    def test_unknown_static_name_is_rejected(self):
        code, message = self._run_main(["--static", "not-a-real-static-file"])
        self.assertEqual(code, 2)
        self.assertIn("unknown static file", message)


class CopyStaticFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.tmp_dir, ignore_errors=True))

    def test_copies_bundled_file_contents(self):
        destination = self.tmp_dir / "zs.nc"
        status = cli.copy_static_file("zs.nc", destination)

        self.assertEqual(status, "copied")
        self.assertTrue(destination.is_file())
        self.assertGreater(destination.stat().st_size, 0)

    def test_skips_existing_non_empty_file(self):
        destination = self.tmp_dir / "zs.nc"
        destination.write_bytes(b"already here")

        status = cli.copy_static_file("zs.nc", destination)

        self.assertEqual(status, "skipped")
        self.assertEqual(destination.read_bytes(), b"already here")


class RunStaticCommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.tmp_dir, ignore_errors=True))
        self.cwd_patcher = mock.patch.object(cli.Path, "cwd", return_value=self.tmp_dir)
        self.cwd_patcher.start()
        self.addCleanup(self.cwd_patcher.stop)

    def _run(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr):
            code = cli.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_static_all_copies_every_static_file(self):
        code, stdout, _ = self._run(["--static", "all"])
        self.assertEqual(code, 0)
        self.assertTrue((self.tmp_dir / "zs.nc").is_file())
        self.assertIn("1 copied, 0 skipped, 0 failed", stdout)

    def test_static_zs_copies_only_zs(self):
        code, stdout, _ = self._run(["--static", "zs"])
        self.assertEqual(code, 0)
        self.assertTrue((self.tmp_dir / "zs.nc").is_file())
        self.assertIn("1 copied, 0 skipped, 0 failed", stdout)

    def test_second_run_skips_existing_file(self):
        self._run(["--static", "zs"])
        code, stdout, _ = self._run(["--static", "zs"])
        self.assertEqual(code, 0)
        self.assertIn("0 copied, 1 skipped, 0 failed", stdout)


class DownloadFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.tmp_dir, ignore_errors=True))

    def test_downloads_and_writes_atomically(self):
        destination = self.tmp_dir / "out.csv"
        response = mock.MagicMock()
        response.read.side_effect = [b"hello", b""]
        response.__enter__.return_value = response
        response.__exit__.return_value = False

        with mock.patch.object(cli, "urlopen", return_value=response):
            status = cli.download_file("http://example.invalid/file", destination, timeout=1, retries=0)

        self.assertEqual(status, "downloaded")
        self.assertEqual(destination.read_bytes(), b"hello")
        self.assertEqual(list(self.tmp_dir.iterdir()), [destination])

    def test_skips_existing_non_empty_file(self):
        destination = self.tmp_dir / "out.csv"
        destination.write_bytes(b"already here")

        with mock.patch.object(cli, "urlopen") as urlopen:
            status = cli.download_file("http://example.invalid/file", destination, timeout=1, retries=0)

        self.assertEqual(status, "skipped")
        urlopen.assert_not_called()

    def test_retries_then_succeeds(self):
        destination = self.tmp_dir / "out.csv"
        good_response = mock.MagicMock()
        good_response.read.side_effect = [b"ok", b""]
        good_response.__enter__.return_value = good_response
        good_response.__exit__.return_value = False

        with mock.patch.object(cli, "urlopen", side_effect=[OSError("boom"), good_response]):
            with mock.patch.object(cli.time_module, "sleep"):
                status = cli.download_file("http://example.invalid/file", destination, timeout=1, retries=1)

        self.assertEqual(status, "downloaded")
        self.assertEqual(destination.read_bytes(), b"ok")

    def test_raises_after_exhausting_retries(self):
        destination = self.tmp_dir / "out.csv"

        with mock.patch.object(cli, "urlopen", side_effect=OSError("boom")):
            with mock.patch.object(cli.time_module, "sleep"):
                with self.assertRaises(OSError):
                    cli.download_file("http://example.invalid/file", destination, timeout=1, retries=1)
        self.assertFalse(destination.exists())


class DownloadModelWeightTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.tmp_dir, ignore_errors=True))
        self.weight = cli.ModelWeight("test-weight", "TestWeight.npz", size_bytes=4)

    def test_downloads_full_weight(self):
        response = mock.MagicMock()
        response.getcode.return_value = 200
        response.read.side_effect = [b"data", b""]
        response.__enter__.return_value = response
        response.__exit__.return_value = False

        with mock.patch.object(cli, "urlopen", return_value=response):
            status = cli.download_model_weight(self.weight, self.tmp_dir, timeout=1, retries=0)

        self.assertEqual(status, "downloaded")
        self.assertEqual((self.tmp_dir / "TestWeight.npz").read_bytes(), b"data")

    def test_skips_already_complete_file(self):
        destination = self.tmp_dir / "TestWeight.npz"
        destination.write_bytes(b"data")

        with mock.patch.object(cli, "urlopen") as urlopen:
            status = cli.download_model_weight(self.weight, self.tmp_dir, timeout=1, retries=0)

        self.assertEqual(status, "skipped")
        urlopen.assert_not_called()

    def test_resumes_partial_file_with_range_request(self):
        destination = self.tmp_dir / "TestWeight.npz"
        destination.write_bytes(b"da")

        response = mock.MagicMock()
        response.getcode.return_value = 206
        response.headers = {"Content-Range": "bytes 2-3/4"}
        response.read.side_effect = [b"ta", b""]
        response.__enter__.return_value = response
        response.__exit__.return_value = False

        captured_request = {}

        def fake_urlopen(request, timeout):
            captured_request["headers"] = dict(request.header_items())
            return response

        with mock.patch.object(cli, "urlopen", side_effect=fake_urlopen):
            status = cli.download_model_weight(self.weight, self.tmp_dir, timeout=1, retries=0)

        self.assertEqual(status, "downloaded")
        self.assertEqual(destination.read_bytes(), b"data")
        self.assertEqual(captured_request["headers"].get("Range"), "bytes=2-")

    def test_raises_when_existing_file_is_too_large(self):
        destination = self.tmp_dir / "TestWeight.npz"
        destination.write_bytes(b"toolarge")

        with self.assertRaises(OSError):
            cli.download_model_weight(self.weight, self.tmp_dir, timeout=1, retries=0)


if __name__ == "__main__":
    unittest.main()
