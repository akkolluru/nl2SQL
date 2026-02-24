Got it 💯 — you only want the run instructions, clean and copy-pasteable (no fluff, just the steps to run the whole project).
Here’s your ready block 👇

⸻


# 🚀 How to Run the Project

### 1️⃣ Clone the Repository
```bash
git clone <your-repo-link>
cd nl2sql_mvp

2️⃣ Install Dependencies

uv pip install -r requirements.txt
# or
pip install -r requirements.txt

3️⃣ Set Up the .env File

Create a file named .env in the root directory:

DB_HOST=127.0.0.1
DB_USER=nl2sql_app
DB_PASS=
DB_NAME=shopdb
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=mistral
DEFAULT_LIMIT=100

4️⃣ Set Up the MySQL Database

mysql -u root -p

Inside MySQL:

CREATE DATABASE shopdb;
USE shopdb;
SOURCE data/seed.sql;
SHOW TABLES;

5️⃣ Start Ollama (Model Server)

Install from https://ollama.com/download
Then run:

ollama pull mistral
ollama serve

6️⃣ Run the FastAPI Backend

Open a new terminal in the project folder:

uvicorn app.main:app --reload

Check health:

curl http://127.0.0.1:8000/health

Expected:

{"status":"ok"}

7️⃣ Run the Streamlit Frontend

Open another terminal:

streamlit run streamlit_app.py

Then visit:

http://localhost:8501

8️⃣ Test the System

In Streamlit, type:

Show total orders per city

Expected result:
	•	Generated SQL displayed
	•	Data fetched from MySQL and shown in table

9️⃣ Stop Everything

Press Ctrl + C in each terminal to stop FastAPI, Streamlit, and Ollama.

---

That’s your final “run the project” section — short, ordered, and ready for your README or report.