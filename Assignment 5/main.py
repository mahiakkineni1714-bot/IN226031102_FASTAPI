from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

feedback = []
orders = []

# ── ASSIGNMENT 2 ──────────────────────────────────────────

@app.get("/products/filter")
def filter_products(
    category: Optional[str] = None,
    max_price: Optional[int] = None,
    min_price: Optional[int] = None
):
    result = products
    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]
    if max_price:
        result = [p for p in result if p["price"] <= max_price]
    if min_price:
        result = [p for p in result if p["price"] >= min_price]
    return result


@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return {"name": product["name"], "price": product["price"]}
    return {"error": "Product not found"}


class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):
    feedback.append(data.dict())
    return {
        "message": "Feedback submitted successfully",
        "feedback": data.dict(),
        "total_feedback": len(feedback)
    }


@app.get("/products/summary")
def product_summary():
    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]
    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])
    categories = list(set(p["category"] for p in products))
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock),
        "out_of_stock_count": len(out_stock),
        "most_expensive": {"name": expensive["name"], "price": expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": categories
    }


class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):
    confirmed = []
    failed = []
    grand_total = 0
    for item in order.items:
        product = next((p for p in products if p["id"] == item.product_id), None)
        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})
        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})
        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal
            confirmed.append({"product": product["name"], "qty": item.quantity, "subtotal": subtotal})
    return {"company": order.company_name, "confirmed": confirmed, "failed": failed, "grand_total": grand_total}


# ── ASSIGNMENT 3 ──────────────────────────────────────────

@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}


class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

@app.post("/products")
def add_product(data: NewProduct):
    for p in products:
        if p["name"].lower() == data.name.lower():
            return {"error": "Product already exists"}
    new_id = max(p["id"] for p in products) + 1
    product = {"id": new_id, "name": data.name, "price": data.price, "category": data.category, "in_stock": data.in_stock}
    products.append(product)
    return {"message": "Product added", "product": product}


@app.put("/products/{product_id}")
def update_product(product_id: int, price: Optional[int] = None, in_stock: Optional[bool] = None):
    for product in products:
        if product["id"] == product_id:
            if price is not None:
                product["price"] = price
            if in_stock is not None:
                product["in_stock"] = in_stock
            return {"message": "Product updated", "product": product}
    return {"error": "Product not found"}


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return {"message": f"Product '{product['name']}' deleted"}
    return {"error": "Product not found"}


# ── ASSIGNMENT 5 — NEW ENDPOINTS ──────────────────────────

# Q1 — Search Products
@app.get("/products/search")
def search_products(keyword: str = Query(...)):
    result = [p for p in products if keyword.lower() in p["name"].lower()]
    if not result:
        return {"message": f"No products found for: {keyword}"}
    return {"keyword": keyword, "total_found": len(result), "products": result}


# Q2 — Sort Products
@app.get("/products/sort")
def sort_products(sort_by: str = Query("price"), order: str = Query("asc")):
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}
    result = sorted(products, key=lambda p: p[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "products": result}


# Q3 — Paginate Products
@app.get("/products/page")
def get_products_paged(page: int = Query(1, ge=1), limit: int = Query(2, ge=1, le=20)):
    start = (page - 1) * limit
    return {
        "page": page, "limit": limit,
        "total_pages": -(-len(products) // limit),
        "products": products[start: start + limit]
    }


# Q4 — Search Orders
@app.get("/orders/search")
def search_orders(customer_name: str = Query(...)):
    results = [o for o in orders if customer_name.lower() in o["customer_name"].lower()]
    if not results:
        return {"message": f"No orders found for: {customer_name}"}
    return {"customer_name": customer_name, "total_found": len(results), "orders": results}


# Q5 — Sort by Category then Price
@app.get("/products/sort-by-category")
def sort_by_category():
    result = sorted(products, key=lambda p: (p["category"], p["price"]))
    return {"products": result, "total": len(result)}


# Q6 — Browse (Search + Sort + Paginate combined)
@app.get("/products/browse")
def browse_products(
    keyword: str = Query(None),
    sort_by: str = Query("price"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1, le=20),
):
    result = products
    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]
    if sort_by in ["price", "name"]:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))
    total = len(result)
    start = (page - 1) * limit
    return {
        "keyword": keyword, "sort_by": sort_by, "order": order,
        "page": page, "limit": limit, "total_found": total,
        "total_pages": -(-total // limit),
        "products": result[start: start + limit],
    }


# BONUS — Paginate Orders
@app.get("/orders/page")
def get_orders_paged(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=20)):
    start = (page - 1) * limit
    return {
        "page": page, "limit": limit,
        "total": len(orders),
        "total_pages": -(-len(orders) // limit),
        "orders": orders[start: start + limit],
    }


# ── TASK 5 ────────────────────────────────────────────────

class Order(BaseModel):
    customer_name: str
    product_id: int

@app.post("/orders")
def create_order(order: Order):
    new_order = {
        "order_id": len(orders) + 1,
        "customer_name": order.customer_name,
        "product_id": order.product_id
    }
    orders.append(new_order)
    return {"message": "Order created successfully", "order": new_order}


# ── ASSIGNMENT 3 EXTRAS ───────────────────────────────────

# GET PRODUCT BY ID
@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product
    return {"error": "Product not found"}


# PRODUCT AUDIT
@app.get("/products/audit")
def product_audit():
    in_stock_list = [p for p in products if p["in_stock"]]
    out_stock_list = [p for p in products if not p["in_stock"]]
    stock_value = sum(p["price"] * 10 for p in in_stock_list)
    priciest = max(products, key=lambda p: p["price"])
    return {
        "total_products": len(products),
        "in_stock_count": len(in_stock_list),
        "out_of_stock_names": [p["name"] for p in out_stock_list],
        "total_stock_value": stock_value,
        "most_expensive": {"name": priciest["name"], "price": priciest["price"]}
    }