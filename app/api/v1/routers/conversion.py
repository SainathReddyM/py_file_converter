import logging
import os
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends
from starlette.background import BackgroundTask
from starlette.responses import FileResponse

from app.api.v1.services.conversion_service import ConversionService
from app.utils.custom_exceptions import ConversionError, AppException

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    logger.info("--- LOG: pdf-to-word controller endpoint CALLED ---")

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

@router.post(
    "/word-to-pdf",
    summary="Convert Word Document to PDF",
    description="Upload a DOCX file to convert it into a PDF document."
)
async def convert_word_to_pdf(
    file: UploadFile,
    service: ConversionService = Depends()
):
    """
        Endpoint to convert a DOCX file to a PDF file.
        """
    logger.info("--- LOG: word-to-pdf controller endpoint CALLED ---")
    try:
        pdf_path = await service.convert_docx_to_pdf(file)

        # The filename the user will see when downloading
        download_filename = f"{os.path.splitext(file.filename)[0]}.pdf"

        return FileResponse(
            path=pdf_path,
            media_type='application/pdf',
            filename=download_filename,
            background=BackgroundTask(os.remove, pdf_path)
        )
    except AppException as e:
        # This will be caught by our custom exception handler in main.py
        raise e

@router.post(
    "/images-to-pdf",
    summary="Convert Images to a single PDF",
    description="Upload one or more image files (JPG, PNG, etc.) to convert them into a single PDF document."
)
async def convert_images_to_pdf(
    files: List[UploadFile] = File(..., description="One or more image files to be converted."),
    service: ConversionService = Depends()
):
    """
    Endpoint to convert multiple image files into a single PDF.
    """
    logger.info(f"--- LOG: images-to-pdf controller endpoint CALLED with {len(files)} file(s) ---")
    try:
        pdf_path = await service.convert_images_to_pdf(files)

        # The filename the user will see when downloading
        download_filename = "converted_images.pdf"

        return FileResponse(
            path=pdf_path,
            media_type='application/pdf',
            filename=download_filename,
            background=BackgroundTask(os.remove, pdf_path)
        )
    except AppException as e:
        raise e

@router.post(
    "/pdf-to-images",
    summary="Convert PDF to Images (zipped)",
    description="Upload a PDF file to convert each page into a PNG image. Returns a zip file containing all images."
)
async def convert_pdf_to_images(
    file: UploadFile = File(..., description="The PDF file to be converted."),
    service: ConversionService = Depends()
):
    """
    Endpoint to convert a PDF file into a zip archive of images.
    """
    logger.info(f"--- LOG: pdf-to-images controller endpoint CALLED for file: {file.filename} ---")
    try:
        zip_path = await service.convert_pdf_to_images(file)
        # The filename the user will see when downloading
        download_filename = f"{os.path.splitext(file.filename)[0]}.zip"
        return FileResponse(
            path=zip_path,
            media_type='application/zip',  # <-- Correct MIME type for a zip file
            filename=download_filename,
            background=BackgroundTask(os.remove, zip_path)  # Clean up the zip file after sending
        )
    except AppException as e:
        raise e



