import pytest
from app.prompt import build_prompt, LANG_INSTRUCTIONS

def test_build_prompt_english():
    prompt = build_prompt("Show sales", "Tables: sales(id)", language="en")
    assert "English" in prompt
    assert "Show sales" in prompt
    assert "Tables: sales(id)" in prompt

def test_build_prompt_hindi():
    prompt = build_prompt("बिक्री दिखाओ", "Tables: sales(id)", language="hi")
    assert "Hindi" in prompt
    assert "बिक्री दिखाओ" in prompt

def test_build_prompt_telugu():
    prompt = build_prompt("అమ్మకాలు", "Tables: sales(id)", language="te")
    assert "Telugu" in prompt

def test_build_prompt_unsupported_language():
    with pytest.raises(ValueError, match="Unsupported language"):
        build_prompt("Show sales", "Tables: sales(id)", language="es")
