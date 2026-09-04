#!/usr/bin/env python3
"""Download WeatherNext model weights or Weather Lab cyclone products."""

from __future__ import annotations

import argparse
import calendar
import os
import sys
import time as time_module
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from itertools import chain
from pathlib import Path
from typing import Iterable, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


BASE_URL = "https://deepmind.google.com/science/weatherlab/download/cyclones"
GOOGLE_WEIGHT_BASE_URL = (
    "https://storage.googleapis.com/dm_graphcast/weathernext2/params"
)
HUGGINGFACE_WEIGHT_BASE_URL = (
    "https://huggingface.co/CONGG/weathernext-weight/resolve/main"
)
WEIGHT_OUTPUT_DIRECTORY = "weathernext-weight"
FIRST_DEFAULT_DATE = date(2022, 1, 1)
FORECAST_HOURS = (0, 6, 12, 18)
CHUNK_SIZE = 1024 * 1024

# Inclusive UTC initialization-time boundaries observed in Weather Lab.
MODEL_COVERAGE: dict[str, tuple[datetime, datetime | None]] = {
    "OPER": (datetime(2025, 6, 12, 0), None),
    "WNV3": (datetime(2024, 1, 1, 0), None),
    "FNV3P2": (datetime(2022, 1, 1, 0), None),
    "FNV3P1": (datetime(2022, 1, 1, 0), None),
    "FNV3P0": (datetime(2022, 1, 1, 0), datetime(2026, 5, 28, 12)),
    "FNV3_LARGE_ENSEMBLE": (datetime(2025, 10, 18, 0), None),
}


@dataclass(frozen=True)
class Product:
    name: str
    output_dir: Path

    def url_for(
        self, forecast_time: datetime, file_format: str, model: str
    ) -> str:
        filename = filename_for(forecast_time, file_format, model)
        return f"{BASE_URL}/{model}/{self.name}/paired/{file_format}/{filename}"


@dataclass(frozen=True)
class ModelWeight:
    abbreviation: str
    filename: str
    size_bytes: int

    def url_for(self, use_huggingface: bool = False) -> str:
        base_url = (
            HUGGINGFACE_WEIGHT_BASE_URL
            if use_huggingface
            else GOOGLE_WEIGHT_BASE_URL
        )
        return f"{base_url}/{quote(self.filename, safe='')}"

    def output_filename(self, rename: bool = False) -> str:
        if rename:
            return f"{self.abbreviation}.npz"
        return self.filename


MODEL_WEIGHTS: tuple[ModelWeight, ...] = (
    *(
        ModelWeight(
            f"wn2-25-m{member}",
            f"WeatherNext2_<2025_model{member}.npz",
            735_348_710,
        )
        for member in range(1, 5)
    ),
    *(
        ModelWeight(
            f"wnc-23-m{member}",
            f"WeatherNextCyclones_<2023_model{member}.npz",
            735_326_830,
        )
        for member in range(1, 5)
    ),
    *(
        ModelWeight(
            f"wnc-24-m{member}",
            f"WeatherNextCyclones_<2024_model{member}.npz",
            735_326_830,
        )
        for member in range(1, 5)
    ),
    *(
        ModelWeight(
            f"wnc-25-m{member}",
            f"WeatherNextCyclones_<2025_model{member}.npz",
            735_326_830,
        )
        for member in range(1, 5)
    ),
    ModelWeight(
        "wnc-mini-23", "WeatherNextCyclones_Mini_<2023.npz", 226_897_594
    ),
    ModelWeight(
        "wnc-mini-24", "WeatherNextCyclones_Mini_<2024.npz", 226_897_594
    ),
)
MODEL_WEIGHTS_BY_ABBREVIATION = {
    weight.abbreviation: weight for weight in MODEL_WEIGHTS
}


def filename_for(forecast_time: datetime, file_format: str, model: str) -> str:
    if file_format == "atcf":
        suffix = forecast_time.strftime("%Y_%m_%dT%H_00_atcf_a_deck.txt")
    else:
        suffix = forecast_time.strftime("%Y_%m_%dT%H_00_paired.csv")
    return f"{model}_{suffix}"


def parse_time(value: str) -> datetime:
    if len(value) != 10 or not value.isdigit():
        raise argparse.ArgumentTypeError("time must have the format YYYYMMDDHH")
    try:
        result = datetime.strptime(value, "%Y%m%d%H")
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid time {value!r}: {error}") from error
    if result.hour not in FORECAST_HOURS:
        allowed = ", ".join(f"{hour:02d}" for hour in FORECAST_HOURS)
        raise argparse.ArgumentTypeError(f"hour must be one of: {allowed}")
    return result


def parse_date_prefix(value: str) -> str:
    if len(value) not in (4, 6, 8) or not value.isdigit():
        raise argparse.ArgumentTypeError("date must have the format YYYY, YYYYMM, or YYYYMMDD")

    try:
        if len(value) == 4:
            datetime.strptime(value, "%Y")
        elif len(value) == 6:
            datetime.strptime(value, "%Y%m")
        else:
            datetime.strptime(value, "%Y%m%d")
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"invalid date {value!r}: {error}") from error
    return value


def dates_for_prefix(value: str, end_limit: date | None = None) -> Iterator[date]:
    year = int(value[:4])
    if len(value) == 4:
        start = date(year, 1, 1)
        end = date(year, 12, 31)
    elif len(value) == 6:
        month = int(value[4:6])
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
    else:
        start = end = datetime.strptime(value, "%Y%m%d").date()

    if end_limit is not None:
        end = min(end, end_limit)
    yield from date_range(start, end)


def date_range(start: date, end: date) -> Iterator[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def forecast_times_for_dates(dates: Iterable[date]) -> Iterator[datetime]:
    for day in dates:
        for hour in FORECAST_HOURS:
            yield datetime(day.year, day.month, day.day, hour)


def latest_download_date() -> date:
    return (datetime.now(timezone.utc) - timedelta(hours=24)).date()


def default_forecast_times() -> Iterator[datetime]:
    last_date = latest_download_date()
    if last_date < FIRST_DEFAULT_DATE:
        return
    yield from forecast_times_for_dates(date_range(FIRST_DEFAULT_DATE, last_date))


def restrict_to_model_coverage(
    forecast_times: Iterable[datetime], model: str
) -> Iterator[datetime]:
    start, end = MODEL_COVERAGE[model]
    for forecast_time in forecast_times:
        if forecast_time < start or (end is not None and forecast_time > end):
            continue
        if model == "WNV3" and forecast_time.year == 2025:
            if forecast_time.hour not in (6, 18):
                continue
        yield forecast_time


def download_file(url: str, destination: Path, timeout: float, retries: int) -> str:
    """Download one URL atomically, returning ``downloaded`` or ``skipped``."""
    if destination.is_file() and destination.stat().st_size > 0:
        return "skipped"

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.part")
    request = Request(url, headers={"User-Agent": "weathernext-downloader/1.0"})

    try:
        for attempt in range(retries + 1):
            try:
                with urlopen(request, timeout=timeout) as response, temporary.open("wb") as output:
                    while chunk := response.read(CHUNK_SIZE):
                        output.write(chunk)
                temporary.replace(destination)
                return "downloaded"
            except (HTTPError, URLError, TimeoutError, OSError):
                temporary.unlink(missing_ok=True)
                if attempt == retries:
                    raise
                time_module.sleep(min(2**attempt, 8))
    finally:
        temporary.unlink(missing_ok=True)

    raise RuntimeError("unreachable")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Download WeatherNext weights or paired Weather Lab cyclone files."
        ),
        epilog=(
            "Use --cyclone with the cyclone options, or use --weight list, "
            "--weight ABBREVIATION, or --weight all for pretrained weights."
        ),
    )

    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--cyclone",
        action="store_true",
        help="download Weather Lab cyclone forecast products",
    )
    action.add_argument(
        "--weight",
        dest="weight_selection",
        metavar="ABBREVIATION",
        help="list or download pretrained weights (use 'list' or 'all')",
    )
    parser.add_argument(
        "--rename",
        action="store_true",
        help="save weight files as ABBREVIATION.npz (only with --weight)",
    )
    parser.add_argument(
        "--hf",
        action="store_true",
        help="download weights from the Hugging Face mirror instead of Google",
    )

    period = parser.add_mutually_exclusive_group()
    period.add_argument(
        "--time",
        type=parse_time,
        metavar="YYYYMMDDHH",
        help="download one cycle within the selected model's coverage",
    )
    period.add_argument(
        "--date",
        type=parse_date_prefix,
        metavar="YYYY[MM[DD]]",
        help="download the selected period within current and model coverage",
    )

    product = parser.add_mutually_exclusive_group()
    product.add_argument("--ensemble-mean", "--ensemble_mean", action="store_true")
    product.add_argument("--ensemble", action="store_true")
    product.add_argument("--both", action="store_true")

    file_format = parser.add_mutually_exclusive_group()
    file_format.add_argument(
        "--csv", action="store_const", const="csv", dest="file_format"
    )
    file_format.add_argument(
        "--atcf", action="store_const", const="atcf", dest="file_format"
    )

    model = parser.add_mutually_exclusive_group()
    model.add_argument(
        "--oper", action="store_const", const="OPER", dest="cyclone_model"
    )
    model.add_argument(
        "--wnv3", action="store_const", const="WNV3", dest="cyclone_model"
    )
    model.add_argument(
        "--v3p2", action="store_const", const="FNV3P2", dest="cyclone_model"
    )
    model.add_argument(
        "--v3p1", action="store_const", const="FNV3P1", dest="cyclone_model"
    )
    model.add_argument(
        "--v3p0", action="store_const", const="FNV3P0", dest="cyclone_model"
    )
    model.add_argument(
        "--v3p2LE",
        "--v3p2le",
        action="store_const",
        const="FNV3_LARGE_ENSEMBLE",
        dest="cyclone_model",
    )

    parser.add_argument("--timeout", type=float, default=60.0, metavar="SECONDS")
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        metavar="N",
        help="retry each failed download N times (default: 2)",
    )
    return parser


def selected_products(args: argparse.Namespace) -> list[Product]:
    output_root = Path.cwd()
    if args.ensemble_mean:
        names = ("ensemble_mean",)
    elif args.ensemble:
        names = ("ensemble",)
    else:
        names = ("ensemble_mean", "ensemble")
    return [Product(name, output_root / name) for name in names]


def selected_forecast_times(args: argparse.Namespace) -> Iterable[datetime]:
    if args.time is not None:
        forecast_times: Iterable[datetime] = (args.time,)
    elif args.date is not None:
        dates = dates_for_prefix(args.date, end_limit=latest_download_date())
        forecast_times = forecast_times_for_dates(dates)
    else:
        forecast_times = default_forecast_times()
    return restrict_to_model_coverage(forecast_times, args.cyclone_model)


def format_size(size_bytes: int) -> str:
    return f"{size_bytes / (1024 * 1024):.1f} MiB"


def list_model_weights() -> None:
    abbreviation_width = max(
        len("ABBREVIATION"),
        *(len(weight.abbreviation) for weight in MODEL_WEIGHTS),
    )
    print(f"{'ABBREVIATION':<{abbreviation_width}}  {'SIZE':>9}  FILE")
    for weight in MODEL_WEIGHTS:
        print(
            f"{weight.abbreviation:<{abbreviation_width}}  "
            f"{format_size(weight.size_bytes):>9}  {weight.filename}"
        )
    total_size = sum(weight.size_bytes for weight in MODEL_WEIGHTS)
    print(
        f"\n{len(MODEL_WEIGHTS)} models; "
        f"{total_size / (1024 ** 3):.3f} GiB total"
    )


def download_model_weight(
    weight: ModelWeight,
    output_directory: Path,
    timeout: float,
    retries: int,
    rename: bool = False,
    use_huggingface: bool = False,
) -> str:
    """Download or resume one model weight with urllib."""
    output_directory.mkdir(parents=True, exist_ok=True)
    destination = output_directory / weight.output_filename(rename)
    source_url = weight.url_for(use_huggingface)

    for attempt in range(retries + 1):
        if destination.is_file():
            existing_size = destination.stat().st_size
            if existing_size == weight.size_bytes:
                return "skipped" if attempt == 0 else "downloaded"
            if existing_size > weight.size_bytes:
                raise OSError(
                    f"{destination} is larger than the expected "
                    f"{weight.size_bytes} bytes"
                )
            if attempt == 0 and existing_size > 0:
                print(
                    f"RESUMING   {destination} "
                    f"({format_size(existing_size)} of "
                    f"{format_size(weight.size_bytes)})",
                    flush=True,
                )
        elif destination.exists():
            raise OSError(f"{destination} exists but is not a regular file")
        else:
            existing_size = 0

        headers = {"User-Agent": "weathernext-download/1.0"}
        if existing_size:
            headers["Range"] = f"bytes={existing_size}-"
        request = Request(source_url, headers=headers)

        try:
            with urlopen(request, timeout=timeout) as response:
                status = response.getcode()
                if existing_size and status == 206:
                    content_range = response.headers.get("Content-Range", "")
                    if not content_range.startswith(f"bytes {existing_size}-"):
                        raise OSError(
                            f"unexpected Content-Range {content_range!r}"
                        )
                    mode = "ab"
                elif status in (200, 206):
                    # Restart when the server ignores a Range request.
                    mode = "wb"
                else:
                    raise OSError(f"unexpected HTTP status {status}")

                with destination.open(mode) as output:
                    while chunk := response.read(CHUNK_SIZE):
                        output.write(chunk)

            downloaded_size = destination.stat().st_size
            if downloaded_size != weight.size_bytes:
                raise OSError(
                    f"{destination} has {downloaded_size} bytes; expected "
                    f"{weight.size_bytes} bytes"
                )
            return "downloaded"
        except (HTTPError, URLError, TimeoutError, OSError):
            if attempt == retries:
                raise
            time_module.sleep(min(2**attempt, 8))

    raise RuntimeError("unreachable")


def cyclone_only_options_selected(args: argparse.Namespace) -> bool:
    return any(
        (
            args.time is not None,
            args.date is not None,
            args.ensemble_mean,
            args.ensemble,
            args.both,
            args.file_format is not None,
            args.cyclone_model is not None,
        )
    )


def run_weight_command(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> int:
    if cyclone_only_options_selected(args):
        parser.error(
            "cyclone forecast options may only be used together with --cyclone"
        )

    selection = args.weight_selection.lower()
    if selection == "list":
        list_model_weights()
        return 0
    if selection == "all":
        weights = MODEL_WEIGHTS
    else:
        try:
            weights = (MODEL_WEIGHTS_BY_ABBREVIATION[selection],)
        except KeyError:
            parser.error(
                f"unknown weight abbreviation {args.weight_selection!r}; "
                "use --weight list to see the available weights"
            )

    output_directory = Path.cwd() / WEIGHT_OUTPUT_DIRECTORY
    failures: list[tuple[ModelWeight, BaseException]] = []
    downloaded = 0
    skipped = 0
    for weight in weights:
        try:
            status = download_model_weight(
                weight,
                output_directory,
                args.timeout,
                args.retries,
                args.rename,
                args.hf,
            )
        except OSError as error:
            failures.append((weight, error))
            print(
                f"FAILED     {weight.abbreviation}: {error}",
                file=sys.stderr,
                flush=True,
            )
            continue

        destination = output_directory / weight.output_filename(args.rename)
        if status == "downloaded":
            downloaded += 1
            print(
                f"DOWNLOADED {weight.url_for(args.hf)} -> {destination}",
                flush=True,
            )
        else:
            skipped += 1
            print(f"SKIPPED    {destination} (complete file exists)", flush=True)

    print(
        f"Finished: {downloaded} downloaded, {skipped} skipped, "
        f"{len(failures)} failed.",
        file=sys.stderr if failures else sys.stdout,
    )
    return 1 if failures else 0


def run_cyclone_command(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> int:
    if args.rename:
        parser.error("--rename may only be used together with --weight")
    if args.hf:
        parser.error("--hf may only be used together with --weight")
    args.file_format = args.file_format or "csv"
    args.cyclone_model = args.cyclone_model or "OPER"


    products = selected_products(args)
    forecast_times = iter(selected_forecast_times(args))
    try:
        first_forecast_time = next(forecast_times)
    except StopIteration:
        parser.error(
            f"the requested time does not overlap current availability and "
            f"{args.cyclone_model} model coverage"
        )

    failures: list[tuple[str, BaseException]] = []
    downloaded = 0
    skipped = 0

    for forecast_time in chain((first_forecast_time,), forecast_times):
        for product in products:
            destination = product.output_dir / filename_for(
                forecast_time, args.file_format, args.cyclone_model
            )
            url = product.url_for(
                forecast_time, args.file_format, args.cyclone_model
            )
            try:
                status = download_file(url, destination, args.timeout, args.retries)
            except (HTTPError, URLError, TimeoutError, OSError) as error:
                failures.append((url, error))
                print(f"FAILED     {url}: {error}", file=sys.stderr, flush=True)
                continue

            if status == "downloaded":
                downloaded += 1
                print(f"DOWNLOADED {url} -> {destination}", flush=True)
            else:
                skipped += 1
                print(f"SKIPPED    {destination} (already exists)", flush=True)

    print(
        f"Finished: {downloaded} downloaded, {skipped} skipped, {len(failures)} failed.",
        file=sys.stderr if failures else sys.stdout,
    )
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if args.retries < 0:
        parser.error("--retries cannot be negative")

    if args.cyclone:
        return run_cyclone_command(args, parser)
    return run_weight_command(args, parser)


if __name__ == "__main__":
    raise SystemExit(main())
