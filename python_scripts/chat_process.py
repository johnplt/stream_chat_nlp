import pandas as pd
import argparse

def process_chat_data(args):
    # Load data
    df = pd.read_csv(args.csv_path, sep = ',')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(['chat_identifier', 'timestamp'])

    # Calculate time difference between consecutive messages from the same user
    df['time_diff'] = df.groupby('chat_identifier')['timestamp'].diff().dt.total_seconds()
    
    # Identify a "new message block" if time_diff > threshold or it's a new user
    df['new_block'] = (df['time_diff'] > args.time_threshold_secs) | (df['time_diff'].isna())
    df['block_id'] = df.groupby('chat_identifier')['new_block'].cumsum()

    # Aggregate blocks
    cleaned_df = df.groupby(['chat_identifier', 'block_id']).agg({
        'timestamp': 'first',
        'chat_message': lambda x: ' '.join(x)
    }).reset_index().drop(columns=['block_id'])
    
    return cleaned_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process chat message.")

    parser.add_argument("--csv_path", type=str, default="data/raw_chats.csv", help="Chemin vers le fichier csv des données.")
    parser.add_argument("--time_threshold_secs", type=str, default=5, help="Chemin vers le fichier de test CSV.")

    args = parser.parse_args()
    result = process_chat_data(args)
    result.to_csv("data/cleaned_messages_from_python.csv", index=False)