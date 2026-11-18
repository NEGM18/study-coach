from ml_core.text_normalize import normalize_for_eval, normalize_for_training


def test_training_removes_arabic_diacritics() -> None:
    assert normalize_for_training("مُدَرِّسٌ") == "مدرس"


def test_training_removes_tatweel() -> None:
    assert normalize_for_training("كـــتاب") == "كتاب"


def test_training_unifies_alef_forms() -> None:
    assert normalize_for_training("أ إ آ ا\u0654 ا\u0655 ا\u0653 ا") == "ا ا ا ا ا ا ا"


def test_training_converts_arabic_indic_digits() -> None:
    assert normalize_for_training("٠١٢٣٤٥٦٧٨٩ ۰۱۲۳۴۵۶۷۸۹ 12") == "0123456789 0123456789 12"


def test_training_lowercases_latin_letters() -> None:
    assert normalize_for_training("CaFÉ API Ω") == "café api Ω"


def test_training_removes_non_speech_tags() -> None:
    assert normalize_for_training("قبل[MUSIC]بعد [background noise] [API]") == "قبل بعد [api]"


def test_training_collapses_whitespace() -> None:
    assert normalize_for_training("\t  هنا\n\n كلام\u00a0كمان  ") == "هنا كلام كمان"


def test_eval_maps_alef_maksura_to_yaa() -> None:
    assert normalize_for_eval("على") == "علي"


def test_eval_maps_taa_marbuta_to_haa() -> None:
    assert normalize_for_eval("القاعة") == "القاعه"


def test_eval_removes_arabic_and_english_punctuation() -> None:
    assert normalize_for_eval("أول،تاني؛تالت؟ (A/B)! 2+2=4") == "اول تاني تالت a b 2+2=4"


def test_training_and_eval_handle_mixed_arabic_and_english() -> None:
    transcript = "  إِحنا فِي القَاعَة؛ عَلَى API ٣ [music]، وده الـQuiz!  "

    assert normalize_for_training(transcript) == "احنا في القاعة؛ على api 3 ، وده الquiz!"
    assert normalize_for_eval(transcript) == "احنا في القاعه علي api 3 وده الquiz"


def test_both_modes_return_empty_text_without_spoken_content() -> None:
    assert normalize_for_training(" \t[music]\n ") == ""
    assert normalize_for_eval(" \t[music]،!\n ") == ""


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
