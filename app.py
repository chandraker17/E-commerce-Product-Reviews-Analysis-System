"""
E-commerce Product Reviews Analysis System
Streamlit dashboard for sentiment analysis, insights, and product recommendations.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
from db import get_connection, read_sql_dataframe
from sentiment import (
    analyze_sentiment,
    clean_text,
    get_top_keywords,
    detect_fake_review,
    get_recommendation,
)

# --------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="E-commerce Product Reviews Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# CUSTOM CSS - Off-white background, black text
# --------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main app background - off white */
    .stApp {
        background-color: #f5f5f0;
    }

    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #000000;
        margin: 1.5rem 0 0.75rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #6366f1;
    }

    /* KPI cards */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #000000 !important;
    }

    [data-testid="metric-container"] {
        background-color: #ffffff;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #fafaf8;
    }
    [data-testid="stSidebar"] * {
        color: #000000 !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #6366f1;
        color: white !important;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #4f46e5;
    }

    /* Headers and text - black */
    h1, h2, h3, h4 {
        color: #000000 !important;
    }
    p, span, label {
        color: #000000 !important;
    }
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] span,
    [data-testid="stAppViewContainer"] label {
        color: #000000 !important;
    }

    /* Dividers */
    hr {
        border-color: #d0d0d0 !important;
        margin: 1.5rem 0 !important;
    }

    /* Expander / containers */
    .streamlit-expanderHeader {
        background-color: #ffffff;
        border-radius: 8px;
    }

    /* DataFrames */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# INIT & DATA LOADING
# --------------------------------------------------------------------------
@st.cache_data(ttl=60)
def load_reviews_data():
    """Load all review data with sentiment. Cached for 60s."""
    query = """
    SELECT f.feedback_id, f.user_id, f.product_name, f.category, f.feedback_text,
           f.rating, f.created_at, f.is_suspicious,
           s.sentiment_label, s.sentiment_score, s.subjectivity_score
    FROM feedback f
    LEFT JOIN sentiment_analysis s ON f.feedback_id = s.feedback_id
    ORDER BY f.created_at DESC
    """
    try:
        df = read_sql_dataframe(query)
    except Exception as e:
        # Fallback if category/is_suspicious don't exist
        query_simple = """
        SELECT f.feedback_id, f.user_id, f.product_name, f.feedback_text,
               f.rating, f.created_at,
               s.sentiment_label, s.sentiment_score
        FROM feedback f
        LEFT JOIN sentiment_analysis s ON f.feedback_id = s.feedback_id
        ORDER BY f.created_at DESC
        """
        try:
            df = read_sql_dataframe(query_simple)
            df["category"] = None
            df["is_suspicious"] = False
        except Exception:
            st.error(f"Database error: {e}")
            return pd.DataFrame()
    return df


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Data processing: handle missing values, add derived columns, clean text."""
    if df.empty:
        return df
    out = df.copy()
    out["feedback_text"] = out["feedback_text"].fillna("").astype(str)
    out["product_name"] = out["product_name"].fillna("Unknown")
    out["rating"] = pd.to_numeric(out["rating"], errors="coerce").fillna(0).astype(int)
    out["sentiment_label"] = out["sentiment_label"].fillna("Neutral")
    out["sentiment_score"] = pd.to_numeric(out["sentiment_score"], errors="coerce").fillna(0)
    out["created_at"] = pd.to_datetime(out["created_at"], errors="coerce")
    out["cleaned_text"] = out["feedback_text"].apply(clean_text)
    out["word_count"] = out["cleaned_text"].str.split().str.len().fillna(0).astype(int)
    return out


# --------------------------------------------------------------------------
# HEADER
# --------------------------------------------------------------------------
st.markdown("""
<div style="text-align: center; padding: 1rem 0;">
    <h1>E-commerce Product Reviews Analysis System</h1>
    <p style="color: #000000; font-size: 1.1rem;">Sentiment insights, trends & recommendations</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# --------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧭 Navigation")
    menu = st.radio(
        "Go to",
        [
            "Dashboard",
            "Add Review",
            "View Reviews",
            "Insights",
            "Advanced Features",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("### Settings")
    sentiment_method = st.selectbox("Sentiment Engine", ["vader", "textblob"], help="VADER: social/text. TextBlob: general.")
    st.caption("VADER works better for short, informal reviews.")

# --------------------------------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------------------------------
try:
    conn = get_connection()
except Exception as e:
    st.error(f"Database connection failed: {e}. Check MySQL and db.py.")
    st.stop()

# Load data
df_raw = load_reviews_data()
df = process_dataframe(df_raw)

# --------------------------------------------------------------------------
# PAGE: DASHBOARD
# --------------------------------------------------------------------------
if "Dashboard" in menu:
    st.markdown("## Analytics Dashboard")
    if df.empty:
        st.info("No reviews yet. Add reviews to see analytics.")
    else:
        # Filters
        with st.expander("Filters", expanded=False):
            f1, f2, f3, f4 = st.columns(4)
            with f1:
                products = ["All"] + sorted(df["product_name"].dropna().unique().tolist())
                filter_product = st.selectbox("Product", products)
            with f2:
                if "category" in df.columns and df["category"].notna().any():
                    cats = ["All"] + sorted(df["category"].dropna().unique().tolist())
                    filter_cat = st.selectbox("Category", cats)
                else:
                    filter_cat = "All"
            with f3:
                filter_rating = st.selectbox("Rating", ["All", "5", "4", "3", "2", "1"])
            with f4:
                filter_sentiment = st.selectbox("Sentiment", ["All", "Positive", "Negative", "Neutral"])

        # Apply filters
        filtered = df.copy()
        if filter_product != "All":
            filtered = filtered[filtered["product_name"] == filter_product]
        if filter_cat != "All" and "category" in filtered.columns:
            filtered = filtered[filtered["category"] == filter_cat]
        if filter_rating != "All":
            filtered = filtered[filtered["rating"] == int(filter_rating)]
        if filter_sentiment != "All":
            filtered = filtered[filtered["sentiment_label"] == filter_sentiment]

        # KPI Cards
        st.markdown("### Key Metrics")
        total = len(filtered)
        positive = len(filtered[filtered["sentiment_label"] == "Positive"])
        pct_positive = (100 * positive / total) if total else 0
        avg_rating = filtered["rating"].mean()
        neutral = len(filtered[filtered["sentiment_label"] == "Neutral"])
        negative = len(filtered[filtered["sentiment_label"] == "Negative"])

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Reviews", total)
        k2.metric("Avg Rating", f"{avg_rating:.1f}" if total else "—")
        k3.metric("% Positive", f"{pct_positive:.0f}%", delta=f"{positive} reviews")
        k4.metric("Negative", negative, delta=f"{100*negative/total:.0f}%" if total else "0%")

        st.markdown("---")

        # Charts row
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Sentiment Distribution")
            sent_counts = filtered["sentiment_label"].value_counts().reset_index()
            sent_counts.columns = ["Sentiment", "Count"]
            fig_pie = px.pie(
                sent_counts, values="Count", names="Sentiment",
                color="Sentiment",
                color_discrete_map={"Positive": "#22c55e", "Negative": "#ef4444", "Neutral": "#eab308"},
            )
            fig_pie.update_layout(margin=dict(t=10, b=10), showlegend=True, height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

        with c2:
            st.markdown("#### Ratings Distribution")
            rating_counts = filtered["rating"].value_counts().sort_index().reset_index()
            rating_counts.columns = ["Rating", "Count"]
            fig_bar = px.bar(rating_counts, x="Rating", y="Count", color="Count", color_continuous_scale="Blues")
            fig_bar.update_layout(margin=dict(t=10, b=10), height=300, xaxis=dict(tickmode="linear"))
            st.plotly_chart(fig_bar, use_container_width=True)

        # Reviews over time
        st.markdown("#### Reviews Over Time")
        if "created_at" in filtered.columns and filtered["created_at"].notna().any():
            ts = filtered.copy()
            ts["date"] = ts["created_at"].dt.date
            ts_counts = ts.groupby("date").size().reset_index(name="Reviews")
            fig_line = px.line(ts_counts, x="date", y="Reviews", markers=True)
            fig_line.update_layout(margin=dict(t=10, b=10), height=300)
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.caption("No date data available for trend chart.")

# --------------------------------------------------------------------------
# PAGE: ADD REVIEW
# --------------------------------------------------------------------------
elif "Add Review" in menu:
    st.markdown("## Add Product Review")

    feedback_text = st.text_area(
        "Review Text",
        placeholder="Share your experience with this product...",
        height=120,
        key="add_review_text",
    )
    if feedback_text:
        label, score, subj = analyze_sentiment(feedback_text, sentiment_method)
        st.info(f"**Live Sentiment:** {label} | Score: {score:.2f}")

    with st.form("review_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            user_id = st.number_input("User ID", min_value=1, value=1)
            product_name = st.text_input("Product Name", placeholder="e.g. Wireless Earbuds Pro")
        with col_b:
            category = st.text_input("Category (optional)", placeholder="e.g. Electronics")
            rating = st.slider("Rating", 1, 5, 3)
        submit = st.form_submit_button("Submit Review")

    if submit:
        if not feedback_text or not feedback_text.strip():
            st.warning("Please enter review text.")
        elif not product_name or not product_name.strip():
            st.warning("Please enter product name.")
        else:
            try:
                is_fake, reason = detect_fake_review(feedback_text, rating)
                label, score, subj = analyze_sentiment(feedback_text, sentiment_method)
                suspicious_val = 1 if is_fake else 0

                # Insert feedback (try with category first)
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        """INSERT INTO feedback (user_id, product_name, category, feedback_text, rating, is_suspicious)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (user_id, product_name.strip(), category.strip() or None, feedback_text.strip(), rating, suspicious_val),
                    )
                except Exception:
                    cursor.execute(
                        """INSERT INTO feedback (user_id, product_name, feedback_text, rating)
                           VALUES (%s, %s, %s, %s)""",
                        (user_id, product_name.strip(), feedback_text.strip(), rating),
                    )
                conn.commit()
                fid = cursor.lastrowid
                cursor.close()

                cursor = conn.cursor()
                try:
                    cursor.execute(
                        """INSERT INTO sentiment_analysis (feedback_id, sentiment_label, sentiment_score, subjectivity_score)
                           VALUES (%s, %s, %s, %s)""",
                        (fid, label, score, subj),
                    )
                except Exception:
                    cursor.execute(
                        """INSERT INTO sentiment_analysis (feedback_id, sentiment_label, sentiment_score)
                           VALUES (%s, %s, %s)""",
                        (fid, label, score),
                    )
                conn.commit()
                cursor.close()

                if is_fake:
                    st.warning(f"Review submitted but flagged as suspicious: {reason}")
                else:
                    st.success("Review submitted and sentiment analyzed.")
            except Exception as e:
                st.error(f"Error: {e}")

# --------------------------------------------------------------------------
# PAGE: VIEW REVIEWS
# --------------------------------------------------------------------------
elif "View Reviews" in menu:
    st.markdown("## Review Records")

    if df.empty:
        st.info("No reviews yet. Add reviews to get started.")
    else:
        with st.expander("Filters", expanded=True):
            v1, v2, v3 = st.columns(3)
            with v1:
                products = ["All"] + sorted(df["product_name"].dropna().unique().tolist())
                v_product = st.selectbox("Product", products, key="v_product")
            with v2:
                v_sentiment = st.selectbox("Sentiment", ["All", "Positive", "Negative", "Neutral"], key="v_sentiment")
            with v3:
                v_search = st.text_input("Search in text", placeholder="Keywords...", key="v_search")

        vf = df.copy()
        if v_product != "All":
            vf = vf[vf["product_name"] == v_product]
        if v_sentiment != "All":
            vf = vf[vf["sentiment_label"] == v_sentiment]
        if v_search:
            vf = vf[vf["feedback_text"].str.contains(v_search, case=False, na=False)]

        st.caption(f"Showing {len(vf)} of {len(df)} reviews")
        display_cols = [c for c in ["product_name", "rating", "sentiment_label", "feedback_text", "created_at"] if c in vf.columns]
        st.dataframe(vf[display_cols], use_container_width=True, height=400)

        st.markdown("---")
        e1, e2, _ = st.columns([1, 1, 2])
        with e1:
            st.download_button("Download CSV", vf.to_csv(index=False).encode("utf-8"), "reviews.csv", "text/csv", key="dl1")
        with e2:
            buf = io.BytesIO()
            vf.to_excel(buf, index=False, engine="openpyxl")
            buf.seek(0)
            st.download_button("Download Excel", buf, "reviews.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl2")

# --------------------------------------------------------------------------
# PAGE: INSIGHTS
# --------------------------------------------------------------------------
elif "Insights" in menu:
    st.markdown("## Insights & Keywords")

    if df.empty:
        st.info("Add reviews to see insights.")
    else:
        pos_texts = df[df["sentiment_label"] == "Positive"]["feedback_text"].dropna().tolist()
        neg_texts = df[df["sentiment_label"] == "Negative"]["feedback_text"].dropna().tolist()

        i1, i2 = st.columns(2)
        with i1:
            st.markdown("#### Top Positive Keywords")
            top_pos = get_top_keywords(pos_texts, n=10)
            if top_pos:
                st.write(", ".join(top_pos))
            else:
                st.caption("No positive reviews yet")
        with i2:
            st.markdown("#### Top Negative Keywords")
            top_neg = get_top_keywords(neg_texts, n=10)
            if top_neg:
                st.write(", ".join(top_neg))
            else:
                st.caption("No negative reviews yet")

        st.markdown("---")
        st.markdown("#### 📦 Product Performance")

        prod_stats = df.groupby("product_name").agg(
            avg_rating=("rating", "mean"),
            total_reviews=("feedback_id", "count"),
            positive_count=("sentiment_label", lambda x: (x == "Positive").sum()),
        ).reset_index()
        prod_stats["pct_positive"] = (prod_stats["positive_count"] / prod_stats["total_reviews"] * 100).round(1)

        p1, p2 = st.columns(2)
        with p1:
            best = prod_stats.loc[prod_stats["avg_rating"].idxmax()]
            st.success(f"**Best Performing:** {best['product_name']} ({best['avg_rating']:.1f} avg rating, {best['pct_positive']:.0f}% positive)")
        with p2:
            worst = prod_stats.loc[prod_stats["avg_rating"].idxmin()]
            st.error(f"**Worst Performing:** {worst['product_name']} ({worst['avg_rating']:.1f} avg rating, {worst['pct_positive']:.0f}% positive)")

        st.markdown("---")
        st.markdown("#### Product Summary Table")
        st.dataframe(prod_stats.round(2), use_container_width=True)

        # Word clouds
        st.markdown("#### Word Clouds")
        wc1, wc2 = st.columns(2)
        with wc1:
            st.markdown("**All Reviews**")
            all_text = " ".join(df["feedback_text"].fillna("").astype(str))
            if all_text.strip():
                wc = WordCloud(width=400, height=200, background_color="white", colormap="viridis").generate(all_text)
                fig, ax = plt.subplots(figsize=(6, 3))
                ax.imshow(wc, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)
                plt.close()
        with wc2:
            st.markdown("**Negative Reviews**")
            neg_text = " ".join(neg_texts)
            if neg_text.strip():
                wc2 = WordCloud(width=400, height=200, background_color="white", colormap="Reds").generate(neg_text)
                fig2, ax2 = plt.subplots(figsize=(6, 3))
                ax2.imshow(wc2, interpolation="bilinear")
                ax2.axis("off")
                st.pyplot(fig2)
                plt.close()
            else:
                st.caption("No negative reviews")

# --------------------------------------------------------------------------
# PAGE: ADVANCED FEATURES
# --------------------------------------------------------------------------
elif "Advanced Features" in menu:
    st.markdown("## Advanced Features")

    if df.empty:
        st.info("Add reviews to use advanced features.")
    else:
        tab1, tab2, tab3 = st.tabs(["Fake Review Detection", "Product Comparison", "Recommendation"])

        with tab1:
            st.markdown("#### Suspicious Review Detection")
            has_susp = "is_suspicious" in df.columns
            suspicious = df[df["is_suspicious"] == True] if has_susp else pd.DataFrame()
            if has_susp and len(suspicious) > 0:
                st.warning(f"Found {len(suspicious)} potentially suspicious reviews.")
                st.dataframe(suspicious[["product_name", "rating", "feedback_text", "sentiment_label"]].head(20), use_container_width=True)
            else:
                st.caption("Run detection on new reviews (check 'Add Review' for flags). Or analyze below:")
            sample = st.text_area("Analyze review for fake signals:", "Great product! Amazing! Best ever!")
            r = st.slider("Rating", 1, 5, 5)
            if st.button("Check"):
                is_fake, reason = detect_fake_review(sample, r)
                if is_fake:
                    st.warning(f"Suspicious: {reason}")
                else:
                    st.success("No obvious fake signals detected.")

        with tab2:
            st.markdown("#### Compare Products")
            prods = df["product_name"].unique().tolist()
            if len(prods) < 2:
                st.caption("Need at least 2 products to compare.")
            else:
                p_a = st.selectbox("Product A", prods, key="pa")
                p_b = st.selectbox("Product B", [p for p in prods if p != p_a], key="pb")
                if p_a and p_b:
                    a = df[df["product_name"] == p_a]
                    b = df[df["product_name"] == p_b]
                    comp = pd.DataFrame({
                        "Metric": ["Avg Rating", "Total Reviews", "Positive %", "Negative %"],
                        p_a: [
                            a["rating"].mean().round(2),
                            len(a),
                            f"{100*(a['sentiment_label']=='Positive').sum()/len(a):.0f}%",
                            f"{100*(a['sentiment_label']=='Negative').sum()/len(a):.0f}%",
                        ],
                        p_b: [
                            b["rating"].mean().round(2),
                            len(b),
                            f"{100*(b['sentiment_label']=='Positive').sum()/len(b):.0f}%",
                            f"{100*(b['sentiment_label']=='Negative').sum()/len(b):.0f}%",
                        ],
                    })
                    st.dataframe(comp.set_index("Metric"), use_container_width=True)

        with tab3:
            st.markdown("#### Best Product Recommendation")
            _ps = df.groupby("product_name").agg(
                avg_rating=("rating", "mean"),
                total_reviews=("feedback_id", "count"),
                positive_count=("sentiment_label", lambda x: (x == "Positive").sum()),
            ).reset_index()
            _ps["pct_positive"] = (100 * _ps["positive_count"] / _ps["total_reviews"].replace(0, 1)).fillna(0)
            rec = get_recommendation(_ps)
            st.success(f"**Recommended:** {rec}")
            st.caption("Based on average rating + % positive sentiment.")
