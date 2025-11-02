from pathlib import Path
from typing import Callable, Protocol

from . import models


class ClientProtocol(Protocol):
    async def download_latest_10k_filing(
        self,
        cik: models.CIK,
        dest_dir: Path,
    ) -> models.Filing | None: ...


Converter = Callable[[models.Filing], None]
