import os

import pdfkit  # pyright: ignore[reportMissingTypeStubs]

from . import models


def with_pdfkit(filing: models.Filing) -> None:
    pdf_path = filing.path.with_suffix(".pdf")
    pdfkit.from_file(  # pyright: ignore[reportUnknownMemberType, reportUnusedCallResult]
        str(filing.path),
        str(pdf_path),
        options={
            "enable-local-file-access": None,
        },
    )
    os.remove(filing.path)
