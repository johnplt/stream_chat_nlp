{{ config(materialized='table') }}

WITH base_data AS (
    SELECT 
        chat_id,
        message_content,
        -- Ensure timestamp is handled correctly for sorting
        CAST(message_at AS TIMESTAMP) as msg_timestamp
    FROM {{ ref('stg_chat_messages') }}
)

SELECT
    chat_id,
    -- Glue the fragments together with a space, ordered by time
    string_agg(message_content, ' ' ORDER BY msg_timestamp ASC) as full_message,
    MIN(msg_timestamp) as chat_start_time,
    MAX(msg_timestamp) as chat_end_time,
    COUNT(*) as fragment_count
FROM base_data
GROUP BY chat_id