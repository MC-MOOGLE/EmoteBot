from src.emote_processor.get_emote import get_emote

def test_get_emote_no_file():
    assert get_emote() is None