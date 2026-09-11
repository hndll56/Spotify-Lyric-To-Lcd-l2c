from main import get_current_lyric, normalize, parse_lrc


def test_normalize():
    assert normalize("The Weeknd - Blinding Lights!") == "theweekndblindinglights"


def test_parse_lrc_sorts_timestamps():
    lyrics = parse_lrc("[00:02.50]World\n[00:01.00]Hello")
    assert lyrics == [(1.0, "Hello"), (2.5, "World")]


def test_get_current_lyric():
    lyrics = [(1.0, "Hello"), (2.5, "World")]
    assert get_current_lyric(lyrics, 0.5) == ""
    assert get_current_lyric(lyrics, 1.0) == "Hello"
    assert get_current_lyric(lyrics, 3.0) == "World"
