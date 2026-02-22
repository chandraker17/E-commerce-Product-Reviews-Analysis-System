"""
Sentiment analysis and data processing for E-commerce Product Reviews.
Supports TextBlob and VADER. Includes text cleaning, keyword extraction, and fake review detection.
"""
import re
import string
from collections import Counter

# Try importing NLP libraries
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader = SentimentIntensityAnalyzer()
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

# Stopwords (common English - subset for lightweight approach)
STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your",
    "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she",
    "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of",
    "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "in", "out", "on", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just",
    "don", "should", "now", "d", "ll", "m", "o", "re", "ve", "y", "ain", "aren",
    "couldn", "didn", "doesn", "hadn", "hasn", "haven", "isn", "ma", "mightn",
    "mustn", "needn", "shan", "shouldn", "wasn", "weren", "won", "wouldn",
}


def clean_text(text: str) -> str:
    """
    Clean review text: lowercase, remove punctuation, remove stopwords.
    Handles missing/empty values.
    """
    if not text or not isinstance(text, str):
        return ""
    text = str(text).strip().lower()
    text = re.sub(r"http\S+|www\S+", "", text)  # Remove URLs
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = text.split()
    words = [w for w in words if w not in STOPWORDS and len(w) > 1]
    return " ".join(words)


def get_tokens(text: str) -> list:
    """Get cleaned tokens for keyword extraction."""
    return clean_text(text).split()


def analyze_sentiment_textblob(text: str) -> tuple:
    """Analyze sentiment using TextBlob. Returns (label, score, subjectivity)."""
    if not TEXTBLOB_AVAILABLE or not text or not str(text).strip():
        return "Neutral", 0.0, 0.0
    blob = TextBlob(str(text))
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    label = _score_to_label(polarity)
    return label, polarity, subjectivity


def analyze_sentiment_vader(text: str) -> tuple:
    """Analyze sentiment using VADER. Returns (label, compound_score, None)."""
    if not VADER_AVAILABLE or not text or not str(text).strip():
        return "Neutral", 0.0, None
    scores = vader.polarity_scores(str(text))
    compound = scores["compound"]
    label = _compound_to_label(compound)
    return label, compound, None


def _score_to_label(polarity: float) -> str:
    """Convert polarity (-1 to 1) to sentiment label."""
    if polarity > 0.1:
        return "Positive"
    if polarity < -0.1:
        return "Negative"
    return "Neutral"


def _compound_to_label(compound: float) -> str:
    """Convert VADER compound score (-1 to 1) to sentiment label."""
    if compound >= 0.05:
        return "Positive"
    if compound <= -0.05:
        return "Negative"
    return "Neutral"


def analyze_sentiment(text: str, method: str = "vader") -> tuple:
    """
    Analyze sentiment. method: 'textblob' or 'vader'.
    Returns (label, sentiment_score, subjectivity_or_none).
    """
    if method == "textblob" and TEXTBLOB_AVAILABLE:
        return analyze_sentiment_textblob(text)
    if method == "vader" and VADER_AVAILABLE:
        return analyze_sentiment_vader(text)
    if TEXTBLOB_AVAILABLE:
        return analyze_sentiment_textblob(text)
    if VADER_AVAILABLE:
        return analyze_sentiment_vader(text)
    return "Neutral", 0.0, None


def get_top_keywords(texts: list, n: int = 10, min_len: int = 3) -> list:
    """Extract top N keywords from a list of texts."""
    all_tokens = []
    for t in texts:
        all_tokens.extend(get_tokens(str(t) if t else ""))
    filtered = [w for w in all_tokens if len(w) >= min_len]
    return [w for w, _ in Counter(filtered).most_common(n)]


def detect_fake_review(text: str, rating: int) -> tuple:
    """
    Basic fake review detection.
    Flags: repeated text, extreme rating mismatch, very short, excessive caps.
    Returns (is_suspicious: bool, reason: str).
    """
    reasons = []
    if not text:
        return True, "Empty review"
    text_str = str(text).strip()

    # Too short
    if len(text_str) < 10:
        reasons.append("Very short review")

    # Repeated phrases (same phrase 3+ times)
    words = text_str.lower().split()
    if len(words) >= 6:
        for i in range(len(words) - 2):
            phrase = " ".join(words[i : i + 3])
            if text_str.lower().count(phrase) >= 3:
                reasons.append("Repeated phrases")
                break

    # Extreme rating vs sentiment (basic heuristic)
    label, score, _ = analyze_sentiment(text_str, "vader")
    if rating >= 4 and label == "Negative" and score < -0.3:
        reasons.append("Rating/sentiment mismatch (high rating, negative text)")
    elif rating <= 2 and label == "Positive" and score > 0.3:
        reasons.append("Rating/sentiment mismatch (low rating, positive text)")

    # Excessive caps (>50% uppercase letters)
    letters = [c for c in text_str if c.isalpha()]
    if letters:
        upper_pct = sum(1 for c in letters if c.isupper()) / len(letters)
        if upper_pct > 0.5:
            reasons.append("Excessive capitalization")

    is_suspicious = len(reasons) > 0
    return is_suspicious, "; ".join(reasons) if reasons else "OK"


def get_recommendation(products_df) -> str:
    """
    Recommend best product based on sentiment + rating.
    products_df should have: product_name, avg_rating, pct_positive (or positive_count/total).
    """
    try:
        import pandas as pd
        if products_df is None or (hasattr(products_df, "empty") and products_df.empty):
            return "No products to recommend."
        df = pd.DataFrame(products_df) if not isinstance(products_df, pd.DataFrame) else products_df.copy()
        if df.empty:
            return "No products to recommend."
        if "pct_positive" not in df.columns and "positive_count" in df.columns and "total_reviews" in df.columns:
            df["pct_positive"] = (df["positive_count"] / df["total_reviews"].replace(0, 1) * 100).fillna(0)
        elif "pct_positive" not in df.columns:
            df["pct_positive"] = 0
        if "avg_rating" not in df.columns:
            df["avg_rating"] = 0
        df["score"] = df["avg_rating"] * 20 + df["pct_positive"] * 0.5
        idx = df["score"].idxmax()
        best = df.loc[idx]
        name_col = "product_name" if "product_name" in df.columns else df.columns[0]
        return str(best[name_col])
    except Exception:
        return "Unable to compute recommendation."
