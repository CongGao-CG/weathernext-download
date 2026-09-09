# weathernext-download

`weathernext-download` downloads pretrained WeatherNext model weights,
static input fields, gridded WeatherNext 2 ensemble-mean forecasts, and
paired tropical-cyclone forecast files. Model weights come from
[Google's public `dm_graphcast` bucket](https://console.cloud.google.com/storage/browser/dm_graphcast/weathernext2/params?pageState=%28%22StorageObjectListTable%22:%28%22f%22:%22%255B%255D%22%29%29)
by default, with
[`CONGG/weathernext-weight`](https://huggingface.co/CONGG/weathernext-weight)
available as an optional Hugging Face mirror. Static input fields are bundled
with this package rather than downloaded. Gridded forecasts come from
Google's [WeatherNext 2 model guide](https://developers.google.com/weathernext/guides/models-wn2).
Cyclone products come from
[Google DeepMind Weather Lab](https://deepmind.google.com/science/weatherlab).

## Installation

```bash
pip install --upgrade weathernext-download
```

Or from source:

```bash
git clone https://github.com/CongGao-CG/weathernext-download.git
cd weathernext-download
pip install .
```

The base package has no third-party Python runtime dependencies. Both cyclone files
and model weights are downloaded using Python's standard-library `urllib`.

## Model weights

List all 18 available pretrained weights and their abbreviations:

```bash
weathernext-download --weight list
```

Download one weight:

```bash
weathernext-download --weight wnc-25-m1
```

Use the Hugging Face mirror instead of Google:

```bash
weathernext-download --weight wnc-25-m1 --hf
```

Save it using its abbreviation (`wnc-25-m1.npz`) instead of its original
filename:

```bash
weathernext-download --weight wnc-25-m1 --rename
```

Download all 18 weights:

```bash
weathernext-download --weight all
```

Add `--rename` to save all 18 files as their abbreviations:

```bash
weathernext-download --weight all --rename
```

Weights are stored under `./weathernext-weight`. A complete existing file is
skipped. A smaller partial file is resumed using an HTTP `Range` request.
During a download, interactive terminals show a progress bar with the
percentage, transferred size, speed, and estimated time remaining.
Abbreviations are case-insensitive. Without `--rename`, the original weight
filename is retained. `--rename` and `--hf` are available only with `--weight`.

Without `--hf`, weights are downloaded directly from Google's public bucket:

```text
https://storage.googleapis.com/dm_graphcast/weathernext2/params/<encoded-filename>
```

For example, the default URL for `wn2-25-m1` is:

```text
https://storage.googleapis.com/dm_graphcast/weathernext2/params/WeatherNext2_%3C2025_model1.npz
```

With `--hf`, the Hugging Face mirror is used:

```text
https://huggingface.co/CONGG/weathernext-weight/resolve/main/<encoded-filename>
```

For example:

```text
https://huggingface.co/CONGG/weathernext-weight/resolve/main/WeatherNext2_%3C2025_model1.npz
```

### Weight inventory

| Abbreviation | Weight filename | Model | Resolution | Trained through | Size |
| --- | --- | --- | --- | --- | ---: |
| `wn2-25-m1` | `WeatherNext2_<2025_model1.npz` | WeatherNext 2, model 1 | 0.25° | 2024 | 701.283 MiB |
| `wn2-25-m2` | `WeatherNext2_<2025_model2.npz` | WeatherNext 2, model 2 | 0.25° | 2024 | 701.283 MiB |
| `wn2-25-m3` | `WeatherNext2_<2025_model3.npz` | WeatherNext 2, model 3 | 0.25° | 2024 | 701.283 MiB |
| `wn2-25-m4` | `WeatherNext2_<2025_model4.npz` | WeatherNext 2, model 4 | 0.25° | 2024 | 701.283 MiB |
| `wnc-23-m1` | `WeatherNextCyclones_<2023_model1.npz` | WeatherNext Cyclones, model 1 | 0.25° | 2022 | 701.262 MiB |
| `wnc-23-m2` | `WeatherNextCyclones_<2023_model2.npz` | WeatherNext Cyclones, model 2 | 0.25° | 2022 | 701.262 MiB |
| `wnc-23-m3` | `WeatherNextCyclones_<2023_model3.npz` | WeatherNext Cyclones, model 3 | 0.25° | 2022 | 701.262 MiB |
| `wnc-23-m4` | `WeatherNextCyclones_<2023_model4.npz` | WeatherNext Cyclones, model 4 | 0.25° | 2022 | 701.262 MiB |
| `wnc-24-m1` | `WeatherNextCyclones_<2024_model1.npz` | WeatherNext Cyclones, model 1 | 0.25° | 2023 | 701.262 MiB |
| `wnc-24-m2` | `WeatherNextCyclones_<2024_model2.npz` | WeatherNext Cyclones, model 2 | 0.25° | 2023 | 701.262 MiB |
| `wnc-24-m3` | `WeatherNextCyclones_<2024_model3.npz` | WeatherNext Cyclones, model 3 | 0.25° | 2023 | 701.262 MiB |
| `wnc-24-m4` | `WeatherNextCyclones_<2024_model4.npz` | WeatherNext Cyclones, model 4 | 0.25° | 2023 | 701.262 MiB |
| `wnc-25-m1` | `WeatherNextCyclones_<2025_model1.npz` | WeatherNext Cyclones/FNV3, model 1 | 0.25° | 2024 | 701.262 MiB |
| `wnc-25-m2` | `WeatherNextCyclones_<2025_model2.npz` | WeatherNext Cyclones/FNV3, model 2 | 0.25° | 2024 | 701.262 MiB |
| `wnc-25-m3` | `WeatherNextCyclones_<2025_model3.npz` | WeatherNext Cyclones/FNV3, model 3 | 0.25° | 2024 | 701.262 MiB |
| `wnc-25-m4` | `WeatherNextCyclones_<2025_model4.npz` | WeatherNext Cyclones/FNV3, model 4 | 0.25° | 2024 | 701.262 MiB |
| `wnc-mini-23` | `WeatherNextCyclones_Mini_<2023.npz` | WeatherNext Cyclones Mini | 1° | 2022 | 216.386 MiB |
| `wnc-mini-24` | `WeatherNextCyclones_Mini_<2024.npz` | WeatherNext Cyclones Mini | 1° | 2023 | 216.386 MiB |

The combined download size is 12,219,111,988 bytes, or approximately 11.380
GiB. The year after `<` identifies the first evaluation year: for example,
`<2025` was trained on data through 2024.

Models 1–4 are independently initialized and trained checkpoints of the same
architecture. They are intended to be combined as a deep ensemble; model 4 is
not newer than model 1. The Mini checkpoints have only one weights file.

### Model input and output variables

The weights above cover three model configurations: `WeatherNextCyclones`,
`WeatherNextCyclones_Mini`, and `WeatherNext2`. These are model tensor
variables used when running the downloaded weights. A ✓ applies to all three
configurations, **WN2 only** applies only to `WeatherNext2`, and — means the
variable is not used in that role.

![WeatherNext model inputs and outputs](https://raw.githubusercontent.com/CongGao-CG/weathernext-download/main/docs/model-input-output.svg)

During autoregressive forecasting, predicted atmospheric and surface fields
are fed back as inputs for the next time step. Static surface fields are
reused, time forcings are advanced, and output-only precipitation and cyclone
fields are not fed back.

| No. | Category | Variable | Input | Output |
| ---: | --- | --- | --- | --- |
| 1 | Pressure level | `temperature` | ✓ | ✓ |
| 2 | Pressure level | `geopotential` | ✓ | ✓ |
| 3 | Pressure level | `u_component_of_wind` | ✓ | ✓ |
| 4 | Pressure level | `v_component_of_wind` | ✓ | ✓ |
| 5 | Pressure level | `vertical_velocity` | ✓ | ✓ |
| 6 | Pressure level | `specific_humidity` | ✓ | ✓ |
| 7 | Surface / near-surface | `2m_temperature` | ✓ | ✓ |
| 8 | Surface / near-surface | `mean_sea_level_pressure` | ✓ | ✓ |
| 9 | Surface / near-surface | `10m_u_component_of_wind` | ✓ | ✓ |
| 10 | Surface / near-surface | `10m_v_component_of_wind` | ✓ | ✓ |
| 11 | Surface / near-surface | `sea_surface_temperature` | ✓ | ✓ |
| 12 | Surface / near-surface | `100m_u_component_of_wind` | **WN2 only** | **WN2 only** |
| 13 | Surface / near-surface | `100m_v_component_of_wind` | **WN2 only** | **WN2 only** |
| 14 | Surface accumulation | `total_precipitation_6hr` | — | ✓ |
| 15 | Static surface | `geopotential_at_surface` | ✓ | — |
| 16 | Static surface | `land_sea_mask` | ✓ | — |
| 17 | Time forcing | `year_progress_sin` | ✓ | — |
| 18 | Time forcing | `year_progress_cos` | ✓ | — |
| 19 | Time forcing | `day_progress_sin` | ✓ | — |
| 20 | Time forcing | `day_progress_cos` | ✓ | — |

Each pressure-level variable spans these 13 pressure levels, in hPa:

```text
50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000
```

Surface and near-surface variables have no pressure-level dimension. Heights
such as 2 m, 10 m, and 100 m denote height above the surface.

Cyclone outputs are separate spatial fields, also without a pressure-level
dimension. All three model configurations predict them; none use them as
configured inputs.

| Cyclone quantity | Output variable(s) | Count |
| --- | --- | ---: |
| Existence | `cyclone_exists_gaussian_unit_mode` | 1 |
| Wind intensity | `cyclone_all_wind_disc`, `cyclone_usa_wind_disc` | 2 |
| 34-knot wind radii | `cyclone_usa_r34_{ne,se,sw,nw}_radius_disc` | 4 |
| 50-knot wind radii | `cyclone_usa_r50_{ne,se,sw,nw}_radius_disc` | 4 |
| 64-knot wind radii | `cyclone_usa_r64_{ne,se,sw,nw}_radius_disc` | 4 |
| Radius of maximum wind | `cyclone_usa_rmw_disc` | 1 |
| Central pressure | `cyclone_usa_pres_disc` | 1 |

The brace notation represents four separate quadrant variables: northeast,
southeast, southwest, and northwest.

| Model configuration | Pressure-level variables | Surface weather outputs | Cyclone outputs |
| --- | ---: | ---: | ---: |
| `WeatherNextCyclones` | 6 (13 levels) | 6 | 17 |
| `WeatherNextCyclones_Mini` | 6 (13 levels) | 6 | 17 |
| `WeatherNext2` | 6 (13 levels) | 8 | 17 |

The model implementations and original model inventory are maintained in
Google DeepMind's [WeatherNext repository](https://github.com/google-deepmind/weathernext#provided-pretrained-models).
The model weights are separate from this package and remain subject to their
own license and terms.

## Static files

`--static` copies static NetCDF fields bundled with the package itself,
rather than downloading them over the network. These correspond to the
static surface inputs listed among the model inputs above: `zs` (`zs.nc`,
surface geopotential, used as terrain elevation) and `lsm` (`lsm.nc`,
land-sea mask).

```bash
weathernext-download --static zs
weathernext-download --static lsm
weathernext-download --static all
```

`--static` requires a NAME. Passing `all` copies every bundled static file
(currently `zs.nc` and `lsm.nc`); passing a specific name copies just that
file. Files are copied to the current directory. An existing non-empty file
with the same name is skipped rather than overwritten. `--rename`, `--hf`,
and the cyclone options cannot be used with `--static`.

Add `--gcloud` to fetch the field fresh from Google Cloud instead of copying
the bundled copy:

```bash
weathernext-download --static zs --gcloud
weathernext-download --static all --gcloud
```

`--gcloud` requires `--static` and re-extracts the requested field(s) from
the public [ARCO-ERA5 Zarr archive](https://console.cloud.google.com/storage/browser/gcp-public-data-arco-era5)
(`gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3`),
using an anonymous GCS connection (no Google account required). Since `zs`
and `lsm` are time-invariant fields, a single reference time is read and the
time dimension is dropped. Using `--gcloud` requires `xarray`, `zarr`,
`gcsfs`, and `netCDF4` in your Python environment; these libraries are not
installed by this package and must be provided separately.

## Gridded forecasts (ensemble mean)

`--gridded` downloads **WeatherNext 2 ensemble-mean forecasts only**, saved
as Zarr. These fields are averages across **64 ensemble members**; this mode does
not download individual members. No additional ensemble-selection flag is
needed.

Using `--gridded` requires `xarray`, `dask` (with array support), `zarr`, and
`gcsfs` in your Python environment. These libraries are not installed by this
package and must be provided separately. Cyclone and weight downloads do not
require them.

WeatherNext 2 provides experimental global medium-range ensemble forecasts
at 0.25° resolution, initialized at 00, 06, 12, and 18 UTC, with six-hour
forecast steps out to 15 days. See Google's [WeatherNext 2 model guide](https://developers.google.com/weathernext/guides/models-wn2).
The ensemble-mean source is:

```text
gs://weathernext/weathernext_2_0_0_mean/zarr/<year>_to_<next-year>/predictions.zarr
```

Downloading these gridded data requires a Google account approved for
WeatherNext data access. If your account has not been approved, complete the
[WeatherNext Data Request form](https://docs.google.com/forms/d/e/1FAIpQLSeCf1JY8G78UDWzbm0ly9kJxfSjUIJT5WyMR_HiNqCm-IHIBg/viewform)
and wait for Google's approval. Configure your local Google Cloud credentials
using the approved account before running `--gridded`.
`--gridded` supports only the `2022_to_2023`, `2023_to_2024`, and
`2024_to_2025` datasets, selected with `--year 2022`, `--year 2023`, and
`--year 2024`, respectively.

```bash
weathernext-download --gridded --year 2022 --var sst
weathernext-download --gridded --year 2022,2023 --var sst,msl
weathernext-download --gridded --var z300,z500,u10,v10
```

`--var` is required. `--year 2022` selects `2022_to_2023`, and
`--year 2022,2023` selects that period plus `2023_to_2024`. Omitting `--year`
selects all three periods: `2022_to_2023`, `2023_to_2024`, and `2024_to_2025`.
Only starting years 2022, 2023, and 2024 are supported.

| Selection | Source variable | Meaning |
| --- | --- | --- |
| `sst` | `sea_surface_temperature` | Sea surface temperature |
| `msl` | `mean_sea_level_pressure` | Mean sea-level pressure |
| `t2m` | `2m_temperature` | Temperature at 2 m |
| `u10` | `10m_u_component_of_wind` | Eastward wind at 10 m |
| `v10` | `10m_v_component_of_wind` | Northward wind at 10 m |
| `tp` | `total_precipitation_6hr` | Six-hour accumulated precipitation |
| `z<level>` | `geopotential` | Geopotential |
| `q<level>` | `specific_humidity` | Specific humidity |
| `t<level>` | `temperature` | Temperature |
| `u<level>` | `u_component_of_wind` | Eastward wind |
| `v<level>` | `v_component_of_wind` | Northward wind |
| `w<level>` | `vertical_velocity` | Vertical velocity |

Pressure-level variables require a level suffix in hPa: `50`, `100`, `150`,
`200`, `250`, `300`, `400`, `500`, `600`, `700`, `850`, `925`, or `1000`.
For example, `z300` is valid but `z` is not. Levels are selected by coordinate
value, not array index. No unit conversion is performed.

Each variable is saved under its own `<var>_zarr` directory, with one Zarr
store per period inside it, such as `./sst_zarr/sst_2022_to_2023.zarr`. Use
`--output-dir` to change the root that `<var>_zarr` directories are created
under. All times, forecast steps, and grid points in the chosen stores are retained.
Pressure-level output variables are named, for example, `geopotential_300hPa`.
Existing destinations are skipped. Writes first use a `.zarr.part` directory;
failed partial outputs are retained and must be moved aside before retrying.
This mode does not resume partial downloads or provide NetCDF output.
Failures produce a nonzero exit status. A Dask progress bar displays writing
progress.

### Gridded data storage sizes

Gridded forecasts require substantial disk space even for one variable and
one period. The following local Zarr sizes were measured with `du -sh` for
the `2022_to_2023` dataset using the standalone reference scripts:

| Variable | Zarr directory | Reported disk usage |
| --- | --- | ---: |
| Sea surface temperature (`sst`) | `sst_zarr/sst_2022_to_2023.zarr` | 154 GiB |
| Eastward wind at 10 m (`u10`) | `u10_zarr/u10_2022_to_2023.zarr` | 310 GiB |
| Northward wind at 10 m (`v10`) | `v10_zarr/v10_2022_to_2023.zarr` | 313 GiB |
| Geopotential at 300 hPa (`z300`) | `z300_zarr/z300_2022_to_2023.zarr` | 247 GiB |
| Mean sea-level pressure (`msl`) | `msl_zarr/msl_2022_to_2023.zarr` | 245 GiB |

## Cyclone forecast products

Weather Lab provides experimental cyclone predictions paired with observed
tracks for verification. Every model below is available as an ensemble mean
(`--ensemble_mean`), a full ensemble of member tracks (`--ensemble`), or both
(`--both`), in CSV (`--csv`) or ATCF (`--atcf`) format.

| Model | Model long name | Option | Products | Full-ensemble members | Formats | Initialization cycles | Temporal coverage |
| --- | --- | --- | --- | ---: | --- | --- | --- |
| OPER | WeatherNext Cyclones Operational | `--oper` (default) | Ensemble mean and full ensemble | 50 | CSV and ATCF | 00, 06, 12, and 18 UTC | 2025-06-12 onward |
| WNV3 | WeatherNext 3 Cyclones | `--wnv3` | Ensemble mean and full ensemble | 64 | CSV and ATCF | 00, 06, 12, and 18 UTC; 2025 only: 06 and 18 UTC | 2024-01-01 onward |
| FNV3P2 | WeatherNext 2 Cyclones (r2) | `--v3p2` | Ensemble mean and full ensemble | 50 | CSV and ATCF | 00, 06, 12, and 18 UTC | 2022-01-01 onward |
| FNV3P1 | WeatherNext 2 Cyclones (r1) | `--v3p1` | Ensemble mean and full ensemble | 50 | CSV and ATCF | 00, 06, 12, and 18 UTC | 2022-01-01 onward |
| FNV3P0 | WeatherNext 2 Cyclones (r0) | `--v3p0` | Ensemble mean and full ensemble | 50 | CSV and ATCF | 00, 06, 12, and 18 UTC | 2022-01-01 through 2026-05-28 12 UTC |
| FNV3 large ensemble | WeatherNext 2 Cyclones (r2, 1,000 members) | `--v3p2LE` | Ensemble mean and full ensemble | 1,000 | CSV and ATCF | 00, 06, 12, and 18 UTC | 2025-10-18 onward; some cycles are unavailable |

The member count applies to the full-ensemble product selected with
`--ensemble`. The `--ensemble_mean` product contains the corresponding
ensemble-mean tracks, and `--both` downloads both products.

Coverage was checked against the Weather Lab download endpoints on 2026-09-03
and may expand or contain isolated gaps. An unavailable upstream file is
reported as a failed download. See Google's [Weather Lab
guide](https://developers.google.com/weathernext/guides/weatherlab) for its
description and terms for experimental cyclone forecast data.

## Cyclone usage

All cyclone-product commands require `--cyclone`. Without it, cyclone options
are rejected.

Download one forecast cycle:

```bash
weathernext-download --cyclone --time 2026070100 --ensemble_mean
```

Download both products for all four cycles on one day:

```bash
weathernext-download --cyclone --date 20260701 --both
```

Download a month or year:

```bash
weathernext-download --cyclone --date 202607 --both
weathernext-download --cyclone --date 2026 --both
```

Download ATCF files from the FNV3P2 model:

```bash
weathernext-download --cyclone --date 20220101 --v3p2 --both --atcf
```

### Time selection

- `--time YYYYMMDDHH` downloads one cycle. The hour must be `00`, `06`, `12`,
  or `18`.
- `--date YYYYMMDD` downloads all four cycles on one day.
- `--date YYYYMM` downloads all four cycles for every day in one month.
- `--date YYYY` downloads all four cycles for every day in one year.
- Date selections are capped at the date obtained from current UTC time minus
  24 hours and restricted to the selected model's temporal coverage. A period
  with no overlap exits with an error instead of sending invalid requests.
- With neither option, all cycles within the selected model's temporal coverage
  are downloaded through the date obtained from current UTC time minus 24
  hours.

### Product selection

- `--ensemble_mean` or `--ensemble-mean`
- `--ensemble`
- `--both` (default)

### File format

- `--csv` (default)
- `--atcf`

### Model selection

- `--oper` for `OPER` (default)
- `--wnv3` for `WNV3`
- `--v3p2` for `FNV3P2`
- `--v3p1` for `FNV3P1`
- `--v3p0` for `FNV3P0`
- `--v3p2LE` or `--v3p2le` for `FNV3_LARGE_ENSEMBLE`

Files are stored under `./ensemble_mean` and `./ensemble` in the directory
where the command is run. Existing non-empty files are skipped. Each new file
is first written to a temporary file and moved into place only after the
download completes.

Run `weathernext-download --help` for all options, including timeout and retry
settings. `--timeout` and `--retries` apply to both download modes.

## License

MIT
