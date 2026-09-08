"""Extract selected WeatherNext 2 ensemble-mean fields into local Zarr stores."""

import argparse
import importlib
from pathlib import Path
import re
import shlex
import sys

LEVELS = (50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000)
SURFACE = {
    "sst": "sea_surface_temperature",
    "msl": "mean_sea_level_pressure",
    "u10": "10m_u_component_of_wind",
    "v10": "10m_v_component_of_wind",
    "t2m": "2m_temperature",
    "tp": "total_precipitation_6hr",
}
ATMOSPHERIC = {
    "z": "geopotential", "q": "specific_humidity", "t": "temperature",
    "u": "u_component_of_wind", "v": "v_component_of_wind",
    "w": "vertical_velocity",
}
BASE = "gs://weathernext/weathernext_2_0_0_mean/zarr"


def parse_years(value):
    parts = [part.strip() for part in value.split(",")]
    if not parts or any(part not in ("2022", "2023", "2024") for part in parts):
        raise argparse.ArgumentTypeError("--year accepts 2022, 2023, 2024, or a comma-separated combination")
    return tuple(dict.fromkeys(int(part) for part in parts))


def variable_spec(alias):
    if alias in SURFACE:
        return SURFACE[alias], None
    match = re.fullmatch(r"([zqtuvw])(\d+)", alias)
    if match and match[2] in {str(level) for level in LEVELS}:
        return ATMOSPHERIC[match[1]], int(match[2])
    raise argparse.ArgumentTypeError(
        f"invalid variable {alias!r}; use sst, msl, u10, v10, t2m, tp, "
        "or z/q/t/u/v/w followed by a supported pressure level (for example z300)"
    )


def parse_variables(value):
    aliases = tuple(dict.fromkeys(part.strip().lower() for part in value.split(",")))
    for alias in aliases:
        variable_spec(alias)
    return aliases


def select_variable(dataset, alias):
    name, level = variable_spec(alias)
    selected = dataset[[name]]
    if level is not None:
        selected = selected.sel(level=level)
        selected = selected.rename({name: f"{name}_{level}hPa"})
    selected = selected.copy()
    for name in selected.variables:
        selected[name].encoding.clear()
    return selected


GRIDDED_REQUIREMENTS = (
    ("xarray", "xarray"),
    ("dask.diagnostics", "dask[array]"),
    ("zarr", "zarr"),
    ("gcsfs", "gcsfs"),
)


def run(args):
    missing = []
    for module_name, package_name in GRIDDED_REQUIREMENTS:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(package_name)
    if missing:
        install_args = " ".join(shlex.quote(package) for package in missing)
        print(
            f"Missing libraries for --gridded: {', '.join(missing)}. "
            f"Install with: pip install {install_args}",
            file=sys.stderr,
        )
        return 1

    import xarray as xr
    from dask.diagnostics import ProgressBar

    output = Path(args.output_dir or ".")
    failures = downloaded = skipped = 0
    for year in args.year or (2022, 2023, 2024):
        period = f"{year}_to_{year + 1}"
        pending = []
        for alias in args.variables:
            var_dir = output / f"{alias}_zarr"
            var_dir.mkdir(parents=True, exist_ok=True)
            destination = var_dir / f"{period}.zarr"
            if destination.exists():
                print(f"SKIPPED    {destination} (already exists)")
                skipped += 1
            else:
                pending.append((alias, destination))
        if not pending:
            continue
        url = f"{BASE}/{period}/predictions.zarr"
        try:
            with xr.open_zarr(url) as dataset:
                for alias, destination in pending:
                    temporary = destination.with_name(destination.name + ".part")
                    try:
                        if temporary.exists():
                            raise FileExistsError(f"Partial output exists: {temporary}; move it aside before retrying")
                        selected = select_variable(dataset, alias)
                        print(f"DOWNLOADING {alias} {period} -> {destination}", flush=True)
                        with ProgressBar():
                            selected.to_zarr(temporary, mode="w-")
                        temporary.rename(destination)
                        downloaded += 1
                    except Exception as error:
                        failures += 1
                        print(f"FAILED     {alias} {period}: {error}", file=sys.stderr)
        except Exception as error:
            failures += len(pending)
            print(f"FAILED     {url}: {error}", file=sys.stderr)
    print(f"Finished: {downloaded} downloaded, {skipped} skipped, {failures} failed.")
    return 1 if failures else 0
