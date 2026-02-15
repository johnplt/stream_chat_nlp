WITH base AS (
    SELECT 
        message_at,
        chat_id,
        message_content,
        -- Get the timestamp of the previous message from the same user
        LAG(message_at) OVER (PARTITION BY chat_id ORDER BY message_at) AS prev_timestamp
    FROM {{ ref('stg_chat_messages') }}
),

calc_gap AS (
    SELECT 
        *,
        -- Define a gap (e.g., 5 seconds). If diff > 5s, it's a new message block.
        CASE 
            WHEN prev_timestamp IS NULL THEN 1
            WHEN DATEDIFF('second', prev_timestamp, message_at) > 5 THEN 1 
            ELSE 0 
        END AS is_new_message
    FROM base
),

message_groups AS (
    SELECT 
        *,
        -- Running sum creates a unique ID for each message "block"
        SUM(is_new_message) OVER (PARTITION BY chat_id ORDER BY message_at) AS message_group_id
    FROM calc_gap
)

SELECT
    chat_id,
    MIN(message_at) AS message_start_time,
    -- Aggregate the strings (Syntax varies by DB: LISTAGG for Snowflake/Redshift, STRING_AGG for BigQuery/Postgres)
    STRING_AGG(message_content, ' ' ORDER BY message_at) AS full_message
FROM message_groups
GROUP BY chat_id, message_group_id