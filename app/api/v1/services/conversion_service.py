import os
import uuid
from fastapi import UploadFile
from pdf2docx import Converter
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.utils.custom_exceptions import ConversionError


class ConversionService:
    def _validate_file(self, file: UploadFile):
        """Validates if the uploaded file is a PDF"""
        if file.content_type != "application/pdf":
            raise ConversionError(f"Invald file type: {file.content_type}. Only PDF files are accepted.")

    async def convert_pdf_to_docx(self, file: UploadFile ) -> str:
        """
        Converts an uploaded PDF file to a DOCX file.

        This method is async, but the core conversion logic (`pdf2docx`) is synchronous.
        We use `run_in_threadpool` to run the blocking I/O and CPU-bound operations
        in a separate thread, preventing the main application event loop from being blocked.
        """
        self._validate_file(file)

        # Generate unique filenames to prevent conflicts
        unique_id = uuid.uuid4()
        pdf_filename = f"{unique_id}.pdf"
        docx_filename = f"{unique_id}.docx"

        pdf_path = os.path.join(settings.TEMP_FILE_DIR, pdf_filename)
        docx_path = os.path.join(settings.TEMP_FILE_DIR, docx_filename)

        try:
            # Save the uploaded file temporaily
            with open(pdf_path, "wb") as buffer:
                buffer.write(await file.read())
            # Run the blocking conversion function in a thread pool
            cv = await run_in_threadpool(Converter, pdf_path)
            await run_in_threadpool(cv.convert, docx_path)
            cv.close()
            return docx_path
        except Exception as e:
            # Catch any error during conversion
            raise ConversionError(f"An unexpected error occurred during conversion: {e}")
        finally:
            # Clean up the temporary PDF file
            if os.path.exists(pdf_path):
                os.remove(pdf_path)