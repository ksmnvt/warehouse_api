import pytest
from fastapi.testclient import TestClient

def test_create_order(client: TestClient):
    """Tests order creation"""
    product_data = {
        "name": "Test Product",
        "description": "Test Description",
        "price": 99.99,
        "stock": 100
    }
    response = client.post("/products/", json=product_data)
    product_id = response.json()["id"]
    
    order_data = {"items": [{"product_id": product_id, "quantity": 2}]}
    
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert len(data["items"]) == 1
    assert data["items"][0]["product"]["id"] == product_id
    assert data["items"][0]["price"] == product_data["price"]
    assert data["order_total"] == product_data["price"] * order_data["items"][0]["quantity"]

def test_get_order(client: TestClient):
    """Tests getting an order by ID"""
    product_data = {
        "name": "Test Product",
        "description": "Test Description",
        "price": 99.99,
        "stock": 100
    }
    response = client.post("/products/", json=product_data)
    product_id = response.json()["id"]
    
    order_data = {"items": [{"product_id": product_id, "quantity": 2}]}
    response = client.post("/orders/", json=order_data)
    order_id = response.json()["id"]
    
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert len(data["items"]) == 1

def test_get_nonexistent_order(client: TestClient):
    """Tests getting a non-existent order"""
    response = client.get("/orders/999")
    assert response.status_code == 404

def test_get_all_orders(client: TestClient):
    """Tests getting all orders"""
    product_data = {
        "name": "Test Product",
        "description": "Test Description",
        "price": 99.99,
        "stock": 100
    }
    response = client.post("/products/", json=product_data)
    product_id = response.json()["id"]
    
    order_data = {"items": [{"product_id": product_id, "quantity": 2}]}
    client.post("/orders/", json=order_data)
    client.post("/orders/", json=order_data)
    
    response = client.get("/orders/")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_update_order_status(client: TestClient):
    """Tests updating order status"""
    product_data = {
        "name": "Test Product",
        "description": "Test Description",
        "price": 99.99,
        "stock": 100
    }
    response = client.post("/products/", json=product_data)
    product_id = response.json()["id"]
    
    order_data = {"items": [{"product_id": product_id, "quantity": 2}]}
    response = client.post("/orders/", json=order_data)
    order_id = response.json()["id"]
    
    response = client.put(f"/orders/{order_id}/status?status_value=confirmed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"

def test_delete_order(client: TestClient):
    """Tests order deletion"""
    product_data = {
        "name": "Test Product",
        "description": "Test Description",
        "price": 99.99,
        "stock": 100
    }
    response = client.post("/products/", json=product_data)
    product_id = response.json()["id"]
    
    order_data = {"items": [{"product_id": product_id, "quantity": 2}]}
    response = client.post("/orders/", json=order_data)
    order_id = response.json()["id"]
    
    response = client.delete(f"/orders/{order_id}")
    assert response.status_code == 204
    
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 404

def test_create_order_insufficient_stock(client: TestClient):
    """Tests creating an order with insufficient stock"""
    product_data = {
        "name": "Test Product",
        "description": "Test Description",
        "price": 99.99,
        "stock": 1
    }
    response = client.post("/products/", json=product_data)
    product_id = response.json()["id"]
    
    order_data = {"items": [{"product_id": product_id, "quantity": 10}]}
    
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 400
    assert "Not enough stock" in response.text

def test_create_order_with_nonexistent_product(client: TestClient):
    """Tests creating an order with a non-existent product"""
    order_data = {"items": [{"product_id": 999, "quantity": 1}]}
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 404
    assert "Product with id 999 not found" in response.text

def test_create_order_with_empty_items_list(client: TestClient):
    """Tests creating an order with an empty items list"""
    order_data = {"items": []}
    response = client.post("/orders/", json=order_data)
    assert response.status_code == 400
    assert "Order must contain at least one item" in response.text

def test_create_order_with_duplicate_products(client: TestClient):
    """Tests creating an order with duplicate products in the items list"""
    product_data = {"name": "Test Product", "description": "Test Description", "price": 10.0, "stock": 10}
    product_response = client.post("/products/", json=product_data)
    product_id = product_response.json()["id"]

    order_data = {
        "items": [
            {"product_id": product_id, "quantity": 1},
            {"product_id": product_id, "quantity": 2}
        ]
    }

    response = client.post("/orders/", json=order_data)
    assert response.status_code == 201
    order = response.json()
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 3
    assert order["order_total"] == 30.0

def test_order_price_is_immutable(client: TestClient):
    """Tests that the price of an order item is not affected by product price changes"""
    original_price = 100.0
    product_data = {"name": "Test Product", "description": "Test Description", "price": original_price, "stock": 10}
    product_response = client.post("/products/", json=product_data)
    product_id = product_response.json()["id"]

    order_data = {"items": [{"product_id": product_id, "quantity": 1}]}
    order_response = client.post("/orders/", json=order_data)
    order_id = order_response.json()["id"]

    # Update the product price
    new_price = 150.0
    client.put(f"/products/{product_id}", json={"price": new_price})

    # Verify that the order's price has not changed
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    order = response.json()
    assert order["items"][0]["price"] == original_price
    assert order["order_total"] == original_price
