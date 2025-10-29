import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# -------------------------------
# 🕸️ Scraping Function
# -------------------------------
def scrape_scrapeme(pages=5):
    base_url = "https://scrapeme.live/shop/page/{}/"
    all_products = []

    for page in range(1, pages + 1):
        response = requests.get(base_url.format(page), verify=False)
        if response.status_code != 200:
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("li", class_="product")

        for item in items:
            # Name
            name_tag = item.find("h2", class_="woocommerce-loop-product__title")
            name = name_tag.text.strip() if name_tag else "N/A"

            # Price
            price_tag = item.find("span", class_="woocommerce-Price-amount")
            price = price_tag.text.strip().replace("£", "").replace("$", "") if price_tag else "0"

            # Rating
            rating_tag = item.find("div", class_="star-rating")
            if rating_tag and rating_tag.get("aria-label"):
                rating_text = rating_tag["aria-label"]
                rating_value = float(rating_text.split()[1])
            else:
                rating_value = 0.0

            # Stock
            stock_tag = item.find("span", class_="stock")
            stock = stock_tag.text.strip() if stock_tag else "In Stock"

            # Product link
            link_tag = item.find("a")
            link = link_tag["href"] if link_tag else "https://scrapeme.live/shop/"

            # Product image
            img_tag = item.find("img")
            img_url = img_tag["src"] if img_tag else ""

            all_products.append({
                "Image": img_url,
                "Product Name": name,
                "Price ($)": float(price) if price.replace('.', '', 1).isdigit() else 0,
                "Rating": rating_value,
                "Stock Availability": stock,
                "Product Link": link
            })

    return pd.DataFrame(all_products)

# -------------------------------
# ⭐ Star Rating Generator
# -------------------------------
def get_stars(rating):
    filled = int(rating)
    empty = 5 - filled
    return '<span style="color:#FFD700;">' + '★' * filled + '</span>' + '<span style="color:#ccc;">' + '★' * empty + '</span>'

# -------------------------------
# 📊 Streamlit Dashboard
# -------------------------------
st.set_page_config(page_title="Scrapeme Product Table", page_icon="🛒", layout="wide")
st.title("🛒 Pokeshop Product Insights")
st.write("Explore product details scraped from [Scrapeme.live](https://scrapeme.live/shop/)!")

# Scrape data
data = scrape_scrapeme(pages=5)
data["Star Rating"] = data["Rating"].apply(get_stars)

# -------------------------------
# 🔍 Sidebar Sorting & Filtering
# -------------------------------
st.sidebar.header("🔎 Sort and Filter")

sort_option = st.sidebar.selectbox(
    "Sort by:",
    ["Sort by popularity", "Sort by average rating", "Sort by price: low to high", "Sort by price: high to low"]
)

if sort_option == "Sort by price: low to high":
    data = data.sort_values(by="Price ($)", ascending=True)
elif sort_option == "Sort by price: high to low":
    data = data.sort_values(by="Price ($)", ascending=False)
elif sort_option == "Sort by average rating":
    data = data.sort_values(by="Rating", ascending=False)
else:
    data = data.sample(frac=1, random_state=42)

# Filter by price
min_price, max_price = float(data["Price ($)"].min()), float(data["Price ($)"].max())
price_range = st.sidebar.slider("Select Price Range ($)", min_price, max_price, (min_price, max_price))
filtered_data = data[(data["Price ($)"] >= price_range[0]) & (data["Price ($)"] <= price_range[1])]

# -------------------------------
# 🧾 Display as Table with HTML
# -------------------------------
st.subheader(f"📋 Showing {len(filtered_data)} Products")

def make_clickable(link, name):
    return f'<a href="{link}" target="_blank">{name}</a>'

def make_image(url):
    return f'<img src="{url}" width="60">'

table_data = filtered_data.copy()
table_data["Product Name"] = table_data.apply(lambda x: make_clickable(x["Product Link"], x["Product Name"]), axis=1)
table_data["Image"] = table_data["Image"].apply(make_image)
table_data = table_data[["Image", "Product Name", "Price ($)", "Star Rating", "Stock Availability"]]

# Display as HTML table
st.write(table_data.to_html(escape=False, index=False), unsafe_allow_html=True)

# -------------------------------
# 📈 Chart
# -------------------------------
st.subheader("📈 Price Distribution")
st.bar_chart(filtered_data.set_index("Product Name")["Price ($)"])

# -------------------------------
# 📊 Summary
# -------------------------------
st.subheader("📊 Price Summary")
st.write(filtered_data["Price ($)"].describe())