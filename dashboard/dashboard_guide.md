# Onboarding Optimization Dashboard Design Guide
**Power BI & Tableau Implementation Specification**

This guide provides the database model schema, calculated metric formulas (DAX & Tableau calculated fields), and visual wireframe guidelines to build an interactive dashboard showcasing the results of our onboarding A/B test.

---

## 🗄️ 1. Data Model & Relationships
For optimal performance in BI tools (Power BI, Tableau, or Looker), model the data as a **Star Schema**:

```text
       ┌────────────────────────┐
       │   dim_demographics     │
       ├────────────────────────┤
       │   user_id (PK)         │ 1
       │   signup_date          │──┐
       │   device               │  │
       │   country              │  │
       │   ab_variant           │  │
       └────────────────────────┘  │
                                   │ 1:N Relationship
                                   ▼
                       ┌────────────────────────┐
                       │      fact_events       │
                       ├────────────────────────┤
                       │   event_id (PK)        │
                       │   user_id (FK)         │
                       │   timestamp            │
                       │   event_name           │
                       │   event_value          │
                       └────────────────────────┘
```

*   **Relationship:** `dim_demographics[user_id]` (1) to `fact_events[user_id]` (Many).
*   **Cross-filter direction:** Single (Demographics filters Events).

---

## 🧮 2. Power BI Calculations (DAX)

Create the following calculated columns and measures in your Power BI data model:

### A. Calculated Columns (In `fact_events`)

*   **Cohort Day (Days since signup):**
    ```dax
    Days Since Signup = 
    DATEDIFF(
        RELATED(dim_demographics[signup_date]), 
        fact_events[timestamp], 
        DAY
    )
    ```

*   **Is Purchaser (Flag in `dim_demographics`):**
    ```dax
    Is Purchaser = 
    IF(
        CALCULATE(
            COUNT(fact_events[event_id]), 
            fact_events[event_name] = "purchase"
        ) > 0, 
        1, 
        0
    )
    ```

### B. Measures

*   **Unique Active Users:**
    ```dax
    Unique Active Users = DISTINCTCOUNT(fact_events[user_id])
    ```

*   **Conversion Rate (% of signups who purchase):**
    ```dax
    Conversion Rate = 
    DIVIDE(
        CALCULATE(DISTINCTCOUNT(fact_events[user_id]), fact_events[event_name] = "purchase"),
        DISTINCTCOUNT(dim_demographics[user_id]),
        0
    )
    ```

*   **Day-N Retention Rate (Cohort Measure):**
    ```dax
    Retention Rate = 
    VAR CurrentDay = SELECTEDVALUE(fact_events[Days Since Signup])
    VAR CohortStartUsers = 
        CALCULATE(
            [Unique Active Users], 
            ALLEXCEPT(dim_demographics, dim_demographics[ab_variant]), 
            fact_events[Days Since Signup] = 0
        )
    RETURN
    DIVIDE([Unique Active Users], CohortStartUsers, 0)
    ```

*   **Average Order Value (AOV):**
    ```dax
    Average Order Value = 
    DIVIDE(
        CALCULATE(SUM(fact_events[event_value]), fact_events[event_name] = "purchase"),
        CALCULATE(COUNT(fact_events[event_id]), fact_events[event_name] = "purchase"),
        0
    )
    ```

---

## 🧮 3. Tableau Calculations (LOD Expressions)

Create these calculated fields in Tableau to construct the visual sheets:

*   **Cohort Day (Days Since Signup):**
    ```tableau
    DATEDIFF('day', [signup_date], [timestamp])
    ```

*   **User Cohort Month:**
    ```tableau
    DATETRUNC('month', [signup_date])
    ```

*   **Is Purchaser:**
    ```tableau
    { FIXED [User Id] : MAX(IF [Event Name] = 'purchase' THEN 1 ELSE 0 END) }
    ```

*   **Conversion Rate:**
    ```tableau
    { FIXED [Ab Variant] : SUM([Is Purchaser]) } / { FIXED [Ab Variant] : COUNTD([User Id]) }
    ```

*   **Retention Rate:**
    ```tableau
    COUNTD([User Id]) / SUM({ FIXED [Ab Variant] : COUNTD(IF [Cohort Day] = 0 THEN [User Id] END) })
    ```

---

## 🎨 4. Wireframe Layout & Design Guidelines

For a premium, executive-ready look, apply a cohesive dark-mode theme or a crisp, professional light-mode layout using the specific HEX colors below.

### Visual Architecture Spec

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│   Onboarding A/B Test Experimentation Dashboard                                │
├────────────────────────────────────────────────────────────────────────────────┤
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────────────────┐ │
│ │ Total Users   │ │ Conversion    │ │ 7D Retention  │ │ Significance Status  │ │
│ │  2,120        │ │ +20.6% Lift   │ │ +19.9% Lift   │ │ STATS SIGNIFICANT    │ │
│ └───────────────┘ └───────────────┘ └───────────────┘ └──────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────┐ ┌──────────────────────────────────┐ │
│ │                                       │ │                                  │ │
│ │      Onboarding Funnel (Control       │ │      Daily Retention Curves      │ │
│ │      vs. Treatment Comparison)        │ │      (Line Chart Day 0 to 7)     │ │
│ │                                       │ │                                  │ │
│ └───────────────────────────────────────┘ └──────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────┐ ┌──────────────────────────────────┐ │
│ │                                       │ │                                  │ │
│ │      Cohort Retention Matrix          │ │      Revenue Impact & ROI        │ │
│ │      (Pre-Test Weekly Heatmap)        │ │      (Value cards, segment table)│ │
│ │                                       │ │                                  │ │
│ └───────────────────────────────────────┘ └──────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Color Guide
*   **Control Metric Fill:** `#4A90E2` (Cool Slate Blue)
*   **Treatment Metric Fill:** `#50E3C2` (Muted Sea Teal)
*   **Background Cards:** `#FFFFFF` (Card background with light grey `#F5F7FA` borders)
*   **Text/Titles:** Dark Slate `#1A202C`

---

## 📈 5. Dashboard Story Points
When presenting this dashboard to stakeholders, structure your page navigation or story tabs to guide them through the data narrative:
1.  **Tab 1: Executive Overview:** High-level experiment results, significance calls, and final ROI.
2.  **Tab 2: Funnel Drop-offs:** The interactive funnel where you filter by device (iOS vs Android) to show where the specific friction points occurred.
3.  **Tab 3: Cohort & User Behavior:** Retention matrices showing weekly improvement and user-segment behavior over time.
