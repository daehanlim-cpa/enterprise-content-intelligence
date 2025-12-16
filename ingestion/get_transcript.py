from youtube_transcript_api import YouTubeTranscriptApi
import json

# --- Helper Function to Pass ID to Analysis Script ---
def save_last_video_id(video_id):
    """Saves the ID of the last processed video to a config file for the analyzer."""
    try:
        # Save the ID to the file that financial_sentiment.py reads
        with open("last_processed_video.txt", "w") as f:
            f.write(video_id)
        print(f"\nSaved last processed video ID to last_processed_video.txt: {video_id}")
    except Exception as e:
        print(f"Warning: Could not save last video ID. {e}")
# ---------------------------------------------------


# --- Replace this with a real video ID from one of your favorite channels ---
video_id = '4iHCHsiW2vs' # Example placeholder ID
# --------------------------------------------------------------------------

try:
    # 1. Initialize the YouTubeTranscriptApi object (the recommended new way)
    ytt_api = YouTubeTranscriptApi() 
    
    # 2. Fetch the transcript using the .fetch() method
    transcript_list = ytt_api.fetch(
        video_id, 
        languages=['en', 'en-US'], # Prioritize English, then American English
        preserve_formatting=True
    )
    
    # NOTE: .fetch() returns a 'FetchedTranscript' object. Call .to_raw_data()
    raw_transcript_data = transcript_list.to_raw_data()
    
    # 3. Join the text parts into a single string for easier NLP processing
    full_transcript_text = " ".join([item['text'] for item in raw_transcript_data])

    print("--- Transcript Successfully Fetched ---")
    print(f"Video ID: {video_id}")
    # Adjusting print length to a more manageable 500 characters for terminal
    print(f"First 10000 characters of text:\n{full_transcript_text[:10000]}...")
    
    # 4. Save the full structured data to a JSON file
    transcript_file_name = f'{video_id}_transcript_data.json'
    with open(transcript_file_name, 'w', encoding='utf-8') as f:
        json.dump(raw_transcript_data, f, ensure_ascii=False, indent=4)
        
    print(f"\nSuccessfully saved structured transcript data to {transcript_file_name}")
    
    # 5. *** KEY NEW STEP: Save the video ID for the next script ***
    save_last_video_id(video_id)

except Exception as e:
    print(f"ERROR: Could not fetch transcript for ID: {video_id}")
    print(f"Reason: {e}")