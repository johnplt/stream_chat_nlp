import pandas as pd
import argparse
import os

def merge_chat_messages(df: pd.DataFrame) -> pd.DataFrame:
    
    # 1. Ensure timestamp is actual datetime for correct sorting
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 2. Sort globally by chat room and then time
    # This ensures that even if rows are out of order in the CSV, 
    # the 'join' happens in the correct sequence.
    df = df.sort_values(['chat_identifier', 'timestamp'])

    # 3. Simple GroupBy and Join
    # We aggregate by chat_identifier and join messages with a space.
    cleaned_df = df.groupby('chat_identifier').agg({
        'chat_message': lambda x: ' '.join(x.astype(str)),
        'timestamp': ['min', 'max', 'count']
    }).reset_index()

    # 4. Flatten the multi-index columns created by agg
    cleaned_df.columns = [
        'chat_identifier', 
        'full_message', 
        'start_time', 
        'end_time', 
        'fragment_count'
    ]

    return cleaned_df

def process_chat_data(args):
    # Load data
    df = pd.read_csv(args.csv_path)
    
    cleaned_df = merge_chat_messages(df)

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    
    cleaned_df.to_csv(args.output_csv, index=False)
    print(f"Successfully merged {len(cleaned_df)} unique chatrooms.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process chat message.")
    parser.add_argument("--csv_path", type=str, default="data/raw_chats.csv")
    parser.add_argument("--output_csv", type=str, default="output/cleaned_messages.csv")

    args = parser.parse_args()
    process_chat_data(args)