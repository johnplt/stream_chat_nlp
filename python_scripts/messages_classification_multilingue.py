import time
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import argparse
import duckdb

# --- Configuration ---
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
model = SentenceTransformer(MODEL_NAME)

#  business categories
CATEGORIES = [
    "Trade Execution (Buy, Sell, Orders)",
    "Account Funding (Deposit, Withdrawal, Wire Transfer)",
    "Technical Support (Login, Password, App Error)",
    "Market Analysis (News, Prices, Trends)",
    "Compliance & Legal (KYC, Documents, Tax)"
]

# Pre-calculate category embeddings for speed
CATEGORY_EMBEDDINGS = model.encode(CATEGORIES, convert_to_tensor=True)

def classify_messages(text):
    """
    Zero-shot classification using semantic similarity.
    Calculates the 'distance' between the message and our categories.
    """
    start_time = time.perf_counter()
    
    # 1. Clean and Encode the message
    # No translation needed - the model handles multiple languages natively
    message_embedding = model.encode(str(text), convert_to_tensor=True)
    
    # 2. Compute Cosine Similarity against all categories
    # util.cos_sim returns a matrix of scores
    cosine_scores = util.cos_sim(message_embedding, CATEGORY_EMBEDDINGS)[0]
    
    # 3. Find the best match
    best_score_idx = cosine_scores.argmax().item()
    best_category = CATEGORIES[best_score_idx]
    best_score = round(float(cosine_scores[best_score_idx]), 3)
    
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    return pd.Series({
        "message_category": best_category,
        "classification_confidence": best_score,
        "classification_ms": duration_ms
    })

def process_dataframe(args):
    """Reads CSV, processes messages, and saves result."""
    # Load Data
    if args.source == "csv":
        print(f"Loading CSV from {args.input_path}...")
        df = pd.read_csv(args.input_path)
    else:
        print(f"Connecting to DuckDB at {args.input_path}...")
        con = duckdb.connect(args.input_path)
        df = con.execute("SELECT * FROM cleaned_messages.cleaned_messages").df()
        con.close()
    
    # Apply the function row-by-row
    print("Classify messages and profiling performance...")
    class_df = df["full_message"].apply(classify_messages)
    
    # Concatenate the original data with class
    final_df = pd.concat([df, class_df], axis=1)
    
    # Save to CSV
    final_df.to_csv(args.output_path, index=False)
    print(f"Success! Processed data saved to {args.output_path}")
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify chat message.")

    parser.add_argument("--source", choices=["csv", "db"], required=True, help="Read from 'csv' or DuckDB 'db'")
    parser.add_argument("--input_path", type=str, help="Path to CSV file (if source=csv)")
    parser.add_argument("--output_path", type=str, default="output/classified_messages.csv", help="Output csv file path")

    args = parser.parse_args()
    process_dataframe(args)