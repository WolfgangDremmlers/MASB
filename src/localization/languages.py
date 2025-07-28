"""Extended language support and localization for MASB."""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from pathlib import Path


class ExtendedLanguage(Enum):
    """Extended language enumeration with more languages."""
    # Original supported languages
    EN = "en"  # English
    DE = "de"  # German  
    FR = "fr"  # French
    ZH = "zh"  # Chinese (Mandarin)
    AR = "ar"  # Arabic
    SW = "sw"  # Swahili
    
    # Additional European languages
    ES = "es"  # Spanish
    IT = "it"  # Italian
    PT = "pt"  # Portuguese
    RU = "ru"  # Russian
    NL = "nl"  # Dutch
    PL = "pl"  # Polish
    TR = "tr"  # Turkish
    SV = "sv"  # Swedish
    NO = "no"  # Norwegian
    DA = "da"  # Danish
    FI = "fi"  # Finnish
    EL = "el"  # Greek
    CS = "cs"  # Czech
    HU = "hu"  # Hungarian
    RO = "ro"  # Romanian
    BG = "bg"  # Bulgarian
    HR = "hr"  # Croatian
    SK = "sk"  # Slovak
    SL = "sl"  # Slovenian
    LV = "lv"  # Latvian
    LT = "lt"  # Lithuanian
    ET = "et"  # Estonian
    
    # Asian languages
    JA = "ja"  # Japanese
    KO = "ko"  # Korean
    TH = "th"  # Thai
    VI = "vi"  # Vietnamese
    ID = "id"  # Indonesian
    MS = "ms"  # Malay
    TL = "tl"  # Filipino/Tagalog
    HI = "hi"  # Hindi
    BN = "bn"  # Bengali
    UR = "ur"  # Urdu
    TA = "ta"  # Tamil
    TE = "te"  # Telugu
    ML = "ml"  # Malayalam
    KN = "kn"  # Kannada
    GU = "gu"  # Gujarati
    PA = "pa"  # Punjabi
    
    # Middle Eastern languages
    FA = "fa"  # Persian/Farsi
    HE = "he"  # Hebrew
    
    # African languages
    AM = "am"  # Amharic
    HA = "ha"  # Hausa
    YO = "yo"  # Yoruba
    IG = "ig"  # Igbo
    ZU = "zu"  # Zulu
    XH = "xh"  # Xhosa
    AF = "af"  # Afrikaans
    
    # American languages
    QU = "qu"  # Quechua
    GN = "gn"  # Guarani


@dataclass
class LanguageInfo:
    """Language information including metadata."""
    code: str
    name: str
    native_name: str
    family: str
    script: str
    rtl: bool = False  # Right-to-Left
    complexity_level: str = "medium"  # low, medium, high
    ai_support_level: str = "good"  # poor, fair, good, excellent


# Comprehensive language information database
EXTENDED_LANGUAGE_INFO: Dict[str, LanguageInfo] = {
    # Major world languages with excellent AI support
    "en": LanguageInfo("en", "English", "English", "Germanic", "Latin", complexity_level="low", ai_support_level="excellent"),
    "zh": LanguageInfo("zh", "Chinese", "中文", "Sino-Tibetan", "Chinese", complexity_level="high", ai_support_level="excellent"),
    "es": LanguageInfo("es", "Spanish", "Español", "Romance", "Latin", complexity_level="medium", ai_support_level="excellent"),
    "hi": LanguageInfo("hi", "Hindi", "हिन्दी", "Indo-European", "Devanagari", complexity_level="high", ai_support_level="good"),
    "ar": LanguageInfo("ar", "Arabic", "العربية", "Semitic", "Arabic", rtl=True, complexity_level="high", ai_support_level="good"),
    "bn": LanguageInfo("bn", "Bengali", "বাংলা", "Indo-European", "Bengali", complexity_level="high", ai_support_level="fair"),
    "pt": LanguageInfo("pt", "Portuguese", "Português", "Romance", "Latin", complexity_level="medium", ai_support_level="good"),
    "ru": LanguageInfo("ru", "Russian", "Русский", "Slavic", "Cyrillic", complexity_level="high", ai_support_level="good"),
    "ja": LanguageInfo("ja", "Japanese", "日本語", "Japonic", "Japanese", complexity_level="high", ai_support_level="excellent"),
    "fr": LanguageInfo("fr", "French", "Français", "Romance", "Latin", complexity_level="medium", ai_support_level="excellent"),
    "de": LanguageInfo("de", "German", "Deutsch", "Germanic", "Latin", complexity_level="high", ai_support_level="excellent"),
    "ko": LanguageInfo("ko", "Korean", "한국어", "Koreanic", "Hangul", complexity_level="high", ai_support_level="good"),
    
    # European languages
    "it": LanguageInfo("it", "Italian", "Italiano", "Romance", "Latin", complexity_level="medium", ai_support_level="good"),
    "nl": LanguageInfo("nl", "Dutch", "Nederlands", "Germanic", "Latin", complexity_level="medium", ai_support_level="good"),
    "pl": LanguageInfo("pl", "Polish", "Polski", "Slavic", "Latin", complexity_level="high", ai_support_level="fair"),
    "tr": LanguageInfo("tr", "Turkish", "Türkçe", "Turkic", "Latin", complexity_level="high", ai_support_level="fair"),
    "sv": LanguageInfo("sv", "Swedish", "Svenska", "Germanic", "Latin", complexity_level="medium", ai_support_level="fair"),
    "no": LanguageInfo("no", "Norwegian", "Norsk", "Germanic", "Latin", complexity_level="medium", ai_support_level="fair"),
    "da": LanguageInfo("da", "Danish", "Dansk", "Germanic", "Latin", complexity_level="medium", ai_support_level="fair"),
    "fi": LanguageInfo("fi", "Finnish", "Suomi", "Uralic", "Latin", complexity_level="high", ai_support_level="fair"),
    "el": LanguageInfo("el", "Greek", "Ελληνικά", "Hellenic", "Greek", complexity_level="high", ai_support_level="fair"),
    "cs": LanguageInfo("cs", "Czech", "Čeština", "Slavic", "Latin", complexity_level="high", ai_support_level="fair"),
    "hu": LanguageInfo("hu", "Hungarian", "Magyar", "Uralic", "Latin", complexity_level="high", ai_support_level="fair"),
    
    # Asian languages
    "th": LanguageInfo("th", "Thai", "ไทย", "Tai-Kadai", "Thai", complexity_level="high", ai_support_level="fair"),
    "vi": LanguageInfo("vi", "Vietnamese", "Tiếng Việt", "Austroasiatic", "Latin", complexity_level="high", ai_support_level="fair"),
    "id": LanguageInfo("id", "Indonesian", "Bahasa Indonesia", "Austronesian", "Latin", complexity_level="medium", ai_support_level="fair"),
    "ms": LanguageInfo("ms", "Malay", "Bahasa Melayu", "Austronesian", "Latin", complexity_level="medium", ai_support_level="fair"),
    "tl": LanguageInfo("tl", "Filipino", "Filipino", "Austronesian", "Latin", complexity_level="medium", ai_support_level="fair"),
    "ur": LanguageInfo("ur", "Urdu", "اردو", "Indo-European", "Arabic", rtl=True, complexity_level="high", ai_support_level="fair"),
    "fa": LanguageInfo("fa", "Persian", "فارسی", "Indo-European", "Arabic", rtl=True, complexity_level="high", ai_support_level="fair"),
    "he": LanguageInfo("he", "Hebrew", "עברית", "Semitic", "Hebrew", rtl=True, complexity_level="high", ai_support_level="fair"),
    
    # Tamil and other Indian languages
    "ta": LanguageInfo("ta", "Tamil", "தமிழ்", "Dravidian", "Tamil", complexity_level="high", ai_support_level="fair"),
    "te": LanguageInfo("te", "Telugu", "తెలుగు", "Dravidian", "Telugu", complexity_level="high", ai_support_level="fair"),
    "ml": LanguageInfo("ml", "Malayalam", "മലയാളം", "Dravidian", "Malayalam", complexity_level="high", ai_support_level="poor"),
    "kn": LanguageInfo("kn", "Kannada", "ಕನ್ನಡ", "Dravidian", "Kannada", complexity_level="high", ai_support_level="poor"),
    "gu": LanguageInfo("gu", "Gujarati", "ગુજરાતી", "Indo-European", "Gujarati", complexity_level="high", ai_support_level="fair"),
    "pa": LanguageInfo("pa", "Punjabi", "ਪੰਜਾਬੀ", "Indo-European", "Gurmukhi", complexity_level="high", ai_support_level="fair"),
    
    # African languages
    "sw": LanguageInfo("sw", "Swahili", "Kiswahili", "Niger-Congo", "Latin", complexity_level="medium", ai_support_level="fair"),
    "am": LanguageInfo("am", "Amharic", "አማርኛ", "Semitic", "Ethiopic", complexity_level="high", ai_support_level="poor"),
    "ha": LanguageInfo("ha", "Hausa", "Hausa", "Afroasiatic", "Latin", complexity_level="medium", ai_support_level="poor"),
    "yo": LanguageInfo("yo", "Yoruba", "Yorùbá", "Niger-Congo", "Latin", complexity_level="medium", ai_support_level="poor"),
    "ig": LanguageInfo("ig", "Igbo", "Igbo", "Niger-Congo", "Latin", complexity_level="medium", ai_support_level="poor"),
    "zu": LanguageInfo("zu", "Zulu", "isiZulu", "Niger-Congo", "Latin", complexity_level="medium", ai_support_level="poor"),
    "xh": LanguageInfo("xh", "Xhosa", "isiXhosa", "Niger-Congo", "Latin", complexity_level="medium", ai_support_level="poor"),
    "af": LanguageInfo("af", "Afrikaans", "Afrikaans", "Germanic", "Latin", complexity_level="medium", ai_support_level="fair"),
}


class LocalizationManager:
    """Manages localization and internationalization."""
    
    def __init__(self, base_path: Path = None):
        """Initialize localization manager.
        
        Args:
            base_path: Base path for localization files
        """
        self.base_path = base_path or Path(__file__).parent / "locales"
        self.translations: Dict[str, Dict[str, str]] = {}
        self.current_locale = "en"
        
    def load_translations(self, language_code: str) -> bool:
        """Load translations for a specific language.
        
        Args:
            language_code: Language code to load
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            locale_file = self.base_path / f"{language_code}.json"
            if locale_file.exists():
                with open(locale_file, 'r', encoding='utf-8') as f:
                    self.translations[language_code] = json.load(f)
                return True
            else:
                # Try to load from a fallback or create minimal translations
                self.translations[language_code] = self._create_minimal_translations(language_code)
                return False
        except Exception as e:
            print(f"Error loading translations for {language_code}: {e}")
            self.translations[language_code] = self._create_minimal_translations(language_code)
            return False
    
    def _create_minimal_translations(self, language_code: str) -> Dict[str, str]:
        """Create minimal translations for a language."""
        lang_info = EXTENDED_LANGUAGE_INFO.get(language_code)
        if not lang_info:
            return {}
        
        # Basic UI translations - would be expanded with proper translations
        minimal = {
            "app.title": "MASB - Multilingual Adversarial Safety Benchmark",
            "nav.home": "Home",
            "nav.evaluate": "Evaluate", 
            "nav.results": "Results",
            "nav.analysis": "Analysis",
            "nav.settings": "Settings",
            "button.start": "Start",
            "button.stop": "Stop", 
            "button.save": "Save",
            "button.cancel": "Cancel",
            "status.running": "Running",
            "status.completed": "Completed", 
            "status.failed": "Failed",
            "language.name": lang_info.native_name
        }
        
        return minimal
    
    def get_text(self, key: str, language: str = None, **kwargs) -> str:
        """Get localized text.
        
        Args:
            key: Translation key
            language: Language code (uses current if None)
            **kwargs: Format parameters
            
        Returns:
            Localized text
        """
        lang = language or self.current_locale
        
        if lang not in self.translations:
            self.load_translations(lang)
        
        # Try to get translation
        translation = self.translations.get(lang, {}).get(key)
        
        # Fallback to English
        if not translation and lang != "en":
            if "en" not in self.translations:
                self.load_translations("en")
            translation = self.translations.get("en", {}).get(key)
        
        # Final fallback to key itself
        if not translation:
            translation = key
        
        # Apply formatting
        try:
            return translation.format(**kwargs) if kwargs else translation
        except (KeyError, ValueError):
            return translation
    
    def set_locale(self, language_code: str):
        """Set current locale.
        
        Args:
            language_code: Language code to set as current
        """
        self.current_locale = language_code
        if language_code not in self.translations:
            self.load_translations(language_code)
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages with metadata.
        
        Returns:
            List of language information
        """
        return [
            {
                "code": code,
                "name": info.name,
                "native_name": info.native_name,
                "family": info.family,
                "script": info.script,
                "rtl": info.rtl,
                "complexity": info.complexity_level,
                "ai_support": info.ai_support_level
            }
            for code, info in EXTENDED_LANGUAGE_INFO.items()
        ]
    
    def get_language_info(self, language_code: str) -> Optional[LanguageInfo]:
        """Get information about a specific language.
        
        Args:
            language_code: Language code
            
        Returns:
            Language information or None if not found
        """
        return EXTENDED_LANGUAGE_INFO.get(language_code)
    
    def is_rtl_language(self, language_code: str) -> bool:
        """Check if language is right-to-left.
        
        Args:
            language_code: Language code
            
        Returns:
            True if RTL, False otherwise
        """
        info = self.get_language_info(language_code)
        return info.rtl if info else False
    
    def get_language_complexity(self, language_code: str) -> str:
        """Get language complexity level.
        
        Args:
            language_code: Language code
            
        Returns:
            Complexity level (low, medium, high)
        """
        info = self.get_language_info(language_code)
        return info.complexity_level if info else "medium"
    
    def create_locale_file(self, language_code: str, translations: Dict[str, str]):
        """Create a locale file for a language.
        
        Args:
            language_code: Language code
            translations: Dictionary of translations
        """
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        locale_file = self.base_path / f"{language_code}.json"
        with open(locale_file, 'w', encoding='utf-8') as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)
        
        # Load into memory
        self.translations[language_code] = translations


# Global localization manager instance
localization_manager = LocalizationManager()