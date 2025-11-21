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
