#!/bin/bash
set -e

echo "--- 🚀 Starting Broker Chat Pipeline ---"

# 1. Install/Update Dependencies
pip install -q -r requirements.txt

# 2. Run dbt
dbt run --project-dir ./dbt_management --profiles-dir ./dbt_management

# 3. Run Python classification
# We pass the root path to the script so it can find the DuckDB file

python python_scripts/message_classification.py \
    --source db \
    --input_path output/cleaned_messages.db

echo "--- ✅ Done! ---"