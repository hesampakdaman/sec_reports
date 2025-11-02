import asyncio
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Callable

from . import models, ports

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


@dataclass
class Sec10KConfig:
    client: ports.ClientProtocol
    pdf_workers: int
    converter: Callable[[models.Filing], None]
    verbose: bool

    def __post_init__(self):
        if self.pdf_workers <= 0:
            raise ValueError("pdf_workers must be a positive non-zero integer")


class Sec10K:
    def __init__(self, cfg: Sec10KConfig):
        self.pdf_workers: int = cfg.pdf_workers
        self.converter: ports.Converter = cfg.converter
        self.client: ports.ClientProtocol = cfg.client
        self.verbose: bool = cfg.verbose

        self.queue: asyncio.Queue[models.Filing] = asyncio.Queue()
        self.pool: ProcessPoolExecutor = ProcessPoolExecutor()

    def close(self):
        self.pool.shutdown(wait=True)

    async def run(self, ciks: list[models.CIK], destination: Path):
        if not destination.is_dir():
            raise ValueError(f"destination_folder must be a directory, got {destination}")

        producers = [asyncio.create_task(self._fetch(cik, destination)) for cik in ciks]
        consumers = [asyncio.create_task(self._convert()) for _ in range(self.pdf_workers)]

        _ = await asyncio.gather(*producers)
        await self.queue.join()
        for c in consumers:
            _ = c.cancel()

    async def _fetch(self, cik: models.CIK, destination: Path):
        if filing := await self.client.download_latest_10k_filing(cik, destination):
            if self.verbose:
                log.info("Fetched 10-K filing for %s", str(cik))
            await self.queue.put(filing)

    async def _convert(self):
        loop = asyncio.get_running_loop()
        while True:
            filing = await self.queue.get()
            if self.verbose:
                log.info("Creating PDF for %s...", str(filing.cik))
            await loop.run_in_executor(self.pool, self.converter, filing)
            if self.verbose:
                log.info("Finished creating PDF for %s.", str(filing.cik))
            self.queue.task_done()
