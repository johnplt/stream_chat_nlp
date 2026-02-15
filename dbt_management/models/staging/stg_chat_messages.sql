{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('messages_data', 'raw_chats') }}
),

renamed AS (
    SELECT
        timestamp AS message_at,
        chat_identifier AS chat_id,
        TRIM(chat_message) AS message_content
    FROM source
)

SELECT * FROM renamed