# Endpoint Fix - 404 Error Resolved

## Issue

The `/api/upload` endpoint was returning 404 because of duplicate `/api` prefix.

## Root Cause

In `routers/upload.py`, the endpoint was defined as:
```python
@router.post("/api/upload")  # ❌ Wrong
```

But in `main.py`, the router was included with:
```python
app.include_router(upload.router, prefix="/api", tags=["upload"])
```

This created the endpoint at `/api/api/upload` instead of `/api/upload`.

## Fix Applied

Changed `routers/upload.py` line 24:
```python
@router.post("/upload")  # ✅ Correct
```

Now the endpoint is correctly available at `/api/upload`.

## Correct API Endpoints

After the fix, all endpoints are:

### Upload
```
POST /api/upload
```

### Status
```
GET /api/status/{job_id}
```

### Extract Dialogs
```
POST /api/extract-dialogs
```

### Download
```
GET /api/download/{job_id}
```

### Health Check
```
GET /health
```

### Root
```
GET /
```

## How to Test

### Option 1: Swagger UI (Recommended)
1. Open http://localhost:8000/docs
2. Find `POST /api/upload` endpoint
3. Click "Try it out"
4. Upload a PDF file
5. Click "Execute"

### Option 2: cURL
```bash
curl -X POST -F "file=@test.pdf" http://localhost:8000/api/upload
```

### Option 3: Python
```python
import requests

with open('test.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/upload',
        files={'file': f}
    )
    print(response.json())
```

## Next Steps

1. **Restart the server** (if not using auto-reload)
   - Press CTRL+C to stop
   - Run `python main.py` again
   - Or just wait for auto-reload to detect the change

2. **Test the upload endpoint**
   - Go to http://localhost:8000/docs
   - Try uploading a PDF

3. **Verify the response**
   - Should return `{"job_id": "uuid-string"}`
   - Status code should be 200

## Status

✅ **Fixed** - Endpoint now correctly available at `/api/upload`

The server should auto-reload and pick up the change automatically since you're running with `reload=True`.
