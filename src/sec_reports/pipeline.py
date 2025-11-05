import asyncio
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import logging
from pathlib import Path

from . import models, ports


@dataclass
class Sec10KConfig:
    client: ports.ClientProtocol
    pdf_workers: int
    converter: ports.Converter

    def __post_init__(self):
        if self.pdf_workers <= 0:
            raise ValueError("pdf_workers must be a positive non-zero integer")


class Sec10K:
    def __init__(self, logger: logging.Logger, cfg: Sec10KConfig):
        self.pdf_workers: int = cfg.pdf_workers
        self.converter: ports.Converter = cfg.converter
        self.client: ports.ClientProtocol = cfg.client

        self.logger: logging.Logger = logger

        self.queue: asyncio.Queue[models.Filing | None] = asyncio.Queue()
        self.pool: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=cfg.pdf_workers)

    def close(self):
        self.pool.shutdown(wait=True)

    async def run(self, ciks: list[models.CIK], destination: Path):
        if not destination.is_dir():
            raise ValueError(f"destination_folder must be a directory, got {destination}")

        async with asyncio.TaskGroup() as tg:
            producers = [tg.create_task(self._fetch(cik, destination)) for cik in ciks]
            _consumer = tg.create_task(self._convert())

            _ = await asyncio.gather(*producers)
            await self.queue.put(None)

    async def _fetch(self, cik: models.CIK, destination: Path):
        if filing := await self.client.download_latest_10k_filing(cik, destination):
            self.logger.debug("Fetched 10-K filing for %s", str(cik))
            await self.queue.put(filing)

    async def _convert(self):
        loop = asyncio.get_running_loop()
        while True:
            filing = await self.queue.get()
            if filing is None:
                self.queue.task_done()
                return
            self.logger.debug("Creating PDF for %s...", str(filing.cik))

            await loop.run_in_executor(self.pool, self.converter, filing)

            self.logger.debug("Finished creating PDF for %s.", str(filing.cik))
            self.queue.task_done()
