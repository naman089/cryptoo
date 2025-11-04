How to Run the Project

1. Create and activate a virtual environment
---------------------------------------------------
python -m venv .venv
.venv\Scripts\Activate.ps1


2. Install dependencies
---------------------------------------------------
pip install -r requirements.txt

3. Create .env file
---------------------------------------------------
OPENAI_API_KEY=sk-your-real-openai-key
AI_PROVIDER=openai
PORT=8000

4. Run the server
---------------------------------------------------
uvicorn main:app --reload --port 8000

5. Open Swagger UI
---------------------------------------------------
Go to http://localhost:8000/docs to test all APIs
