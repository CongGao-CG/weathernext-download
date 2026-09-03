# weathernext-download

`weathernext-download` downloads paired tropical-cyclone forecast files from
Google DeepMind Weather Lab. It supports ensemble and ensemble-mean products,
CSV and ATCF formats, and the OPER and FNV3 model families.

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

## Available products

Weather Lab provides experimental cyclone predictions paired with observed
tracks for verification. Every model below is available as an ensemble mean
(`--ensemble_mean`), a full ensemble of member tracks (`--ensemble`), or both
(`--both`), in CSV (`--csv`) or ATCF (`--atcf`) format.

| Model | Model long name | Option | Products | Formats | Initialization cycles | Temporal coverage |
| --- | --- | --- | --- | --- | --- | --- |
| OPER | WeatherNext Cyclones Operational | `--oper` (default) | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC | 2025-06-12 onward |
| FNV3P2 | WeatherNext 2 Cyclones (r2) | `--v3p2` | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC | 2022-01-01 onward |
| FNV3P1 | WeatherNext 2 Cyclones (r1) | `--v3p1` | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC | 2022-01-01 onward |
| FNV3P0 | WeatherNext 2 Cyclones (r0) | `--v3p0` | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC | 2022-01-01 through 2026-05-28 12 UTC |
| FNV3 large ensemble | WeatherNext 2 Cyclones (r2, 1000 members) | `--v3p2LE` | Ensemble mean and ensemble members | CSV and ATCF | 00, 06, 12, and 18 UTC | 2025-10-18 onward; some cycles are unavailable |

Coverage was checked against the Weather Lab download endpoints on 2026-09-03
and may expand or contain isolated gaps. An unavailable upstream file is
reported as a failed download. See Google's [Weather Lab
guide](https://developers.google.com/weathernext/guides/weatherlab) for its
description and terms for experimental cyclone forecast data.

## Usage

Download one forecast cycle:

```bash
weathernext-download --time 2026070100 --ensemble_mean
```

Download both products for all four cycles on one day:

```bash
weathernext-download --date 20260701 --both
```

Download a month or year:

```bash
weathernext-download --date 202607 --both
weathernext-download --date 2026 --both
```

Download ATCF files from the FNV3P2 model:

```bash
weathernext-download --date 20220101 --v3p2 --both --atcf
```

### Time selection

- `--time YYYYMMDDHH` downloads one cycle. The hour must be `00`, `06`, `12`,
  or `18`.
- `--date YYYYMMDD` downloads all four cycles on one day.
- `--date YYYYMM` downloads all four cycles for every day in one month.
- `--date YYYY` downloads all four cycles for every day in one year.
- With neither option, all cycles from `2022-01-01` through the UTC date 24
  hours before execution are downloaded.

### Product selection

- `--ensemble_mean` or `--ensemble-mean`
- `--ensemble`
- `--both` (default)

### File format

- `--csv` (default)
- `--atcf`

### Model selection

- `--oper` for `OPER` (default)
- `--v3p2` for `FNV3P2`
- `--v3p1` for `FNV3P1`
- `--v3p0` for `FNV3P0`
- `--v3p2LE` or `--v3p2le` for `FNV3_LARGE_ENSEMBLE`

Files are stored under `./ensemble_mean` and `./ensemble` in the directory
where the command is run. Existing non-empty files are skipped. Each new file
is first written to a temporary file and moved into place only after the
download completes.

Run `weathernext-download --help` for all options, including timeout and retry
settings.

## License

MIT
