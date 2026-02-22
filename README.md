# E-commerce-Product-Reviews-Analysis-System

Overview

This project is a Customer Feedback & Sentiment Analysis System focused on e-commerce product reviews.
It analyzes customer feedback, classifies sentiment, and presents insights through an interactive dashboard.

A. The goal is to help businesses:
-Understand customer satisfaction
-Identify product issues
-Make data-driven decisions

B. Key Features
Sentiment Analysis
-Classifies reviews into:
    Positive 😊
    Negative 😠
    Neutral 😐
-Uses TextBlob & VADER NLP models

C. Interactive Dashboard (Streamlit)
    Total Reviews
    Average Rating
    Sentiment Distribution

D. Trends over time
    Filters & Controls
    Filter by Product
    Filter by Rating
    View product-wise insights

E. Data Handling
    Stores data in MySQL database
    Supports CSV import/export
    Automated summary updates

F. Insights Generated
    Best performing products
    Worst performing products
    Positive vs Negative feedback ratio
    Keyword-based insights

G. Tech Stack
    Frontend: Streamlit
    Backend: Python
    Database: MySQL
    Libraries:
        pandas
        matplotlib
        plotly
        textblob
        vaderSentiment
        wordcloud

H. Project Structure
    │
    ├── app/
    │   ├── db.py
    │   ├── sentiment.py
    │
    ├── dashboard/
    │   └── app.py
    │
    ├── data/
    │   └── reviews.csv
    │
    ├── database/
    │   └── schema.sql
    │
    ├── requirements.txt
    └── README.md

I. Setup Instructions
1️⃣ Clone the Repository
git clone [https://github.com/your-username/repo-name.git](https://github.com/your-username/repo-name.git)
cd repo-name

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Setup Database (MySQL)
Open MySQL Workbench and run:
    CREATE DATABASE openfeedback;
    USE openfeedback;
 
 Then execute the schema.sql file.

4️⃣ Configure Database Connection
Update app/db.py:
   mysql.connector.connect(
        host="localhost",
        user="root",
        password="your_password",
        database="openfeedback"
    )
    
5️⃣ Run the Application
    streamlit run dashboard/app.py
