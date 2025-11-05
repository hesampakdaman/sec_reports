import argparse
import asyncio
from dataclasses import dataclass
import logging
from pathlib import Path

import aiohttp

from sec_reports import converter, html, models, pipeline


@dataclass
class Args:
    outdir: Path
    workers: int
    ciks: list[str]
    agent: str
    verbose: bool


def parse_args() -> Args:
    p = argparse.ArgumentParser()
    _ = p.add_argument(
        "--outdir",
        type=Path,
        default=Path("./downloads"),
        help="Directory to where the reports are downloaded. Will be created if they don't exist.",
    )
    _ = p.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of cpu workers dedicated to converting html to pdf.",
    )
    _ = p.add_argument(
        "--agent",
        type=str,
        help="User agent, example: Sample Company Name AdminContact@<sample company domain>.com",
        required=True,
    )
    _ = p.add_argument(
        "--ciks",
        nargs="*",
        default=[
            "0000320193",  # Apple
            "0000886982",  # Goldman Sachs
            "0001018724",  # Amazon
            "0001065280",  # Netflix
            "0001326801",  # Meta
            "0001652044",  # Alphabet
        ],
        help="The 10 digit Central Index Key (CIK). Multiple CIK are separated by space.",
    )
    _ = p.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    ns = p.parse_args()
    return Args(ns.outdir, ns.workers, ns.ciks, ns.agent, ns.verbose)  # pyright: ignore[reportAny]


async def run(logger: logging.Logger, args: Args):
    ciks = [models.CIK(c) for c in args.ciks]
    args.outdir.mkdir(parents=True, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        cfg = pipeline.Sec10KConfig(
            client=html.Client(logger, session, agent=args.agent),
            pdf_workers=args.workers,
            converter=converter.with_pdfkit,
        )
        runner = pipeline.Sec10K(logger, cfg)
        await runner.run(ciks, args.outdir)
        runner.close()


def main():
    args = parse_args()
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(message)s")
    log = logging.getLogger(__name__)

    log.info(f"Starting to fetch {len(args.ciks)} reports...")

    asyncio.run(run(log, args))

    log.info("Done! Reports saved in %s.", args.outdir.absolute())
