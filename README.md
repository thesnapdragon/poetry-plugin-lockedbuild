# Poetry Plugin: Locked Build

This package is a plugin that allows the building of wheel files with locked packages from `poetry.lock`.

## Installation

The easiest way to install the `lockedbuild` plugin is via the `self add` command of Poetry.

```bash
poetry self add poetry-plugin-lockedbuild
```

If you used `pipx` to install Poetry you can add the plugin via the `pipx inject` command.

```bash
pipx inject poetry poetry-plugin-lockedbuild
```

Otherwise, if you used `pip` to install Poetry you can add the plugin packages via the `pip install` command.

```bash
pip install poetry-plugin-lockedbuild
```


## Usage

The plugin provides an `lockedbuild` command to build a wheel file with locked packages.

```bash
poetry lockedbuild
```

### Available options

* `--with`: The optional dependency groups to include when exporting.
