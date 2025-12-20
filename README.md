<<<<<<< HEAD
# PDF Merger - Streamlit App

A modern, web-based PDF merger built with Streamlit and Python.

## Features
- Drag & Drop Interface - Easy file upload
- File Preview - See file details before merging  
- Customizable Options - Compression, optimization, page order
- Local Processing - No files uploaded to servers
- Instant Download - Get merged PDF immediately

## Installation

1. Clone the repository:

```bash
git clone https://github.com/onikanyinsola31-netizen/pdf-merger-streamlit.git
cd pdf-merger-streamlit
=======
# pdf-merger-streamlit
PDF merger using streamlit app
>>>>>>> 1d604d6ed5a979092193819908b3ef6c878ae7c4

**## Deployment & Debugging Log

This document outlines the steps taken to deploy this Streamlit PDF Merger application to Hugging Face Spaces and the key issues resolved.

### **Final Working Configuration**
- **Space URL**: https://huggingface.co/spaces/onika31/pdf_merger
- **SDK**: Docker
- **Port**: 7860 (mandatory for Hugging Face Docker SDK)
- **Entry Point**: `app.py`

### **Key Issues & Solutions**

| Issue | Symptom | Root Cause | Solution |
|-------|---------|------------|----------|
| **1. Authentication Failure** | `Password authentication is no longer supported` | Hugging Face deprecated password-based Git authentication | Generated a User Access Token and used it for Git operations |
| **2. App Not Updating** | Space showed default template despite uploading `app.py` | Browser cache and port mismatch (`8501` vs `7860`) | 1. Used private browsing mode<br>2. Fixed port configuration (see below) |
| **3. Port Conflict** | Logs showed `URL: http://0.0.0.0:8501` but app wouldn't load | Streamlit default port (`8501`) incompatible with Hugging Face Docker SDK | Set port to `7860` using:<br>• `ENV STREAMLIT_SERVER_PORT=7860` in Dockerfile<br>• `.streamlit/config.toml` with `port = 7860` |
| **4. Cached Builds** | Build logs showed `CACHED` on all steps, changes ignored | Docker layer caching preventing updates | Broke cache by making a minor commit to `README.md` |
| **5. Missing Source Files** | Build error: `"/src": not found` | Dockerfile referenced non-existent `src/` directory | Replaced Dockerfile with correct configuration |

### **Critical Files for Deployment**

**1. Dockerfile** (Must be exactly this for Hugging Face):
```dockerfile
FROM python:3.13-slim
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV STREAMLIT_SERVER_PORT=7860
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
