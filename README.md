# weathernext-download

`weathernext-download` downloads pretrained WeatherNext model weights and
paired tropical-cyclone forecast files. Cyclone products come from Google
DeepMind Weather Lab. Model weights come from Google's public `dm_graphcast`
bucket by default, with
[`CONGG/weathernext-weight`](https://huggingface.co/CONGG/weathernext-weight)
available as an optional Hugging Face mirror.

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

The package has no third-party Python runtime dependencies. Both cyclone files
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

The model implementations and original model inventory are maintained in
Google DeepMind's [WeatherNext repository](https://github.com/google-deepmind/weathernext#provided-pretrained-models).
The model weights are separate from this package and remain subject to their
own license and terms.

## Cyclone forecast products

Weather Lab provides experimental cyclone predictions paired with observed
tracks for verification. Every model below is available as an ensemble mean
(`--ensemble_mean`), a full ensemble of member tracks (`--ensemble`), or both
(`--both`), in CSV (`--csv`) or ATCF (`--atcf`) format.

| Model | Model long name | Option | Products | Formats | Initialization cycles | Temporal coverage |
| --- | --- | --- | --- | --- | --- | --- |
| OPER | WeatherNext Cyclones Operational | `--oper` (default) | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC | 2025-06-12 onward |
| WNV3 | WeatherNext 3 Cyclones | `--wnv3` | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC; 2025 only: 06 and 18 UTC | 2024-01-01 onward |
| FNV3P2 | WeatherNext 2 Cyclones (r2) | `--v3p2` | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC | 2022-01-01 onward |
| FNV3P1 | WeatherNext 2 Cyclones (r1) | `--v3p1` | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC | 2022-01-01 onward |
| FNV3P0 | WeatherNext 2 Cyclones (r0) | `--v3p0` | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC | 2022-01-01 through 2026-05-28 12 UTC |
| FNV3 large ensemble | WeatherNext 2 Cyclones (r2, 1000 members) | `--v3p2LE` | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC | 2025-10-18 onward; some cycles are unavailable |

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
