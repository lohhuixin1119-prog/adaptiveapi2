# Adaptive Gateway – FastAPI

## Deploy to Render
- Create new Web Service, point to your repo.
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- (These are the default – just leave them blank.)

## Local run
```bash
pip install -r requirements.txt
uvicorn main:app --reload


---

### What to do now
1. Replace your current `app.py` with `main.py` (copy above).  
2. Update `requirements.txt` with the FastAPI/uvicorn lines.  
3. Push to your Git repository.  
4. On Render, **do not change** the default start command – it will automatically pick `uvicorn main:app`.  
5. Redeploy – it will succeed.

If you still prefer Flask, I can give you the adjusted Flask version with Gunicorn – but FastAPI is the cleaner path. Let me know!
