# Contributing

Thanks for considering a contribution to `weathernext-download`.

## Reporting issues

Use [GitHub Issues](https://github.com/CongGao-CG/weathernext-download/issues)
to report bugs or request features. Include the command you ran, the full
error output, and your Python version.

## Development setup

```bash
git clone https://github.com/CongGao-CG/weathernext-download.git
cd weathernext-download
pip install -e .
```

`--gridded` support requires `xarray`, `dask[array]`, `zarr`, and `gcsfs`.
Install them separately if you're working on `src/weathernext_download/gridded.py`:

```bash
pip install xarray "dask[array]" zarr gcsfs
```

## Running tests

The test suite uses only Python's standard-library `unittest`, so no
third-party test framework is required:

```bash
python -m unittest discover -s tests
```

Tests covering `--gridded` are skipped automatically if `xarray`, `dask`,
`zarr`, or `gcsfs` are not installed.

## Submitting changes

- Keep pull requests focused on one change.
- Add or update tests in `tests/` for any behavior change.
- Update `README.md` if the change affects documented behavior or output
  paths.
- Bump the version in both `pyproject.toml` and
  `src/weathernext_download/__init__.py` together.
