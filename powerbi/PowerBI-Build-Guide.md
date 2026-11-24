# Rebuilding this dashboard in Power BI (about 1 hour)

The interactive dashboard ships as HTML because Power BI Desktop files (.pbix) can only be authored on Windows. This guide recreates the same dashboard from the cleaned data.

## 1. Get the data (5 min)
- Open Power BI Desktop > Get Data > Text/CSV.
- Import `data/clean/orders_master.csv` and `data/clean/order_items_full.csv`.
- In Power Query, set types: dates as Date/Time, `total_price`/`total_freight` as Decimal, `is_late` as True/False.

## 2. Model (2 min)
- Relationship: `order_items_full[order_id]` > `orders_master[order_id]`, many-to-one, single direction.

## 3. Measures (10 min)
```dax
Revenue = SUM(orders_master[total_price])
Orders = COUNTROWS(orders_master)
AOV = DIVIDE([Revenue], [Orders])
Late Rate % = DIVIDE(CALCULATE([Orders], orders_master[is_late] = TRUE()), [Orders])
Avg Review = AVERAGE(orders_master[review_score])
```

## 4. Pages and visuals (30 min)
1. **KPI cards** (Card visual): Revenue, Orders, AOV, Late Rate %, Avg Review.
2. **Monthly revenue**: Line chart, `purchase_month` axis, Revenue values. Add a text box for the Black Friday peak (Nov 2017).
3. **Top categories**: Bar chart from `order_items_full`, `category_en` vs `SUM(price)`, Top N filter = 10.
4. **Late vs on-time reviews**: Clustered column chart; axis = `review_score`, values = % of orders, legend = `is_late`.
5. **Delivery time**: Histogram (bin `delivery_days` by 1 day).
6. **Payment mix**: Donut chart, `main_payment_type` vs order count.

## 5. Polish (10 min)
- Theme: navy #1B2A4A, accent #E8590C, teal #0CA678.
- Titles state the takeaway ("Late deliveries destroy customer ratings"), not the chart type.
- Save as `olist-dashboard.pbix` and export a PDF for the portfolio.

Tip: the report PDF in this project shows the exact five findings and the numbers each visual must reproduce - use it as the acceptance check.
