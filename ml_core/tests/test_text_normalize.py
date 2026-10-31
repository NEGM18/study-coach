"""Unit tests for shared Arabic text normalization (Issue #12)."""

from ml_core.text_normalize import normalize_for_eval, normalize_for_training


def test_normalize_training_removes_diacritics_and_tatweel() -> None:
    raw = "مُحَمَّدٌ كَــــاتِبٌ"
    expected = "محمد كاتب"
    assert normalize_for_training(raw) == expected


def test_normalize_training_unifies_alef_forms() -> None:
    raw = "أحمد إبراهيم آمنة ٱستماع"
    expected = "احمد ابراهيم امنة استماع"
    assert normalize_for_training(raw) == expected


def test_normalize_training_converts_arabic_indic_digits() -> None:
    raw = "محاضرة رقم ١٢ في قاعة ٣٠٥"
    expected = "محاضرة رقم 12 في قاعة 305"
    assert normalize_for_training(raw) == expected


def test_normalize_training_lowercases_english_and_removes_tags() -> None:
    raw = "Data STRUCTURES [music] lecture <applause>"
    expected = "data structures lecture"
    assert normalize_for_training(raw) == expected


def test_normalize_training_collapses_whitespace() -> None:
    raw = "  خوارزميات    الترتيب   و   البحث  \n\t"
    expected = "خوارزميات الترتيب و البحث"
    assert normalize_for_training(raw) == expected


def test_normalize_eval_maps_alif_maqsura_and_ta_marbuta() -> None:
    raw = "مدرسة علي الكبرى"
    expected = "مدرسه علي الكبري"
    assert normalize_for_eval(raw) == expected


def test_normalize_eval_removes_punctuation() -> None:
    raw = "خوارزمية A*، هل هي سريعة؟ نعم!"
    expected = "خوارزميه a هل هي سريعه نعم"
    assert normalize_for_eval(raw) == expected

