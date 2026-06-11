<div align="center">
  <h1>✨ VibeRAG Analytics</h1>
  <p><strong>Premium Creator Comparative Dashboard</strong></p>

  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
  [![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
  [![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/en-US/docs/Glossary/HTML5)
  [![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
</div>

<br/>

**VibeRAG Analytics** is a high-performance, single-process full-stack RAG Chatbot built specifically for content creators, agencies, and social media analysts. It enables side-by-side comparative analysis of YouTube videos and Instagram Reels to uncover why one piece of content outperforms another, analyze transcript hooks, and provide structured, actionable improvements.

---

## 🌟 Key Features

- **📊 Side-by-Side Analytics**: Compare engagement rates, views, likes, and comments between cross-platform video content instantly.
- **🧠 Local Vector Embeddings**: Uses a lightweight local vector database (Chroma/FAISS) instantiated purely in memory, requiring zero external cloud database fees.
- **💬 Conversational RAG Engine**: Query the underlying transcripts and structure using a real-time streaming chat interface, with full source citations down to the sentence level.
- **🛡️ Resilient Scraper**: Equipped with a fallback engine that synthesizes realistic creator metrics if rate limits or login walls are hit, ensuring your app never crashes in a demo environment.
- **🎨 Glassmorphism UI**: A breathtaking, fluid, dark-mode dashboard built purely with HTML, CSS, and vanilla JS for absolute maximum rendering performance.

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | ⚡ FastAPI, Python 3.10+, Uvicorn | High-performance async python backend |
| **AI & RAG** | 🤖 OpenAI, LangChain, ChromaDB | `gpt-4o-mini` & `text-embedding-3-small` |
| **Frontend** | 🖥️ Vanilla HTML/CSS/JS | Zero Node.js dependency, premium aesthetics |
| **Scraping** | 🕸️ `yt-dlp`, `youtube-transcript-api` | Robust media metadata and subtitle extraction |

---

## 🚀 Local Installation

**1. Clone the repository and navigate inside:**
```bash
git clone https://github.com/mvishnunaidu/VibeRAG-Analysis.git
cd VibeRAG-Analysis
```

**2. Create a clean Python virtual environment and activate it:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
# source venv/bin/activate    # On Mac/Linux
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Configure your API key:**
The application will automatically copy `.env.example` to `.env` if it doesn't exist. Add your OpenAI API key in `.env`:
```env
OPENAI_API_KEY=sk-proj-your_real_openai_key_here
```

**5. Launch the application:**
```bash
python run.py
```
*Open `http://127.0.0.1:8000` in Google Chrome or Edge.*

---

## ☁️ Deployment

This project is configured out-of-the-box for seamless PaaS deployment on platforms like Render or Heroku. 

### 🟣 Deploying to Render
1. Connect your GitHub repository to Render.
2. The provided `render.yaml` blueprint will automatically configure the Web Service.
3. Ensure you set the `OPENAI_API_KEY` environment variable in the Render Dashboard securely.
4. Deploy!

### 🟣 Deploying to Heroku
1. Create a new Heroku app.
2. The provided `Procfile` (`web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT`) will handle the boot process.
3. Set your `OPENAI_API_KEY` in Heroku Config Vars.
4. Push to Heroku: `git push heroku main`

---
*Built by Vishnu Naidu*
