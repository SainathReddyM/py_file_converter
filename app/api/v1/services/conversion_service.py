import asyncio
import os
import uuid
from fastapi import UploadFile
from pdf2docx import Converter
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.utils.custom_exceptions import ConversionError, FileValidationError


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

    async def convert_docx_to_pdf(self, file: UploadFile) -> str:
        """Converts an uploaded DOCX file to a PDF file using LibreOffice."""
        print("in convert_docx_to_pdf method")
        self._validate_docx_file(file)
        unique_id = uuid.uuid4()
        docx_filename = f"{unique_id}.docx"
        docx_path = os.path.join(settings.TEMP_FILE_DIR, docx_filename)
        output_dir = settings.TEMP_FILE_DIR
        try:
            # Save the uploaded file temporarily
            with open(docx_path, "wb") as buffer:
                buffer.write(await file.read())
                # Construct the command for LibreOffice
                # This command runs LibreOffice in headless mode, converts the docx to pdf,
                # and specifies the output directory.
                cmd = [
                    settings.LIBREOFFICE_PATH,
                    '--headless',
                    '--convert-to',
                    'pdf',
                    '--outdir',
                    output_dir,
                    docx_path
                ]
                # Execute the command asynchronously
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    # If LibreOffice returns a non-zero exit code, it means an error occurred.
                    error_message = stderr.decode('utf-8') if stderr else "Unknown LibreOffice error."
                    raise ConversionError(f"LibreOffice conversion failed: {error_message}")
                pdf_path = os.path.splitext(docx_path)[0] + ".pdf"
                if not os.path.exists(pdf_path):
                    raise ConversionError("PDF file was not created after conversion process.")
                return pdf_path
        except Exception as e:
            # --- TEMPORARY DEBUGGING ---
            print("\n" + "=" * 50)
            print("DEBUG: CAUGHT AN EXCEPTION IN DOCX TO PDF CONVERSION")
            print(f"EXCEPTION TYPE: {type(e)}")
            print(f"EXCEPTION REPR: {repr(e)}")
            print(f"EXCEPTION STR: {str(e)}")
            print("=" * 50 + "\n")
            # --- END TEMPORARY DEBUGGING ---
            # We'll also use repr(e) in the response for more detail
            raise ConversionError(f"An unexpected error occurred: {repr(e)}")
        finally:
            # Clean up the temporary DOCX file
            if os.path.exists(docx_path):
                os.remove(docx_path)

    def _validate_docx_file(self, file: UploadFile):
        """Validates if the uploaded file is a DOCX."""
        # MIME type for .docx
        valid_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if file.content_type != valid_type:
            raise FileValidationError(f"Invalid file type: {file.content_type}. Only DOCX files are accepted.")

