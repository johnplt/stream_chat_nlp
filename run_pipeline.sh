#!/bin/bash
set -e

echo "--- 🚀 Starting Broker Chat Pipeline ---"

# 1. Install/Update Dependencies
pip install -q -r requirements.txt

# 2. Run dbt
dbt run --project-dir ./dbt_management --profiles-dir ./dbt_management

# 3. Run Python audit

python python_scripts/messages_audit.py \
    --source db \
    --input_path output/cleaned_messages.db

# 4. Run Python multilingual classification

python python_scripts/messages_classification_multilingue.py \
    --source db \
    --input_path output/cleaned_messages.db

echo "--- ✅ Done! ---"