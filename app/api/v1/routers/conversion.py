import os

from fastapi import APIRouter, UploadFile, File, Depends
from starlette.background import BackgroundTask
from starlette.responses import FileResponse

from app.api.v1.services.conversion_service import ConversionService
from app.utils.custom_exceptions import ConversionError

router = APIRouter()

@router.post(
    "/pdf-to-word",
    summary="Convert PDF to Word Document",
    description="Upload a PDF file to convert it into a DOCX document."
)
async def convert_pdf_to_word(
        file: UploadFile = File(...,description="PDF to be converted"),
        service: ConversionService = Depends()
):
    """
    Endpoint to convert a PDF file to a DOCX file.

    - **file**: The PDF file uploaded via a multipart/form-data request.
    - **service**: Dependency injection of the ConversionService.

    Returns a `FileResponse` to stream the converted DOCX file back to the client.
    """

    try:
        docx_path  = await service.convert_pdf_to_docx(file);
        # The filename the user will see when downloading
        download_filename = f"{os.path.splitext(file.filename)[0]}.docx"
        return FileResponse(
            path=docx_path,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename=download_filename,
            background=BackgroundTask(os.remove, docx_path)  # Clean up the file after sending
        )
    except ConversionError as e:
        # This will be caught by our custom exception handler in main.py
        raise e
