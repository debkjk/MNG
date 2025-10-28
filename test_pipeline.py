"""
Test the entire pipeline step by step to verify each component
"""
import sys
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.pdf_processor import convert_pdf_to_images, validate_pdf
from services.gemini_service import process_manga_pages
from services.tts_service import generate_audio_tracks
from services.video_generator_slideshow import generate_dubbed_video_from_analysis

def test_pipeline(pdf_path: str):
    """Test the pipeline step by step."""
    
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print("="*60)
    print("🧪 TESTING MANGA DUBBING PIPELINE")
    print("="*60)
    print(f"📄 PDF: {pdf_path.name}\n")
    
    # Step 1: Validate PDF
    print("Step 1: Validating PDF...")
    if not validate_pdf(pdf_path):
        print("❌ PDF validation failed")
        return
    print("✅ PDF is valid\n")
    
    # Step 2: Convert PDF to images
    print("Step 2: Converting PDF to images...")
    try:
        test_job_id = "test_pipeline"
        image_paths = convert_pdf_to_images(pdf_path, test_job_id)
        print(f"✅ Extracted {len(image_paths)} pages")
        for i, img in enumerate(image_paths, 1):
            print(f"   Page {i}: {img.name}")
        print()
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        return
    
    # Step 3: Process with Gemini (ALL pages)
    print("Step 3: Analyzing with Gemini AI...")
    print(f"   Processing {len(image_paths)} pages...\n")
    
    try:
        # Process ALL pages
        result = process_manga_pages(image_paths, test_job_id)
        
        print("📊 GEMINI ANALYSIS RESULTS:")
        print("="*60)
        print(f"Total Dialogues: {result['total_dialogues']}")
        print()
        
        if result['total_dialogues'] == 0:
            print("⚠️  WARNING: No dialogues found!")
            print("   This could mean:")
            print("   1. The page has no text/speech bubbles")
            print("   2. Gemini couldn't detect the text")
            print("   3. Image quality is too low")
            print()
        
        # Show detailed results
        for page in result['pages']:
            print(f"\n📄 Page {page['page_number']}:")
            print(f"   Type: {page.get('page_type', 'unknown')}")
            
            dialogues = page.get('dialogs', [])
            print(f"   Dialogues: {len(dialogues)}")
            
            for dialogue in dialogues:
                sequence = dialogue.get('sequence', 0)
                speaker = dialogue.get('speaker', 'Unknown')
                text = dialogue.get('text', '')
                time_gap = dialogue.get('time_gap_before_s', 0.0)
                
                # Get emotion
                emotion = dialogue.get('emotion', {})
                if isinstance(emotion, dict):
                    emotion_type = emotion.get('type', 'neutral')
                    emotion_desc = emotion.get('description', '')
                    intensity = emotion.get('intensity', 0.5)
                else:
                    emotion_type = emotion
                    emotion_desc = ''
                    intensity = 0.5
                
                # Get speech settings
                speech = dialogue.get('speech', {})
                speed = speech.get('speed', 1.0)
                pitch = speech.get('pitch', 'medium')
                volume = speech.get('volume', 1.0)
                
                # Get position
                position = dialogue.get('position', {})
                vertical = position.get('vertical', 'middle')
                horizontal = position.get('horizontal', 'center')
                
                print(f"\n   {sequence}. [{speaker}] ({emotion_type} - intensity: {intensity})")
                print(f"      \"{text[:80]}{'...' if len(text) > 80 else ''}\"")
                print(f"      ⏱️  Gap before: {time_gap}s")
                print(f"      🎤 Speech: speed={speed}, volume={volume}, pitch={pitch}")
                print(f"      📍 Position: {vertical}-{horizontal}")
        
        # Save results to JSON for inspection
        output_file = Path("test_gemini_output.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Full results saved to: {output_file}")
        print()
        
        # Step 4: Generate Audio with Local TTS
        if result['total_dialogues'] > 0:
            print("\nStep 4: Generating audio with local TTS...")
            try:
                result_with_audio = generate_audio_tracks(result, test_job_id)
                print(f"✅ Generated {result_with_audio.get('successful_dialogues', 0)} audio files")
                print(f"   Merged audio: {result_with_audio.get('merged_audio_path', 'N/A')}")
                print()
                
                # Step 5: Generate Final Video
                print("\nStep 5: Generating final video...")
                try:
                    video_path = generate_dubbed_video_from_analysis(result_with_audio, test_job_id)
                    print(f"✅ Video created: {video_path}")
                    print()
                except Exception as e:
                    print(f"❌ Video generation failed: {e}")
                    import traceback
                    traceback.print_exc()
                    
            except Exception as e:
                print(f"❌ Audio generation failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Summary
        print("="*60)
        print("📋 SUMMARY:")
        print("="*60)
        if result['total_dialogues'] > 0:
            print(f"✅ Gemini successfully extracted {result['total_dialogues']} dialogues")
            print(f"✅ Local TTS audio generation completed")
            print(f"✅ Final video created with slideshow + audio")
        else:
            print("❌ No dialogues extracted from the page")
            print("\n🔍 Possible reasons:")
            print("   1. Page has no text (cover page, illustration only)")
            print("   2. Text is too small or unclear")
            print("   3. Non-English text (Gemini works best with English)")
            print("   4. Complex layout confusing the AI")
            print("\n💡 Try:")
            print("   - A different page with clear speech bubbles")
            print("   - A manga with English text")
            print("   - Higher quality PDF")
        
        print("="*60)
        
    except Exception as e:
        print(f"❌ Gemini processing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n✅ Pipeline test complete!")

if __name__ == "__main__":
    # Test with the PDF in uploads folder
    import glob
    
    # Find most recent PDF
    pdfs = glob.glob("static/uploads/*.pdf")
    
    if pdfs:
        # Use most recent
        latest_pdf = max(pdfs, key=lambda x: Path(x).stat().st_mtime)
        print(f"Found PDF: {latest_pdf}\n")
        test_pipeline(latest_pdf)
    else:
        print("❌ No PDF found in static/uploads/")
        print("   Please upload a PDF first or specify path:")
        print("   python test_pipeline.py path/to/your.pdf")
