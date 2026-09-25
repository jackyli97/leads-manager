from pathlib import Path
from uuid import uuid4

from anyio import to_thread
from fastapi import HTTPException, UploadFile, status

UPLOAD_DIR = Path("uploads")
MAX_PDF_SIZE = 10 * 1024 * 1024


async def save_resume(resume: UploadFile) -> str:
    contents = await resume.read(MAX_PDF_SIZE + 1)
    await resume.close()

    if len(contents) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Resume PDF must be 10 MB or smaller",
        )
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume must be a valid PDF file",
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}.pdf"
    await to_thread.run_sync((UPLOAD_DIR / filename).write_bytes, contents)
    return f"/uploads/{filename}"


async def delete_resume(resume_url: str) -> None:
    filename = Path(resume_url).name
    await to_thread.run_sync((UPLOAD_DIR / filename).unlink, True)
