-- This test will FAIL if it returns any rows.
-- We want to ensure every merged message actually contains text.

SELECT
    chat_id,
    message_start_time
FROM {{ ref('merge_messages') }}
WHERE full_message IS NULL OR full_message = ''