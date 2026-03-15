# 📖 Data Dictionary
### Amazon India Analytics Platform — Column Reference Guide

---

## 🗄️ Database Schema Overview
```sql
amazon_india.db
├── transactions    (primary fact table — ~1M rows)
├── products        (product master — 2000+ rows)
├── customers       (customer master — 355K+ rows)
└── time_dimension  (date lookup table)
```

---

## 📦 Table 1: transactions

| Column | Data Type | Description | Example |
|---|---|---|---|
| transaction_id | TEXT | Unique transaction identifier | TXN-2020-000001 |
| order_date | DATE | Order placement date (YYYY-MM-DD) | 2020-10-15 |
| customer_id | TEXT | Unique customer identifier | CUST-00001 |
| product_id | TEXT | Unique product identifier | PROD-001 |
| original_price_inr | REAL | Listed price before discount (₹) | 75000.00 |
| discount_percent | REAL | Discount applied (%) | 15.0 |
| discounted_price_inr | REAL | Price after discount (₹) | 63750.00 |
| quantity | INTEGER | Number of units ordered | 1 |
| subtotal_inr | REAL | discounted_price × quantity (₹) | 63750.00 |
| delivery_charges | REAL | Delivery fee charged (₹) | 0.00 |
| final_amount_inr | REAL | Total amount paid (₹) | 63750.00 |
| payment_method | TEXT | Payment method used | UPI |
| delivery_days | INTEGER | Days taken for delivery | 2 |
| delivery_type | TEXT | Type of delivery service | Express |
| is_prime_member | INTEGER | Prime membership flag (1=Yes, 0=No) | 1 |
| is_festival_sale | INTEGER | Festival sale flag (1=Yes, 0=No) | 1 |
| festival_name | TEXT | Name of festival if applicable | Diwali Sale |
| customer_rating | REAL | Customer rating given (1.0–5.0) | 4.5 |
| return_status | TEXT | Order return status | Delivered |
| order_year | INTEGER | Year of order (derived) | 2020 |
| product_weight_kg | REAL | Weight of product in kg | 0.35 |

### return_status Values
| Value | Description |
|---|---|
| Delivered | Order successfully delivered, not returned |
| Returned | Order delivered but returned by customer |
| Cancelled | Order cancelled before delivery |

### payment_method Values
| Value | Description |
|---|---|
| UPI | Unified Payments Interface (PhonePe, GPay, Paytm) |
| Cash on Delivery | Payment on delivery |
| Credit Card | Visa, Mastercard, Amex |
| Debit Card | Bank debit cards |
| Net Banking | Internet banking transfer |
| Wallet | Digital wallets |
| BNPL | Buy Now Pay Later |

---

## 🛍️ Table 2: products

| Column | Data Type | Description | Example |
|---|---|---|---|
| product_id | TEXT | Unique product identifier | PROD-001 |
| product_name | TEXT | Full product name | Samsung Galaxy S21 |
| category | TEXT | Major product category | Electronics |
| subcategory | TEXT | Product subcategory | Smartphones |
| brand | TEXT | Product brand name | Samsung |
| product_rating | REAL | Average product rating (1.0–5.0) | 4.3 |
| is_prime_eligible | INTEGER | Prime eligibility flag (1=Yes, 0=No) | 1 |
| base_price_2015 | REAL | Base price at launch in 2015 (₹) | 45000.00 |
| weight_kg | REAL | Product weight in kg | 0.17 |
| launch_year | INTEGER | Year product was launched | 2019 |
| model | TEXT | Product model identifier | SM-G991B |

### category Values
| Category | Subcategories |
|---|---|
| Electronics | Smartphones, Laptops, Tablets, Smart Watch, Audio, TV and Entertainment |
| Fashion | Men's Clothing, Women's Clothing, Footwear, Accessories |
| Home & Kitchen | Kitchen Appliances, Furniture, Home Decor, Bedding |
| Books | Fiction, Non-Fiction, Academic, Children's |
| Sports | Fitness Equipment, Outdoor, Team Sports |
| Beauty | Skincare, Haircare, Makeup, Fragrances |
| Toys | Educational, Action Figures, Board Games |
| Grocery | Fresh, Packaged, Beverages, Snacks |

---

## 👥 Table 3: customers

| Column | Data Type | Description | Example |
|---|---|---|---|
| customer_id | TEXT | Unique customer identifier | CUST-00001 |
| customer_city | TEXT | Customer's city | Mumbai |
| customer_state | TEXT | Customer's state | Maharashtra |
| customer_tier | TEXT | City tier classification | Metro |
| customer_age_group | TEXT | Age group bracket | 26-35 |
| customer_spending_tier | TEXT | Spending classification | High |
| is_prime_member | INTEGER | Prime membership flag (1=Yes, 0=No) | 1 |

### customer_tier Values
| Tier | Description | Example Cities |
|---|---|---|
| Metro | Top 6 metropolitan cities | Mumbai, Delhi, Bengaluru, Chennai, Kolkata, Hyderabad |
| Tier1 | Major state capitals and large cities | Jaipur, Lucknow, Ahmedabad, Pune |
| Tier2 | Secondary cities | Indore, Coimbatore, Bhopal, Surat |
| Rural | Smaller towns and rural areas | Smaller districts |

### customer_age_group Values
| Group | Age Range |
|---|---|
| 18-25 | Young adults / students |
| 26-35 | Core working professionals |
| 36-45 | Mid-career / family buyers |
| 46-55 | Senior professionals |
| 55+ | Senior citizens |

### customer_spending_tier Values
| Tier | Description |
|---|---|
| High | Top 20% spenders by lifetime value |
| Medium | Middle 50% spenders |
| Low | Bottom 30% spenders |

---

## 📅 Table 4: time_dimension

| Column | Data Type | Description | Example |
|---|---|---|---|
| date | DATE | Calendar date | 2020-10-15 |
| year | INTEGER | Year | 2020 |
| month | INTEGER | Month number (1-12) | 10 |
| month_name | TEXT | Month name | October |
| quarter | INTEGER | Quarter (1-4) | 4 |
| quarter_name | TEXT | Quarter label | Q4 |
| is_festival_month | INTEGER | Festival month flag | 1 |
| week_of_year | INTEGER | Week number (1-52) | 42 |
| day_of_week | TEXT | Day name | Thursday |
| is_weekend | INTEGER | Weekend flag (1=Yes) | 0 |

---

## 📊 Derived Metrics Used in Dashboard

| Metric | Formula | Used In |
|---|---|---|
| Revenue (₹Cr) | SUM(final_amount_inr) / 1e7 | All pages |
| Revenue (₹Bn) | SUM(final_amount_inr) / 1e9 | Executive page |
| AOV (₹K) | AVG(final_amount_inr) / 1000 | Executive, Customer |
| Return Rate % | SUM(returned) / COUNT(*) × 100 | Operations page |
| On-Time Rate % | SUM(delivery_days≤3) / COUNT(*) × 100 | Operations page |
| Prime % | SUM(is_prime=1) / COUNT(*) × 100 | Customer page |
| Festival Lift % | (Festival AOV / Normal AOV - 1) × 100 | Festival page |
| YoY Growth % | (Current Year Rev / Last Year Rev - 1) × 100 | Revenue page |
| RFM Score | R_score + F_score + M_score (3-15) | Customer page |
| CLV | AVG(monetary) × AVG(frequency) | Customer page |
| Health Score | Weighted avg of 4 operational KPIs (0-100) | Executive page |

---

## 🔍 Data Quality Notes

| Column | Known Issues | Cleaning Applied |
|---|---|---|
| order_date | 4 mixed formats + invalid dates | Standardized to YYYY-MM-DD |
| original_price_inr | ₹ symbols, commas, text entries | Stripped to numeric |
| customer_rating | Stars text, fraction format, nulls | Normalized to 1.0-5.0 |
| customer_city | Bangalore/Bengaluru, case variations | Mapped to standard names |
| is_prime_member | True/False/Yes/No/1/0/Y/N | Converted to 1/0 |
| category | Case variations, ampersand variations | Standardized to 8 categories |
| delivery_days | Negatives, text, extreme values | Clipped to valid range 0-14 |
| payment_method | UPI/PhonePe/GPay merged | Consolidated to 7 categories |
| original_price_inr | 100x outliers from decimal errors | IQR correction applied |
| transaction_id | Genuine vs error duplicates | Strategy-based deduplication |

---

*Amazon India Analytics Platform · GUVI × HCL Capstone Project · 2015–2025*