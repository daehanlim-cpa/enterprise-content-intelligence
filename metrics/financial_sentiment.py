import json
import spacy
from transformers import pipeline
import pandas as pd
import os

# --- Configuration: Risk Taxonomy & Portfolio ---

# 1. Define your Risk Categories for the LLM classifier
RISK_CATEGORIES = [
    "MACRO_RISK (Economy, Inflation, Rates)",
    "FINANCE_RISK (Debt, Earnings, Cash Flow)",
    "PRODUCT_RISK (Supply Chain, Product Failure)",
    "REGULATORY_RISK (Lawsuits, Policy Changes)",
    "COMPANY_SPECIFIC_POSITIVE (Growth, New Product)" # Track positive news too
]

# 2. Your Personal Portfolio Holdings and Weights
MY_POSITIONS = {
    'AAPL': {'weight': 0.35, 'risk_tolerance': 'LOW'}, 
    'TESLA': {'weight': 0.15, 'risk_tolerance': 'MEDIUM'},
    'MSFT': {'weight': 0.20, 'risk_tolerance': 'LOW'},
    # Add more tickers/weights here as needed
}
PORTFOLIO_TICKERS = list(MY_POSITIONS.keys())

# --- Model Loading ---
try:
    nlp = spacy.load("en_core_web_sm") 
    sentiment_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert") 
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
except Exception as e:
    print(f"Error loading required models: {e}")
    print("Please ensure you ran 'pip install spacy transformers' and downloaded the spaCy model: 'python -m spacy download en_core_web_sm'")
    exit()

# --- Helper Functions ---

def get_last_video_id():
    """Reads the ID of the last processed video from the config file."""
    try:
        with open("last_processed_video.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: Config file 'last_processed_video.txt' not found.")
        print("Please run get_transcript.py first to create the necessary file.")
        return None

def load_transcript(transcript_json_file):
    """
    Loads raw transcript data and merges short chunks into full, contextual sentences
    for better NLP accuracy.
    """
    try:
        with open(transcript_json_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Transcript file not found at {transcript_json_file}. Check the path.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {transcript_json_file}.")
        return []

    # --- NEW MERGING LOGIC ---
    merged_sentences = []
    current_chunk = ""
    MAX_CHUNK_LENGTH = 1500 # Max characters before forcing a merge

    for item in raw_data:
        text = item['text']

        # Append the current text chunk
        current_chunk += (" " + text)

        # Check for sentence-ending punctuation OR check if the chunk is getting too long
        if text.endswith(('.', '?', '!')) or len(current_chunk) > MAX_CHUNK_LENGTH:
            # Clean up excessive whitespace before appending
            merged_sentences.append(current_chunk.strip())
            current_chunk = "" # Reset the buffer

    # Handle any remaining text left in the buffer after the loop
    if current_chunk:
        merged_sentences.append(current_chunk.strip())
        
    print(f"Transcript loaded. Original chunks: {len(raw_data)}, Merged sentences: {len(merged_sentences)}")
    return merged_sentences


def assess_risk(sentiment_result, asset_ticker):
    """Calculates a personal risk score based on sentiment and portfolio weight."""
    sentiment_label = sentiment_result[0]['label']
    sentiment_score = sentiment_result[0]['score']
    
    asset_weight = MY_POSITIONS.get(asset_ticker, {}).get('weight', 0)
    
    # Normalize sentiment score (-1.0 for highly negative, +1.0 for highly positive)
    risk_multiplier = 0 
    if sentiment_label == 'negative':
        risk_multiplier = -sentiment_score
    elif sentiment_label == 'positive':
        risk_multiplier = sentiment_score
        
    # Calculate the final Portfolio Risk Score (weighted by capital exposure)
    portfolio_impact_score = risk_multiplier * (asset_weight * 10)

    return portfolio_impact_score, risk_multiplier


# --- Main Analysis Function ---

def analyze_transcript(transcript_json_file):
    
    risk_data = []
    sentences = load_transcript(transcript_json_file)

    if not sentences:
        return pd.DataFrame() 

    # --- Start Loop: Iterate through each sentence ---
    for sentence in sentences:
        
        # 1. Initialize variables for each loop
        found_asset = None 
        doc = nlp(sentence)
        
        # 2. TICKER MATCHING LOGIC
        # Check for known portfolio tickers first
        for ticker in PORTFOLIO_TICKERS:
            if ticker in sentence.upper():
                found_asset = ticker
                break
        
        # If no ticker found, check for large Organization entities (e.g., 'Apple' for 'AAPL')
        if not found_asset:
            for ent in doc.ents:
                if ent.label_ == 'ORG' and ent.text.upper() in [name.upper() for name in PORTFOLIO_TICKERS]:
                    found_asset = ent.text
                    break
        
        # 3. Proceed with analysis ONLY if an asset was found
        if found_asset:
            
            # --- Task 1: FinBERT Sentiment ---
            sentiment_result = sentiment_pipeline(sentence)
            
            # --- Task 2: Risk Factor Classification (Zero-Shot) ---
            classification_result = classifier(sentence, RISK_CATEGORIES)
            top_category = classification_result['labels'][0]
            
            # --- Task 3: Portfolio Impact Scoring ---
            impact_score, risk_multiplier = assess_risk(sentiment_result, found_asset)

            risk_data.append({
                'Asset': found_asset,
                'Portfolio_Weight': MY_POSITIONS[found_asset]['weight'],
                'Sentence': sentence,
                'Sentiment_Label': sentiment_result[0]['label'],
                'Top_Risk_Category': top_category,
                'Portfolio_Impact_Score': f"{impact_score:.4f}",
            })
            
    # --- Final Reporting ---
    df = pd.DataFrame(risk_data)
    
    # FIX: Check if DataFrame is empty before attempting column access
    if df.empty:
        return df

    # Convert impact score to numeric for sorting
    df['Portfolio_Impact_Score'] = pd.to_numeric(df['Portfolio_Impact_Score'])
    
    # Sort by the most negative Impact Score first (ascending=True)
    df_sorted = df.sort_values(by='Portfolio_Impact_Score', ascending=True)
    
    return df_sorted


# --- Main Execution Block ---

if __name__ == "__main__":
    
    # 1. DYNAMICALLY get the latest video ID
    video_id = get_last_video_id()
    if not video_id:
        exit() # Stop if no video ID is found
    
    # 2. CONSTRUCT the filename dynamically
    transcript_file_name = f'{video_id}_transcript_data.json' 
    
    print(f"Starting analysis on transcript: {transcript_file_name}")
    
    final_risk_df = analyze_transcript(transcript_file_name)
    
    print("\n" + "="*50)
    print(" FINANCIAL RISK ANALYSIS RESULTS (Top Findings) ")
    print("="*50)

    if not final_risk_df.empty:
        # Print the top 5 most negative findings
        print(final_risk_df.head(5).to_markdown(index=False)) 
        
        # Save ALL results to a CSV file
        output_csv_name = 'financial_risk_output.csv'
        final_risk_df.to_csv(output_csv_name, index=False)
        
        print("\n" + "="*50)
        print(f" ✅ Full results saved to {output_csv_name}")
        print("="*50)
    else:
        print("No relevant portfolio assets were mentioned or the transcript could not be loaded.")