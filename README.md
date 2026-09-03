# weathernext-download

`weathernext-download` downloads paired tropical-cyclone forecast files from
Google DeepMind Weather Lab. It supports ensemble and ensemble-mean products,
CSV and ATCF formats, and the OPER and FNV3 model families.

## Installation

Install from the project directory:

```bash
python -m pip install .
```

For editable development:

```bash
python -m pip install -e .
```

The package has no runtime dependencies outside the Python standard library.

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

