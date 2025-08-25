# py_file_converter
Python FastAPI File converter

## Steps to setup this project in local

- Run the following Commands

1. python -m venv venv
2. pip install -r requirements.txt

## Running the application on local

1. Make the following changes to .env file:
   - Change value of LIBREOFFICE_PATH variable. Point it to soffice.exe file in libreoffice installation folder
   - Change value of VALID_API_KEYS_STR. Add your seurity keys (comma-seperated)
2. In your terminal (make sure you are in the root directory and (venv) is active), run Uvicorn:
   - `uvicorn app.main:app --reload`
   - The --reload flag will automatically restart the server when you make code changes.
3. Test with the Interactive Docs:
   - Open your browser and navigate to `http://127.0.0.1:8000/docs`.
   - You will see the Swagger UI documentation for API.
   - Expand the POST `/api/v1/conversion/pdf-to-word` endpoint.
   - Click "Try it out".
   - Click the "Choose File" button and select a PDF from your computer.
   - Click "Execute".