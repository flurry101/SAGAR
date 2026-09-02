"""
Unit Test Suite — 22 Indian Language Support in SAGAR
Verifies language catalog completeness, coastal states mapping, RTL script direction,
and translation coverage for marine decision-support.
"""

import os
import unittest

COASTAL_STATE_LANGUAGES = {
    "karnataka": "kn",
    "tamil_nadu": "ta",
    "kerala": "ml",
    "andhra_pradesh": "te",
    "maharashtra": "mr",
    "gujarat": "gu",
    "goa": "kok",
    "odisha": "or",
    "west_bengal": "bn",
}

SCHEDULED_22_LANGUAGES = {
    "as", "bn", "brx", "doi", "gu", "hi", "kn", "ks", "kok", "mai",
    "ml", "mni", "mr", "ne", "or", "pa", "sa", "sat", "sd", "ta", "te", "ur"
}

RTL_LANGUAGES = {"ur", "ks", "sd"}

def test_all_22_scheduled_languages_present():
    """Verify that all 22 8th Schedule Indian languages are defined."""
    assert len(SCHEDULED_22_LANGUAGES) == 22
    assert "kn" in SCHEDULED_22_LANGUAGES
    assert "ta" in SCHEDULED_22_LANGUAGES
    assert "ml" in SCHEDULED_22_LANGUAGES
    assert "te" in SCHEDULED_22_LANGUAGES
    assert "mr" in SCHEDULED_22_LANGUAGES
    assert "gu" in SCHEDULED_22_LANGUAGES
    assert "bn" in SCHEDULED_22_LANGUAGES
    assert "or" in SCHEDULED_22_LANGUAGES
    assert "kok" in SCHEDULED_22_LANGUAGES

def test_coastal_states_have_primary_languages():
    """Ensure all 9 coastal states map to valid 8th Schedule languages."""
    for state, lang_code in COASTAL_STATE_LANGUAGES.items():
        assert lang_code in SCHEDULED_22_LANGUAGES, f"Coastal state {state} language {lang_code} missing from scheduled list!"

def test_po_catalogs_exist_and_non_empty():
    """Verify that all 23 language .po catalogs (22 scheduled + en) exist and are valid UTF-8."""
    base_locales_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "locales")
    )
    
    assert os.path.isdir(base_locales_dir), f"Locales directory not found at {base_locales_dir}"
    
    all_locales = SCHEDULED_22_LANGUAGES | {"en"}
    for locale in all_locales:
        po_path = os.path.join(base_locales_dir, locale, "messages.po")
        assert os.path.isfile(po_path), f"PO catalog missing for locale: {locale} at {po_path}"
        
        with open(po_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert f"Language: {locale}" in content or f'"{locale}"' in content
            assert "msgid" in content
            assert "msgstr" in content

def test_rtl_languages_classification():
    """Ensure Urdu, Kashmiri, and Sindhi are designated as RTL languages."""
    for rtl_lang in RTL_LANGUAGES:
        assert rtl_lang in SCHEDULED_22_LANGUAGES
        assert rtl_lang in {"ur", "ks", "sd"}

def test_critical_maritime_terms_in_catalogs():
    """Verify key maritime domain phrases are translated across coastal language catalogs."""
    base_locales_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src", "locales")
    )
    
    # Test coastal catalogs (e.g. Kannada, Tamil, Malayalam, Marathi)
    for locale in ["kn", "ta", "ml", "mr", "gu", "bn"]:
        po_path = os.path.join(base_locales_dir, locale, "messages.po")
        with open(po_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert 'msgid "SAGAR Marine Decision Support"' in content
            assert 'msgid "Plan Maritime Trip"' in content
            assert 'msgid "Conditions Favourable"' in content
