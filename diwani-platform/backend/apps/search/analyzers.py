"""
===================================
منصة ديواني - Arabic Text Analyzers
محللات النصوص العربية المتقدمة
===================================

يدعم:
- تحليل النص العربي
- إزالة التشكيل
- معالجة الألف واللام
- البحث بالجذور (Stemming)
- المرادفات العربية
- Autocomplete
"""

# ===================================
# إعدادات الفهرس الأساسية
# ===================================
ARABIC_INDEX_SETTINGS = {
    "index": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "refresh_interval": "1s",
        "max_result_window": 50000,
        "max_ngram_diff": 20,
    },
    "analysis": {
        # ===================================
        # Character Filters
        # ===================================
        "char_filter": {
            # تنظيف النص العربي
            "arabic_normalize": {
                "type": "mapping",
                "mappings": [
                    "ٱ => ا",  # ألف وصل
                    "أ => ا",  # همزة فوق الألف
                    "إ => ا",  # همزة تحت الألف
                    "آ => ا",  # ألف مد
                    "ى => ي",  # ألف مقصورة
                    "ة => ه",  # تاء مربوطة (اختياري)
                    "ؤ => و",  # همزة على واو
                    "ئ => ي",  # همزة على ياء
                ]
            },
            # إزالة التشكيل
            "remove_diacritics": {
                "type": "pattern_replace",
                "pattern": "[\\u064B-\\u065F\\u0670]",  # الحركات العربية
                "replacement": ""
            },
            # تحويل الأرقام العربية للإنجليزية
            "arabic_to_english_numbers": {
                "type": "mapping",
                "mappings": [
                    "٠ => 0", "١ => 1", "٢ => 2", "٣ => 3", "٤ => 4",
                    "٥ => 5", "٦ => 6", "٧ => 7", "٨ => 8", "٩ => 9"
                ]
            },
            # تنظيف الرموز الخاصة
            "clean_special_chars": {
                "type": "pattern_replace",
                "pattern": "[_\\-/\\\\]",
                "replacement": " "
            }
        },

        # ===================================
        # Tokenizers
        # ===================================
        "tokenizer": {
            # للـ Autocomplete
            "autocomplete_tokenizer": {
                "type": "edge_ngram",
                "min_gram": 2,
                "max_gram": 20,
                "token_chars": ["letter", "digit"]
            },
            # للبحث بالأجزاء
            "ngram_tokenizer": {
                "type": "ngram",
                "min_gram": 3,
                "max_gram": 15,
                "token_chars": ["letter", "digit"]
            }
        },

        # ===================================
        # Filters
        # ===================================
        "filter": {
            # Arabic Stemmer
            "arabic_stemmer": {
                "type": "stemmer",
                "language": "arabic"
            },
            # Arabic Stop Words
            "arabic_stop": {
                "type": "stop",
                "stopwords": [
                    "في", "من", "إلى", "على", "عن", "مع", "هذا", "هذه",
                    "ذلك", "تلك", "هو", "هي", "هم", "هن", "نحن", "أنا",
                    "أنت", "أنتم", "التي", "الذي", "الذين", "اللذين",
                    "اللتين", "اللواتي", "ما", "ماذا", "لماذا", "كيف",
                    "أين", "متى", "أي", "كل", "بعض", "غير", "سوى",
                    "حتى", "لكن", "بل", "أو", "و", "ثم", "أم", "إن",
                    "أن", "لأن", "كان", "كانت", "كانوا", "يكون", "تكون",
                    "قد", "لقد", "سوف", "لن", "لم", "ليس", "ليست"
                ]
            },
            # تصغير الحروف
            "lowercase_filter": {
                "type": "lowercase"
            },
            # إزالة الكلمات القصيرة جداً
            "min_length_filter": {
                "type": "length",
                "min": 2
            },
            # Edge Ngram للـ Autocomplete
            "autocomplete_filter": {
                "type": "edge_ngram",
                "min_gram": 2,
                "max_gram": 20
            },
            # المرادفات العربية لمواد البناء
            "building_materials_synonyms": {
                "type": "synonym",
                "synonyms": [
                    # الحديد
                    "حديد, صلب, معدن, steel",
                    "حديد تسليح, حديد بناء, rebar",
                    # الخرسانة
                    "خرسانة, اسمنت, cement, concrete",
                    "خرسانة جاهزة, خرسانة مسلحة",
                    # الطوب
                    "طوب, بلوك, block, brick",
                    "طوب أحمر, طوب اسمنتي, طوب حراري",
                    # الرمل
                    "رمل, sand",
                    "رمل ناعم, رمل خشن",
                    # العزل
                    "عزل, عازل, insulation",
                    "عزل حراري, عزل مائي, عزل صوتي",
                    # الدهانات
                    "دهان, طلاء, بوية, paint",
                    # السيراميك
                    "سيراميك, بلاط, tiles, ceramic",
                    "بورسلين, رخام, جرانيت",
                    # السباكة
                    "سباكة, مواسير, أنابيب, plumbing, pipes",
                    # الكهرباء
                    "كهرباء, أسلاك, كيابل, electrical, wires",
                    # الأبواب والنوافذ
                    "أبواب, doors",
                    "نوافذ, شبابيك, windows",
                    # أدوات
                    "أدوات, عدة, tools",
                ]
            }
            # ملاحظة: تم إزالة arabic_phonetic لأنه يتطلب plugin غير مثبت
            # يمكن إضافته لاحقاً بتثبيت analysis-phonetic plugin
        },

        # ===================================
        # Analyzers
        # ===================================
        "analyzer": {
            # المحلل العربي الرئيسي
            "arabic_analyzer": {
                "type": "custom",
                "char_filter": [
                    "arabic_normalize",
                    "remove_diacritics",
                    "arabic_to_english_numbers",
                    "clean_special_chars"
                ],
                "tokenizer": "standard",
                "filter": [
                    "lowercase_filter",
                    "arabic_stop",
                    "arabic_stemmer",
                    "min_length_filter"
                ]
            },

            # محلل البحث (بدون stemming للدقة)
            "arabic_search_analyzer": {
                "type": "custom",
                "char_filter": [
                    "arabic_normalize",
                    "remove_diacritics",
                    "arabic_to_english_numbers"
                ],
                "tokenizer": "standard",
                "filter": [
                    "lowercase_filter",
                    "arabic_stop"
                ]
            },

            # محلل الـ Autocomplete
            "autocomplete_analyzer": {
                "type": "custom",
                "char_filter": [
                    "arabic_normalize",
                    "remove_diacritics"
                ],
                "tokenizer": "autocomplete_tokenizer",
                "filter": [
                    "lowercase_filter"
                ]
            },

            # محلل البحث في الـ Autocomplete
            "autocomplete_search_analyzer": {
                "type": "custom",
                "char_filter": [
                    "arabic_normalize",
                    "remove_diacritics"
                ],
                "tokenizer": "standard",
                "filter": [
                    "lowercase_filter"
                ]
            },

            # محلل مع المرادفات
            "arabic_synonym_analyzer": {
                "type": "custom",
                "char_filter": [
                    "arabic_normalize",
                    "remove_diacritics"
                ],
                "tokenizer": "standard",
                "filter": [
                    "lowercase_filter",
                    "building_materials_synonyms",
                    "arabic_stop",
                    "arabic_stemmer"
                ]
            },

            # محلل للأسماء والعناوين
            "arabic_keyword_analyzer": {
                "type": "custom",
                "char_filter": [
                    "arabic_normalize",
                    "remove_diacritics"
                ],
                "tokenizer": "keyword",
                "filter": [
                    "lowercase_filter",
                    "trim"
                ]
            },

            # محلل للـ SKU وأرقام المنتجات
            "sku_analyzer": {
                "type": "custom",
                "char_filter": [
                    "clean_special_chars"
                ],
                "tokenizer": "standard",
                "filter": [
                    "lowercase_filter"
                ]
            },

            # محلل مدمج (عربي + إنجليزي)
            "multilingual_analyzer": {
                "type": "custom",
                "char_filter": [
                    "arabic_normalize",
                    "remove_diacritics",
                    "arabic_to_english_numbers"
                ],
                "tokenizer": "standard",
                "filter": [
                    "lowercase_filter",
                    "min_length_filter"
                ]
            }
        },

        # ===================================
        # Normalizers (للـ Keyword fields)
        # ===================================
        "normalizer": {
            "arabic_normalizer": {
                "type": "custom",
                "char_filter": [
                    "arabic_normalize",
                    "remove_diacritics"
                ],
                "filter": [
                    "lowercase"
                ]
            },
            "lowercase_normalizer": {
                "type": "custom",
                "filter": ["lowercase"]
            }
        }
    }
}


# ===================================
# Helper Functions
# ===================================
def get_text_field_mapping(
    analyzer: str = "arabic_analyzer",
    search_analyzer: str = None,
    boost: float = 1.0,
    include_keyword: bool = True,
    include_autocomplete: bool = False
) -> dict:
    """
    إنشاء mapping لحقل نصي مع الإعدادات المطلوبة
    """
    mapping = {
        "type": "text",
        "analyzer": analyzer,
        "boost": boost,
    }

    if search_analyzer:
        mapping["search_analyzer"] = search_analyzer

    fields = {}

    if include_keyword:
        fields["keyword"] = {
            "type": "keyword",
            "normalizer": "arabic_normalizer",
            "ignore_above": 256
        }

    if include_autocomplete:
        fields["autocomplete"] = {
            "type": "text",
            "analyzer": "autocomplete_analyzer",
            "search_analyzer": "autocomplete_search_analyzer"
        }

    # إضافة حقل للبحث بالمرادفات
    fields["synonyms"] = {
        "type": "text",
        "analyzer": "arabic_synonym_analyzer"
    }

    if fields:
        mapping["fields"] = fields

    return mapping


def get_geo_point_mapping() -> dict:
    """Mapping للموقع الجغرافي"""
    return {
        "type": "geo_point"
    }


def get_completion_field_mapping() -> dict:
    """Mapping للـ Suggest/Autocomplete"""
    return {
        "type": "completion",
        "analyzer": "autocomplete_analyzer",
        "search_analyzer": "autocomplete_search_analyzer",
        "preserve_separators": True,
        "preserve_position_increments": True,
        "max_input_length": 50,
        "contexts": [
            {
                "name": "category",
                "type": "category"
            },
            {
                "name": "location",
                "type": "geo",
                "precision": "100km"
            }
        ]
    }
