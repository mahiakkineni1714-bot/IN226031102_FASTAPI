from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

# Create FastAPI app
app = FastAPI()

# Sample Products Data


products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

feedback = []
orders = []

# Q1 Filter Products by Minimum Price

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


# Q2 Get Product Price

@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }

    return {"error": "Product not found"}

# Q3 Customer Feedback

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


# Q4 Product Summary Dashboard

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
        "most_expensive": {
            "name": expensive["name"],
            "price": expensive["price"]
        },
        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },
        "categories": categories
    }


# Q5 Bulk Order

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
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })

        elif not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock"
            })

        else:

            subtotal = product["price"] * item.quantity
            grand_total += subtotal

            confirmed.append({
                "product": product["name"],
                "qty": iem.quantity,
                "subtotal": subtotal
            })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }
    #assignment 3
     
    #  GET ALL PRODUCTS

@app.get("/products")
def get_products():
    return {
        "products": products,
        "total": len(products)
    }


# ADD NEW PRODUCT

class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True


@app.post("/products")
def add_product(data: NewProduct):

    # check duplicate product
    for p in products:
        if p["name"].lower() == data.name.lower():
            return {"error": "Product already exists"}

    new_id = max(p["id"] for p in products) + 1

    product = {
        "id": new_id,
        "name": data.name,
        "price": data.price,
        "category": data.category,
        "in_stock": data.in_stock
    }

    products.append(product)

    return {
        "message": "Product added",
        "product": product
    }


# GET PRODUCT BY ID

@app.get("/products/{product_id}")
def get_product(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return product

    return {"error": "Product not found"}



# UPDATE PRODUCT

@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    price: Optional[int] = None,
    in_stock: Optional[bool] = None
):

    for product in products:

        if product["id"] == product_id:

            if price is not None:
                product["price"] = price

            if in_stock is not None:
                product["in_stock"] = in_stock

            return {
                "message": "Product updated",
                "product": product
            }

    return {"error": "Product not found"}


# DELETE PRODUCT

@app.delete("/products/{product_id}")
def delete_product(product_id: int):

    for product in products:

        if product["id"] == product_id:

            products.remove(product)

            return {
                "message": f"Product '{product['name']}' deleted"
            }

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
        "most_expensive": {
            "name": priciest["name"],
            "price": priciest["price"]
        }
    }