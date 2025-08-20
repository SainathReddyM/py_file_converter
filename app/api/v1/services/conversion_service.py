import asyncio
import io
import os
import shutil
import uuid
from typing import List
from zipfile import ZipFile

import fitz
from PIL import Image
from fastapi import UploadFile
from pdf2docx import Converter
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.utils.custom_exceptions import ConversionError, FileValidationError


class ConversionService:
    def _validate_pdf_file(self, file: UploadFile):
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
        self._validate_pdf_file(file)

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

    def _validate_image_files(self, files: List[UploadFile]):
        """Validates if the uploaded files are images."""
        if not files:
            raise FileValidationError("No files were uploaded.")

        allowed_content_types = ["image/jpeg", "image/png", "image/gif", "image/bmp"]
        for file in files:
            if file.content_type not in allowed_content_types:
                raise FileValidationError(f"Invalid file type: {file.content_type}. Only images are accepted.")

    async def convert_images_to_pdf(self, files: List[UploadFile]) -> str:
        """
        Converts one or more uploaded image files into a single PDF document.
        Each image is placed on its own page, scaled to fit while preserving aspect ratio.
        """
        self._validate_image_files(files)
        # This entire block is CPU/IO-bound, so we run it in a threadpool
        def _processing_task():
            # Create a new PDF document in memory
            pdf_doc = fitz.open()
            # Define the page size (A4)
            page_width, page_height = fitz.paper_size("a4")
            for file_upload in files:
                # Read image into memory
                image_bytes = file_upload.file.read()
                # Open image with Pillow to get its dimensions
                with Image.open(io.BytesIO(image_bytes)) as img:
                    img_width, img_height = img.size
                # Create a new page
                page = pdf_doc.new_page(width=page_width, height=page_height)
                # --- Aspect Ratio Calculation ---
                # Calculate the rectangle to place the image in.
                # This scales the image to fit the page while preserving its aspect ratio.
                scale_w = page_width / img_width
                scale_h = page_height / img_height
                scale = min(scale_w, scale_h)
                final_w = img_width * scale
                final_h = img_height * scale
                # Center the image on the page
                x0 = (page_width - final_w) / 2
                y0 = (page_height - final_h) / 2
                x1 = x0 + final_w
                y1 = y0 + final_h
                image_rect = fitz.Rect(x0, y0, x1, y1)
                # --------------------------------
                # Insert the image onto the page
                page.insert_image(rect=image_rect, stream=image_bytes)
            # Save the result to a temporary file
            unique_id = uuid.uuid4()
            pdf_filename = f"{unique_id}.pdf"
            pdf_path = os.path.join(settings.TEMP_FILE_DIR, pdf_filename)
            pdf_doc.save(pdf_path)
            pdf_doc.close()
            return pdf_path
        try:
            # Run the entire processing function in a threadpool
            return await run_in_threadpool(_processing_task)
        except Exception as e:
            raise ConversionError(f"An unexpected error occurred during image to PDF conversion: {repr(e)}")

    async def convert_pdf_to_images(self, file: UploadFile) -> str:
        """
        Converts each page of an uploaded PDF file into a PNG image,
        then zips all the images and returns the path to the zip file.
        """
        self._validate_pdf_file(file)
        # 1. Await the file read here, in the async function.
        pdf_bytes = await file.read()
        # This entire block is CPU/IO-bound, so we run it in a threadpool
        def _processing_task():
            job_id = str(uuid.uuid4())
            # Create a dedicated temporary directory for this conversion job
            temp_image_dir = os.path.join(settings.TEMP_FILE_DIR, job_id)
            os.makedirs(temp_image_dir)
            zip_filename = f"{job_id}.zip"
            zip_path = os.path.join(settings.TEMP_FILE_DIR, zip_filename)
            try:
                # Open the PDF from in-memory bytes
                pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                # Render each page as a high-quality PNG
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc.load_page(page_num)
                    # Use a DPI of 200 for good quality
                    pix = page.get_pixmap(dpi=200)
                    image_path = os.path.join(temp_image_dir, f"page_{page_num + 1}.png")
                    pix.save(image_path)
                pdf_doc.close()
                # Create the zip file
                with ZipFile(zip_path, 'w') as zipf:
                    # Walk through the temp directory and add files to the zip
                    for root, dirs, files in os.walk(temp_image_dir):
                        for file in files:
                            zipf.write(os.path.join(root, file), arcname=file)
                return zip_path
            except Exception as e:
                # Re-raise with our custom exception
                raise ConversionError(f"An unexpected error occurred during PDF to image conversion: {repr(e)}")
            finally:
                # CRUCIAL CLEANUP: Ensure the temporary image directory is always removed
                if os.path.exists(temp_image_dir):
                    shutil.rmtree(temp_image_dir)
        try:
            # Run the entire processing function in a threadpool
            return await run_in_threadpool(_processing_task)
        except Exception as e:
            # Propagate any exceptions from the threadpool
            raise e