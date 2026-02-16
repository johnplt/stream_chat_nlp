import pandas as pd
from pandas.testing import assert_frame_equal
from python_scripts.chat_process import merge_chat_messages

def test_merge_chat_messages_logic():
    # 1. ARRANGE: Create dummy data with messages out of order
    input_data = pd.DataFrame({
        'chat_identifier': ['room_A', 'room_A', 'room_B'],
        'chat_message': ['World', 'Hello', 'Single msg'],
        'timestamp': ['2026-01-01 10:00:05', '2026-01-01 10:00:00', '2026-01-01 11:00:00']
    })

    # 2. ACT: Run your merging function
    result = merge_chat_messages(input_data)

    # 3. ASSERT: Define what the perfect output should look like
    expected_data = pd.DataFrame({
        'chat_identifier': ['room_A', 'room_B'],
        'full_message': ['Hello World', 'Single msg'], # room_A is ordered correctly
        'start_time': pd.to_datetime(['2026-01-01 10:00:00', '2026-01-01 11:00:00']),
        'end_time': pd.to_datetime(['2026-01-01 10:00:05', '2026-01-01 11:00:00']),
        'fragment_count': [2, 1]
    })

    assert_frame_equal(result, expected_data)

def test_merge_handles_empty_values():
    # Test how it handles a row with a missing message
    input_data = pd.DataFrame({
        'chat_identifier': ['room_C', 'room_C'],
        'chat_message': ['Part 1', None],
        'timestamp': ['2026-01-01 10:00:00', '2026-01-01 10:00:01']
    })
    
    result = merge_chat_messages(input_data)
    # Ensure it doesn't crash and converts None to string
    assert "Part 1 None" in result.iloc[0]['full_message']