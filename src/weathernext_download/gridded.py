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

ARCO_ERA5_URL = "gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3"
ARCO_ERA5_REFERENCE_TIME = "2000-01-01T00:00:00"
STATIC_GCLOUD_SPECS = {
    "zs": {
        "source_variable": "geopotential_at_surface",
        "attrs": {
            "units": "m2 s-2",
            "long_name": "Surface geopotential",
            "short_name": "zs",
            "standard_name": "surface_geopotential",
        },
    },
    "lsm": {
        "source_variable": "land_sea_mask",
        "attrs": {
            "units": "1",
            "long_name": "Land-sea mask",
            "short_name": "lsm",
            "standard_name": "land_binary_mask",
        },
    },
}
STATIC_GCLOUD_REQUIREMENTS = (
    ("xarray", "xarray"),
    ("zarr", "zarr"),
    ("gcsfs", "gcsfs"),
    ("netCDF4", "netCDF4"),
)


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


def missing_libraries(requirements):
    missing = []
    for module_name, package_name in requirements:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(package_name)
    return missing


def missing_libraries_message(flag, missing):
    install_args = " ".join(shlex.quote(package) for package in missing)
    return (
        f"Missing libraries for {flag}: {', '.join(missing)}. "
        f"Install with: pip install {install_args}"
    )


def fetch_static_from_gcloud(name: str, destination: Path) -> str:
    """Fetch one static field fresh from the ARCO-ERA5 Zarr archive, returning ``downloaded`` or ``skipped``."""
    if destination.is_file() and destination.stat().st_size > 0:
        return "skipped"

    import xarray as xr

    spec = STATIC_GCLOUD_SPECS[name]
    dataset = xr.open_zarr(ARCO_ERA5_URL, chunks=None, storage_options=dict(token="anon"))
    field = (
        dataset[spec["source_variable"]]
        .sel(time=ARCO_ERA5_REFERENCE_TIME)
        .drop_vars("time")
        .rename(name)
    )
    field.attrs.update(spec["attrs"])

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    field.to_netcdf(temporary, encoding={name: {"zlib": True, "complevel": 4}})
    temporary.replace(destination)
    return "downloaded"


def run(args):
    missing = missing_libraries(GRIDDED_REQUIREMENTS)
    if missing:
        print(missing_libraries_message("--gridded", missing), file=sys.stderr)
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
            destination = var_dir / f"{alias}_{period}.zarr"
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
