# Troubleshooting Upload Issue

## Problem

Frontend shows: **"Invalid response from server"**

## Root Cause Analysis

The error occurs at line 460 in `static/index.html`:
```javascript
try {
  const data = JSON.parse(xhr.responseText);
  jobIdSpan.textContent = data.job_id;  // ← Expects 'job_id' field
  // ...
} catch (error) {
  showUploadError("Invalid response from server");  // ← This error
}
```

This means one of two things:
1. The response is not valid JSON
2. The response doesn't have a `job_id` field

## Diagnosis Steps

### Step 1: Check Server Logs

Look at your terminal where `python main.py` is running. You should see:
```
INFO:     127.0.0.1:xxxxx - "POST /api/upload HTTP/1.1" 200 OK
```

If you see `404` or `500`, that's the issue.

### Step 2: Verify Server Reloaded

After changing `routers/upload.py`, you should have seen:
```
INFO:     Detected file change in 'routers/upload.py'
INFO:     Reloading...
```

**If you didn't see this**, the server is still using the old code with `/api/upload` endpoint.

### Step 3: Manual Restart (RECOMMENDED)

Press **CTRL+C** to stop the server, then restart:
```bash
python main.py
```

You should see:
```
Database initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Test with cURL

Open a new terminal and test:
```bash
curl -X POST -F "file=@MangaTest_removed.pdf" http://localhost:8000/api/upload
```

**Expected response:**
```json
{"job_id":"550e8400-e29b-41d4-a716-446655440000"}
```

**If you get 404:**
```json
{"detail":"Not Found"}
```
→ Server hasn't reloaded. Restart manually.

**If you get 500:**
```json
{"detail":"some error message"}
```
→ Check server logs for the actual error.

### Step 5: Test with Python Script

```bash
python test_upload.py MangaTest_removed.pdf
```

This will show detailed request/response information.

## Common Issues & Fixes

### Issue 1: Server Not Reloaded

**Symptom**: Still getting 404 on `/api/upload`

**Fix**:
```bash
# Stop server (CTRL+C)
python main.py
```

### Issue 2: Database Error

**Symptom**: 500 error with "Failed to create job"

**Fix**:
```bash
python reset_database.py
# Type: yes
python main.py
```

### Issue 3: File Permission Error

**Symptom**: 500 error with "Permission denied"

**Fix**:
```bash
# Check uploads directory exists and is writable
mkdir -p static/uploads
chmod 755 static/uploads  # Linux/Mac
# Windows: Right-click → Properties → Security → Edit
```

### Issue 4: Missing Dependencies

**Symptom**: Import errors in logs

**Fix**:
```bash
pip install -r requirements.txt
```

## Quick Fix Checklist

- [ ] Stop server (CTRL+C)
- [ ] Restart server (`python main.py`)
- [ ] Wait for "Database initialized successfully"
- [ ] Refresh browser (CTRL+F5 to clear cache)
- [ ] Try upload again

## Verify Endpoint is Correct

Check the server logs when you try to upload. You should see:

```
INFO:     127.0.0.1:xxxxx - "POST /api/upload HTTP/1.1" 200 OK
```

**NOT:**
```
INFO:     127.0.0.1:xxxxx - "POST /api/upload HTTP/1.1" 404 Not Found
```

## Test Response Format

The upload endpoint should return:
```json
{
  "job_id": "uuid-string-here"
}
```

If it returns anything else, the frontend will show "Invalid response from server".

## Manual Test in Browser

1. Open **http://localhost:8000/docs**
2. Find `POST /api/upload`
3. Click "Try it out"
4. Upload a PDF
5. Click "Execute"
6. Check the response

**Expected:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Next Steps

1. **Restart server** (most likely fix)
2. **Check logs** for actual error
3. **Test with cURL** to isolate issue
4. **Check database** was reset properly

## If Still Not Working

Check these files for errors:
- `routers/upload.py` - Line 24 should be `@router.post("/upload")`
- `main.py` - Line 74 should be `app.include_router(upload.router, prefix="/api")`
- `services/db_service.py` - `create_job()` function
- Database exists at `database/manga_dubbing.db`

## Success Indicators

✅ Server logs show: `"POST /api/upload HTTP/1.1" 200 OK`
✅ Response contains: `{"job_id": "..."}`
✅ Frontend shows: Job ID and status section
✅ Status polling starts automatically

---

**Most Likely Fix**: Just restart the server with `python main.py`
