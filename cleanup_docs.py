"""
Remove old documentation and test files, keep only essential ones
"""
import os

def cleanup_docs():
    """Remove old documentation files."""
    
    print("🧹 Cleaning up old documentation and test files...\n")
    
    # Old documentation files to remove (keep only essential ones)
    docs_to_remove = [
        "API_QUOTA_ISSUE.md",
        "CHANGES_SUMMARY.md",
        "CODEBASE_ANALYSIS.md",
        "DOCUMENTATION_STRATEGY.md",
        "ELEVENLABS_BLOCKED_SOLUTION.md",
        "ENDPOINT_FIX.md",
        "LOGGING_GUIDE.md",
        "QUICK_REFERENCE.md",
        "QUICK_START.md",
        "READY_TO_TEST.md",
        "REFACTORING_SUMMARY.md",
        "SOLUTION_STEPS.md",
        "START_HERE.md",
        "STUDIO_QUALITY_IMPLEMENTATION.md",
        "TROUBLESHOOTING_UPLOAD.md",
    ]
    
    # Keep these essential docs:
    # - README.md (main documentation)
    # - FINAL_STRUCTURE.md (current structure reference)
    
    # Old test files to remove
    test_files_to_remove = [
        "test_upload.py",  # Already tested, not needed
        "test_gemini_output.json",  # Test output, can be regenerated
    ]
    
    # Keep these test files:
    # - test_pipeline.py (useful for testing Gemini extraction)
    
    # Remove old docs
    removed_count = 0
    for doc_file in docs_to_remove:
        if os.path.exists(doc_file):
            try:
                os.remove(doc_file)
                print(f"✅ Removed: {doc_file}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {doc_file}: {e}")
    
    # Remove old test files
    for test_file in test_files_to_remove:
        if os.path.exists(test_file):
            try:
                os.remove(test_file)
                print(f"✅ Removed: {test_file}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {test_file}: {e}")
    
    print(f"\n🎉 Cleanup complete! Removed {removed_count} files")
    print("\n📋 Kept essential files:")
    print("   - README.md (main documentation)")
    print("   - FINAL_STRUCTURE.md (current structure)")
    print("   - test_pipeline.py (Gemini testing)")
    print("   - input/MangaTest.pdf (test PDF)")

if __name__ == "__main__":
    cleanup_docs()
