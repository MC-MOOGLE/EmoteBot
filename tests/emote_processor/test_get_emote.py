import pytest
from src.emote_processor.get_emote import get_emote

def test_get_emote_no_file():
    with pytest.raises(ValueError):
        get_emote("test_images/sadd_1.jpg")

def test_get_emote():
    result = get_emote("test_images/sad_2.jpg")

    print(result)

    assert result == "angry"