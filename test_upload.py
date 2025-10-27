"""
Quick test script to check if the upload endpoint is working.
"""
import requests
import sys
from pathlib import Path

def test_upload(pdf_path: str):
    """Test the upload endpoint."""
    url = "http://localhost:8000/api/upload"
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"📤 Uploading: {pdf_path}")
    print(f"🎯 Endpoint: {url}")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            response = requests.post(url, files=files, timeout=30)
        
        print(f"\n📊 Status Code: {response.status_code}")
        print(f"📝 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Success!")
            print(f"🆔 Job ID: {data.get('job_id')}")
            print(f"\n📋 Full Response:")
            print(data)
            
            # Test status endpoint
            job_id = data.get('job_id')
            if job_id:
                print(f"\n🔍 Checking status...")
                status_url = f"http://localhost:8000/api/status/{job_id}"
                status_response = requests.get(status_url)
                print(f"Status: {status_response.json()}")
        else:
            print(f"\n❌ Error!")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error: Is the server running?")
        print("Start server with: python main.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Try to find a test PDF
        test_files = [
            "MangaTest_removed.pdf",
            "test.pdf",
            "manga.pdf"
        ]
        pdf_path = None
        for test_file in test_files:
            if Path(test_file).exists():
                pdf_path = test_file
                break
        
        if not pdf_path:
            print("Usage: python test_upload.py <path_to_pdf>")
            print("\nOr place a PDF named 'MangaTest_removed.pdf' in the current directory")
            sys.exit(1)
    
    test_upload(pdf_path)
