"""English and Arabic UI strings."""

from typing import Literal

Lang = Literal["EN", "AR"]

LANGUAGES: tuple[Lang, ...] = ("AR", "EN")
LANGUAGE_NAMES: dict[Lang, str] = {"AR": "العربية", "EN": "English"}
LANGUAGE_LABEL = "Language / اللغة"

_ABOUT_EN = """
This tool provides **comprehensive analysis** of Arabic and English conversations with multiple speakers:

### **Conversation Analysis**
- Overall sentiment and emotional tone
- Main topics discussed
- Conversation summary and key moments
- Quality and coherence assessment

### **Speaker Analysis**
- Individual speaker identification
- Each speaker's sentiment and emotional state
- Speaking style and role in conversation
- Speaking time and turn statistics

### **Prosody & Acoustic Features**
- Pitch, energy, and speaking rate
- Voice quality and characteristics
- Quantitative acoustic measurements

### **Interaction Dynamics**
- Turn-taking patterns (who speaks when)
- Conversational balance and dominance
- Rapport and cooperation levels
- Interruptions and overlaps

**Supported formats:** WAV, MP3, M4A, FLAC, OGG

**Maximum duration:** ~40 minutes recommended
"""

_ABOUT_AR = """
توفر هذه الأداة **تحليلاً شاملاً** للمحادثات العربية والإنجليزية مع متحدثين متعددين:

### **تحليل المحادثة**
- المشاعر العامة والنبرة العاطفية
- الموضوعات الرئيسية والمحاور التي تمت مناقشتها
- ملخص المحادثة واللحظات الرئيسية
- تقييم الجودة والترابط

### **تحليل المتحدثين**
- تحديد هوية المتحدث الفردي
- مشاعر كل متحدث وحالته العاطفية
- أسلوب التحدث والدور في المحادثة
- إحصائيات وقت التحدث والأدوار

### **العروض والميزات الصوتية**
- طبقة الصوت، الطاقة، ومعدل التحدث
- جودة الصوت والخصائص
- قياسات صوتية كمية

### **ديناميكيات التفاعل**
- أنماط تبادل الأدوار (من يتحدث متى)
- التوازن في المحادثة والسيطرة
- مستويات الألفة والتعاون
- المقاطعات والتداخلات

**التنسيقات المدعومة:** WAV, MP3, M4A, FLAC, OGG

**المدة القصوى:** ~40 دقيقة موصى بها
"""

STRINGS: dict[Lang, dict[str, str]] = {
    "EN": {
        # Header and upload
        "title": "Sawt · صوت",
        "subtitle": "**Arabic & English conversation analysis**",
        "about_expander": "What does this analyze?",
        "about_content": _ABOUT_EN,
        "upload_label": "Upload an audio file (Arabic or English)",
        "upload_help": "Upload a conversation recording with 1 or more speakers",
        "analyze_btn": "Analyze Conversation",
        "analyzing": "Analyzing conversation... Please wait...",
        "success": "Analysis complete in {}",
        "error": "Analysis failed: {}",
        "technical_details": "Technical details",
        # API status
        "api_unreachable": "Cannot reach the Sawt API at {}. Start the backend, then refresh this page.",
        "models_loading": "The analysis models are still loading. This can take a few minutes on first start.",
        "models_unavailable": "The analysis models failed to load, so the API cannot analyze audio right now.",
        "english_only": "Arabic translation is unavailable; results are shown in English.",
        # Overview
        "conv_overview": "Conversation Overview",
        "overall_sentiment": "Overall Sentiment",
        "sentiment_caption": "The general emotional tone",
        "quality": "Quality",
        "quality_caption": "Overall coherence and structure",
        "duration": "Duration",
        "duration_caption": "Total length of recording",
        "main_topics": "Main Topics",
        "summary": "Summary",
        "key_moments": "Key Moments in the Conversation",
        "detailed_report": "Detailed Analysis Report",
        # Speakers
        "speaker_timeline": "Speaker Timeline",
        "timeline_caption": "Visual representation of when each speaker talks",
        "speaker_stats": "Speaker Statistics",
        "time": "Time",
        "turns": "Turns",
        "avg_turn": "Avg Turn",
        "speaker_analysis": "Speaker Analysis",
        "sentiment": "Sentiment",
        "role": "Role",
        "role_caption": "Function in conversation",
        "speaking_time": "Speaking Time",
        "speaking_time_caption": "% of total conversation",
        "style": "Style",
        "emotional_state": "Emotional State",
        "key_contributions": "Key Contributions",
        "characteristic_phrases": "Characteristic Phrases",
        # Charts
        "chart_time_axis": "Time (seconds)",
        "chart_speaker_axis": "Speaker",
        "start": "Start",
        "end": "End",
        "speaking_time_distribution": "Speaking Time Distribution",
        # Prosody
        "prosody_analysis": "Prosody & Acoustic Analysis",
        "prosody_caption": "Prosody refers to the rhythm, stress, and intonation patterns in speech",
        "pitch": "Pitch",
        "speaking_rate": "Speaking Rate",
        "energy": "Energy",
        "tone_quality": "Tone Quality",
        "emotional_progression": "Emotional Progression",
        "notable_features": "Notable Acoustic Features",
        "speaker_differences": "Speaker Differences",
        "prosodic_markers": "Prosodic Markers",
        "emphasis": "Emphasis",
        "pauses": "Pauses",
        "intonation": "Intonation",
        "detailed_measurements": "Detailed Acoustic Measurements",
        "mean_pitch": "Mean Pitch",
        "pitch_range": "Pitch Range",
        "pitch_caption": "Pitch is the perceived frequency of voice",
        "syllables_per_second": "Syllables/Second",
        "rate_caption": "Normal speech is 3-5 syllables/sec",
        "voice_quality": "Voice Quality",
        "brightness": "Brightness",
        "voice_caption": "Voice quality describes the timbre and resonance",
        # Interaction dynamics
        "interaction_dynamics": "Interaction Dynamics",
        "interaction_caption": "How speakers interact with each other during the conversation",
        "turn_taking_patterns": "Turn-Taking Patterns",
        "total_turns": "Total turns",
        "speaker_switches": "Speaker switches",
        "avg_gap": "Avg gap",
        "overlaps": "Overlaps",
        "balance": "Balance",
        "relationship_quality": "Relationship Quality",
        "rapport": "Rapport",
        "cooperation": "Cooperation",
        "interruptions": "Interruptions",
        "turn_taking_style": "Turn-Taking Style",
        "conversation_dynamics": "Conversation Dynamics",
        "conversation_flow": "Conversation Flow",
        "interaction_quality": "Interaction Quality",
        "dominance_pattern": "Dominance Pattern",
        "engagement_levels": "Engagement Levels",
        # Export
        "export_results": "Export Results",
        "download_json": "Download JSON",
        "download_report": "Download Report",
    },
    "AR": {
        # Header and upload
        "title": "Sawt · صوت",
        "subtitle": "**تحليل المحادثات العربية والإنجليزية**",
        "about_expander": "ماذا يحلل هذا؟",
        "about_content": _ABOUT_AR,
        "upload_label": "تحميل ملف صوتي (عربي أو إنجليزي)",
        "upload_help": "تحميل تسجيل محادثة مع متحدث واحد أو أكثر",
        "analyze_btn": "تحليل المحادثة",
        "analyzing": "جاري تحليل المحادثة... يرجى الانتظار...",
        "success": "اكتمل التحليل في {}",
        "error": "فشل التحليل: {}",
        "technical_details": "تفاصيل تقنية",
        # API status
        "api_unreachable": "تعذر الاتصال بواجهة صوت البرمجية على {}. شغّل الخادم ثم حدّث هذه الصفحة.",
        "models_loading": "لا تزال نماذج التحليل قيد التحميل. قد يستغرق ذلك بضع دقائق عند التشغيل الأول.",
        "models_unavailable": "تعذر تحميل نماذج التحليل، لذا لا يمكن تحليل الصوت حاليًا.",
        "english_only": "الترجمة العربية غير متاحة؛ تُعرض النتائج باللغة الإنجليزية.",
        # Overview
        "conv_overview": "نظرة عامة على المحادثة",
        "overall_sentiment": "المشاعر العامة",
        "sentiment_caption": "النبرة العاطفية العامة",
        "quality": "الجودة",
        "quality_caption": "الترابط والهيكل العام",
        "duration": "المدة",
        "duration_caption": "إجمالي طول التسجيل",
        "main_topics": "الموضوعات الرئيسية",
        "summary": "الملخص",
        "key_moments": "لحظات رئيسية في المحادثة",
        "detailed_report": "تقرير التحليل المفصل",
        # Speakers
        "speaker_timeline": "الجدول الزمني للمتحدثين",
        "timeline_caption": "تمثيل مرئي لوقت تحدث كل متحدث",
        "speaker_stats": "إحصائيات المتحدثين",
        "time": "الوقت",
        "turns": "الأدوار",
        "avg_turn": "متوسط الدور",
        "speaker_analysis": "تحليل المتحدثين",
        "sentiment": "المشاعر",
        "role": "الدور",
        "role_caption": "الوظيفة في المحادثة",
        "speaking_time": "وقت التحدث",
        "speaking_time_caption": "% من إجمالي المحادثة",
        "style": "الأسلوب",
        "emotional_state": "الحالة العاطفية",
        "key_contributions": "المساهمات الرئيسية",
        "characteristic_phrases": "العبارات المميزة",
        # Charts
        "chart_time_axis": "الوقت (ثانية)",
        "chart_speaker_axis": "المتحدث",
        "start": "البداية",
        "end": "النهاية",
        "speaking_time_distribution": "توزيع وقت التحدث",
        # Prosody
        "prosody_analysis": "تحليل العروض والميزات الصوتية",
        "prosody_caption": "تشير العروض إلى الإيقاع والضغط وأنماط التنغيم في الكلام",
        "pitch": "طبقة الصوت",
        "speaking_rate": "معدل التحدث",
        "energy": "الطاقة",
        "tone_quality": "جودة النبرة",
        "emotional_progression": "تطور المشاعر",
        "notable_features": "ميزات صوتية بارزة",
        "speaker_differences": "الاختلافات بين المتحدثين",
        "prosodic_markers": "العلامات العروضية",
        "emphasis": "التوكيد",
        "pauses": "الوقفات",
        "intonation": "نبرة الصوت",
        "detailed_measurements": "قياسات صوتية مفصلة",
        "mean_pitch": "متوسط طبقة الصوت",
        "pitch_range": "نطاق طبقة الصوت",
        "pitch_caption": "طبقة الصوت هي التردد الملحوظ للصوت",
        "syllables_per_second": "مقطع/ثانية",
        "rate_caption": "الكلام الطبيعي هو 3-5 مقاطع/ثانية",
        "voice_quality": "جودة الصوت",
        "brightness": "السطوع",
        "voice_caption": "تصف جودة الصوت الجرس والرنين",
        # Interaction dynamics
        "interaction_dynamics": "ديناميكيات التفاعل",
        "interaction_caption": "كيف يتفاعل المتحدثون مع بعضهم البعض أثناء المحادثة",
        "turn_taking_patterns": "أنماط تبادل الأدوار",
        "total_turns": "إجمالي الأدوار",
        "speaker_switches": "تبديل المتحدثين",
        "avg_gap": "متوسط الفجوة",
        "overlaps": "التداخلات",
        "balance": "التوازن",
        "relationship_quality": "جودة العلاقة",
        "rapport": "الألفة",
        "cooperation": "التعاون",
        "interruptions": "المقاطعات",
        "turn_taking_style": "أسلوب تبادل الأدوار",
        "conversation_dynamics": "ديناميكيات الحوار",
        "conversation_flow": "سير المحادثة",
        "interaction_quality": "جودة التفاعل",
        "dominance_pattern": "نمط السيطرة",
        "engagement_levels": "مستويات المشاركة",
        # Export
        "export_results": "تصدير النتائج",
        "download_json": "تحميل JSON",
        "download_report": "تحميل التقرير",
    },
}


def t(key: str, lang: Lang) -> str:
    """The UI string ``key`` in ``lang``."""
    return STRINGS[lang][key]
