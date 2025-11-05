import logging
from pathlib import Path

import pytest

from sec_reports import models, pipeline

pytestmark = pytest.mark.asyncio

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FakeClient:
    def __init__(self):
        self.called: bool = False

    async def download_latest_10k_filing(self, cik: models.CIK, dest_dir: Path):
        dest = dest_dir / f"{cik}.html"
        _ = dest.write_text("<html><body>Lorem ipsum</body></html>")
        self.called = True
        return models.Filing(cik, "fake://url", dest)


def fake_converter(filing: models.Filing):
    new_path = filing.path.with_suffix(".pdf")
    _ = filing.path.rename(new_path)


async def test_sec10k_pipeline(tmp_path: Path):
    # Given
    fake_client = FakeClient()
    cfg = pipeline.Sec10KConfig(
        client=fake_client,
        pdf_workers=2,
        converter=fake_converter,
    )
    cik = models.CIK("0000000001")
    runner = pipeline.Sec10K(logger, cfg)

    # When
    await runner.run([cik], tmp_path)
    runner.close()

    # Then
    done_files = list(tmp_path.glob("*.pdf"))
    assert fake_client.called
    assert len(done_files) == 1
    assert "0000000001.pdf" == done_files[0].name
