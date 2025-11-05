import asyncio
import logging
from pathlib import Path

import aiohttp
from aiolimiter import AsyncLimiter

from . import models


BASE_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


class Client:
    def __init__(self, logger: logging.Logger, session: aiohttp.ClientSession, *, agent: str, concurrency: int = 4):
        self.session: aiohttp.ClientSession = session
        self.limiter: AsyncLimiter = AsyncLimiter(max_rate=10, time_period=1)
        self.semaphore: asyncio.Semaphore = asyncio.Semaphore(concurrency)
        self.headers: dict[str, str] = {"User-Agent": agent}
        self.logger: logging.Logger = logger

    async def download_latest_10k_filing(
        self, cik: models.CIK, dest_dir: Path
    ) -> models.Filing | None:
        async with self.semaphore:
            url = await self._get_latest_10k_url(cik)
            if not url:
                return None

            filename = url.split("/")[-1]
            dest = dest_dir / filename

            async with self.limiter, self.session.get(url, headers=self.headers) as resp:
                resp.raise_for_status()
                content = await resp.read()
            _ = dest.write_bytes(content)
            return models.Filing(cik=cik, url=url, path=dest)

    async def _get_latest_10k_url(self, cik: models.CIK) -> str | None:
        async with self.limiter:
            url = BASE_URL.format(cik=str(cik))
            async with self.session.get(url, headers=self.headers) as resp:
                if resp.status != 200:
                    self.logger.warning("Skipping CIK %s: HTTP %s", cik, resp.status)
                    return None
                resp.raise_for_status()
                data = await resp.json()  # pyright: ignore[reportAny]

        filings = data["filings"]["recent"]  # pyright: ignore[reportAny]
        for i, form in enumerate(filings["form"]):  # pyright: ignore[reportAny]
            if form == "10-K":
                accession: str = filings["accessionNumber"][i].replace("-", "")  # pyright: ignore[reportAny]
                primary: str = filings["primaryDocument"][i]  # pyright: ignore[reportAny]
                return f"https://www.sec.gov/Archives/edgar/data/{str(cik)}/{accession}/{primary}"
        self.logger.warning("10-K not found for: %s", str(cik))
        return None
