# SEC Reports
Fetches the latest 10-K filings from the U.S. SEC for selected companies and converts them to PDF files.
Implements asynchronous fetching with rate limiting and parallel HTML-to-PDF conversion.

## Requirements
- **Python >= 3.13**
- **wkhtmltopdf** must be installed and available in your system `PATH`, since `pdfkit` depends on it for PDF generation.

Install `wkhtmltopdf` via your package manager, for example:

```bash
sudo apt install wkhtmltopdf
brew install homebrew/cask/wkhtmltopdf
```

## Installation
### Using `uv`
Run directly from source without installation:

```bash
uv run sec-reports --agent "Sample Company AdminContact@sample.com"
```

### Using `pip`
Install locally from source:

```bash
pip install .
```

Or build the wheel and install it:
```bash
uv build
pip install dist/sec_reports-0.1.0-py3-none-any.whl
```

Then `sec-reports` CLI will be available to you
```bash
sec-reports --agent "Sample Company AdminContact@sample.com"
```

## Example
### CLI
The command below downloads the latest 10-K reports for a predefined set of companies and saves them as PDFs under `./downloads`. It will use 2 system threads to convert the htmls to PDF.

```bash
sec-reports --outdir ./downloads --workers 2 --ciks 0001326801 0000789019 --agent "ExampleCorp contact@example.com"
```

**Options:**
- `--outdir`: Directory where reports are saved (default: `./downloads`)
- `--workers`: Number of CPU workers for PDF conversion (default: `8`)
- `--agent`: Custom User-Agent string required by SEC
- `--ciks`: Space-separated list of CIKs (default: six major companies)
- `--verbose`: Enable info-level logging

### Library Example

```python
import asyncio
from pathlib import Path
import aiohttp

from sec_reports import pipeline, html, converter, models


async def download():
    async with aiohttp.ClientSession() as session:
        cfg = pipeline.Sec10KConfig(
            client=html.Client(session, agent="ExampleCorp contact@example.com"),
            pdf_workers=8,
            converter=converter.with_pdfkit,
            verbose=True,
        )
        runner = pipeline.Sec10K(cfg)
        ciks = [models.CIK("0000320193")]
        await runner.run(ciks, Path("./downloads"))
        runner.close()

asyncio.run(download())
```

## Development
Install dependencies (including dev tools):

```bash
make install
```

The provided `Makefile` includes the following shortcuts:

```bash
make lint    # Run static checks and formatting
make test    # Run pytest test suite
make clean   # Remove build artifacts
```

Tests include fake clients to verify the pipeline end-to-end (`test_service.py`).
