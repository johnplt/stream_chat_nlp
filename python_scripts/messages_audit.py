import time
import argparse
import pandas as pd
import duckdb
import fasttext
import os
import urllib.request
from deep_translator import GoogleTranslator

def process_single_message(text, model_path, conf_threshold):
    """Core logic to handle detection, routing, and timing."""
    # Auto-download model if missing
    if not os.path.exists(model_path):
        url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
        urllib.request.urlretrieve(url, model_path)
    
    lang_model = fasttext.load_model(model_path)

    start_all = time.perf_counter()
    
    # --- Step 1: Language Classification ---
    t1_start = time.perf_counter()
    clean_text = str(text).replace("\n", " ")
    pred_label, pred_conf = lang_model.predict(clean_text, k=1)
    
    lang = pred_label[0].replace("__label__", "")
    conf = pred_conf[0]
    t1_ms = (time.perf_counter() - t1_start) * 1000
    
    # --- Step 2: Routing & Translation ---
    t2_start = time.perf_counter()
    translation_result = ""
    status = ""
    
    if conf < conf_threshold:
        status = "revision manually"
        translation_result = "N/A"
    elif lang == 'en':
        status = "english language"
        translation_result = text
    else:
        try:
            # External call (Only for high-confidence non-English)
            translation_result = GoogleTranslator(source='auto', target='en').translate(text)
            status = f"language: {lang}"
        except Exception:
            status = "revision manually (error)"
            translation_result = "N/A"
            
    t2_ms = (time.perf_counter() - t2_start) * 1000
    total_ms = (time.perf_counter() - start_all) * 1000

    # Return a Series so it expands into multiple columns in the DataFrame
    return pd.Series({
        "step1_lang": lang,
        "step1_conf": round(conf, 3),
        "step1_ms": round(t1_ms, 2),
        "step2_status": status,
        "translated_text": translation_result,
        "step2_ms": round(t2_ms, 2),
        "total_ms": round(total_ms, 2)
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
    # result_type='expand' creates the columns automatically
    print("Processing messages and profiling performance...")
    metrics_df = df["full_message"].apply(process_single_message, args=(args.model_path, args.conf_threshold))
    
    # Concatenate the original data with the new metrics
    final_df = pd.concat([df, metrics_df], axis=1)
    
    # Save to CSV
    final_df.to_csv(args.output_path, index=False)
    print(f"Success! Processed data saved to {args.output_path}")
    
    # Quick Summary
    avg_time = final_df['total_ms'].mean()
    print(f"Average processing time per message: {avg_time:.2f}ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit chat message.")

    parser.add_argument("--model_path", type=str, default="lid.176.bin", help="Fast text model path")
    parser.add_argument("--conf_threshold", type=str, default=0.7, help="Confidence hreshold for fasttext consecutive messages")
    parser.add_argument("--source", choices=["csv", "db"], required=True, help="Read from 'csv' or DuckDB 'db'")
    parser.add_argument("--input_path", type=str, help="Path to CSV file (if source=csv)")
    parser.add_argument("--output_path", type=str, default="output/audit_messages.csv", help="Output csv file path")

    args = parser.parse_args()
    process_dataframe(args)