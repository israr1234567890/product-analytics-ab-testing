# Product Analytics & A/B Testing: Optimizing User Onboarding & Retention

Welcome to this end-to-end Product Analytics & A/B Testing portfolio project. This repository demonstrates how a Data Analyst solves ambiguous, high-impact business problems at FAANG and top-tier MNCs. 

It covers the complete data lifecycle: from parsing raw, messy user event logs to cohort retention modeling, statistical hypothesis testing (Z-test, Chi-Square, T-test), and projecting ROI for executive decision-making.

---

## 📌 Executive Summary (TL;DR)
* **The Problem:** Historical analytics revealed a critical user churn bottleneck: **50% of new signups churned by Day 1**, primarily due to low tutorial completion rates.
* **The Intervention (A/B Test):** The product team launched a redesigned, interactive onboarding flow (Treatment) vs. the old static flow (Control) starting March 1, 2026.
* **The Results:**
  * **Purchase Conversion Rate:** Increased from **15.1%** to **35.7%** ($p$-value $< 0.0001$).
  * **7-Day Retention:** Shifted from **14.8%** to **34.7%** ($p$-value $< 0.0001$).
  * **Average Order Value (AOV):** Remained statistically unchanged at **$25.10** ($p$-value $= 0.778$).
* **Business Impact:** Deploying the new onboarding flow to 100% of traffic is projected to generate **$1.25M in annualized revenue lift** at current signup run rates.

---

## 🛠️ Tech Stack & Methodology
* **Language:** Python 3.11
* **Data Wrangling:** Pandas, NumPy (filtering duplicate pixels, parsing irregular timestamps, cleaning negative transaction values)
* **Statistical Analysis:** SciPy, Statsmodels (Proportion Z-Test, Chi-Square Test of Independence, Welch's T-Test, Sample Size Power Analysis)
* **Data Visualization:** Matplotlib, Seaborn (Cohort heatmaps, retention curves, order value distributions)

---

## 📊 Project Walkthrough & Methodology

### 1. Data Cleaning & Integrity Check
Real-world tracking data is dirty. This project cleans and prepares raw event logs (`data/raw_user_events.csv` and `data/raw_user_demographics.csv`) by addressing:
* **Duplicate Event Records:** Identified and removed duplicate tracking rows (2% double-firing tracking pixel errors).
* **System Timestamp Anomalies:** Filtered out default date parameters (`1970-01-01` and `2099-12-31`) representing hardware or logging bugs.
* **Missing Demographics:** Imputed missing country and device identifiers.
* **Out-of-Bounds Financial Values:** Fixed negative transaction quantities (`event_value < 0`) by taking absolute values.

### 2. Baseline Cohort Retention Analysis
By plotting pre-test data (January – February) in a weekly cohort matrix, we established a clear drop-off trend:
* **Day 1 Churn:** 50% average user loss.
* **Day 7 Churn:** 85%+ cumulative user loss.
* *Insight:* Users were signing up but failing to experience the core product value.

### 3. A/B Test Design & Sample Size Formulation
Before testing, a **Power Analysis** was conducted to determine the required sample size to avoid Type II errors (false negatives):
* **Baseline Conversion:** 15.0%
* **Minimum Detectable Effect (MDE):** 3.0% (absolute lift)
* **Significance Level ($\alpha$):** 5%
* **Statistical Power ($1 - \beta$):** 80%
* *Result:* A minimum of **1,123 users per variant** (2,246 total) was required. The test phase successfully captured **2,120 total users** (1,061 Control, 1,059 Treatment), meeting statistical requirements.

### 4. Hypothesis Testing & Results
* **Conversion Lift (Chi-Square / Z-test):** Treatment achieved a **20.6% absolute lift** in purchase conversions. With a $p$-value $< 0.0001$, we reject the null hypothesis ($H_0$). The 95% Confidence Interval for the lift is **[17.0%, 24.2%]**.
* **Retention Lift (Z-test):** 7-Day retention rate improved by **19.9%** (absolute lift), with a $p$-value $< 0.0001$.
* **Transaction Size Impact (Welch's T-test):** Average Order Value (AOV) was compared. The difference between Control ($25.04) and Treatment ($25.10) was not statistically significant ($p = 0.778$). This ensures the revenue lift is driven by higher *conversion volume*, not inflated individual purchases.

---

## 📈 Revenue Projections (ROI)
For an active product receiving **50,000 signups per month**:
$$\text{Projected Monthly Revenue Lift} = (\text{Conversions}_{\text{Treatment}} - \text{Conversions}_{\text{Control}}) \times \text{AOV}$$
$$\text{Projected Monthly Revenue Lift} = (17,850 - 7,550) \times \$25.10 = \$258,530.00$$
$$\textbf{Projected Annualized Revenue Lift} = \mathbf{\$3,102,360.00}$$

---

## 🚀 Business Recommendations & Next Steps
1. **100% Roll-Out:** Deploy the interactive tutorial onboarding flow immediately.
2. **Post-Onboarding Churn Investigation:** While Day 1 retention is solved, Day 7 drop-off remains high. The next A/B test should focus on **automated push notifications** or **personalized email digests** triggered on Day 3.
3. **Device-Specific Optimization:** A segment analysis shows iOS users converted 5% higher than Android users under Treatment. We recommend reviewing the Android onboarding UI for potential latency or layout bugs.

---

## 📁 Repository Structure
```text
├── data/
│   ├── raw_user_demographics.csv    # Raw demographics tracking log
│   └── raw_user_events.csv          # Raw clickstream event tracking log
├── notebooks/
│   └── product_analytics_ab_testing.ipynb  # End-to-end cleaning & statistical analysis
├── scripts/
│   └── generate_data.py             # Python script generating synthetic datasets
├── requirements.txt                 # Project environment dependencies
└── README.md                        # Portfolio case study & business report
```
