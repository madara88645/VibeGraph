from app.utils.snippet import extract_snippet

print("Testing snippet extraction...")
try:
    print(extract_snippet("app/models.py", "UploadResponse")[3][:100])
except Exception as e:
    print("Failed:", e)
