import pytest
from fastapi.testclient import TestClient
from app.schemas.product import ProductCreate

# Test data
test_product_data = {
    "name": "Test Product",
    "description": "Test Description",
    "price": 99.99,
    "stock": 100
}

def test_create_product(client: TestClient):
    """Tests product creation"""
    response = client.post("/products/", json=test_product_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == test_product_data["name"]
    assert data["description"] == test_product_data["description"]
    assert data["price"] == test_product_data["price"]
    assert data["stock"] == test_product_data["stock"]

def test_get_product(client: TestClient):
    """Tests getting a product by ID"""
    response = client.post("/products/", json=test_product_data)
    product_id = response.json()["id"]
    
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == test_product_data["name"]

def test_get_nonexistent_product(client: TestClient):
    """Tests getting a non-existent product"""
    response = client.get("/products/999")
    assert response.status_code == 404

def test_get_all_products(client: TestClient):
    """Tests getting all products"""
    client.post("/products/", json=test_product_data)
    client.post("/products/", json={
        "name": "Another Product",
        "description": "Another Description",
        "price": 199.99,
        "stock": 50
    })
    
    response = client.get("/products/")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_update_product(client: TestClient):
    """Tests updating a product"""
    response = client.post("/products/", json=test_product_data)
    product_id = response.json()["id"]
    
    update_data = {
        "name": "Updated Product",
        "description": "Updated Description",
        "price": 149.99,
        "stock": 75
    }
    
    response = client.put(f"/products/{product_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["price"] == update_data["price"]
    assert data["stock"] == update_data["stock"]

def test_update_nonexistent_product(client: TestClient):
    """Tests updating a non-existent product"""
    update_data = {"name": "This product does not exist"}
    response = client.put("/products/999", json=update_data)
    assert response.status_code == 404

def test_delete_product(client: TestClient):
    """Tests product deletion"""
    response = client.post("/products/", json=test_product_data)
    product_id = response.json()["id"]
    
    response = client.delete(f"/products/{product_id}")
    assert response.status_code == 204
    
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 404

def test_delete_nonexistent_product(client: TestClient):
    """Tests deleting a non-existent product"""
    response = client.delete("/products/999")
    assert response.status_code == 404

def test_delete_product_with_active_order(client: TestClient):
    """Tests that a product with an active order cannot be deleted"""
    product_response = client.post("/products/", json=test_product_data)
    product_id = product_response.json()["id"]

    order_data = {"items": [{"product_id": product_id, "quantity": 1}]}
    client.post("/orders/", json=order_data)

    delete_response = client.delete(f"/products/{product_id}")
    assert delete_response.status_code == 400
    assert "associated order items exist" in delete_response.text

def test_create_product_invalid_data(client: TestClient):
    """Tests creating a product with invalid data"""
    invalid_data = {
        "name": "Invalid Product",
        "description": "Invalid Description",
        "price": -99.99,
        "stock": 100
    }
    
    response = client.post("/products/", json=invalid_data)
    assert response.status_code == 422
