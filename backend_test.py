#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Construction Materials Marketplace
Testing all APIs for the Saudi construction materials platform
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://welcome-msg-84.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class ConstructionMaterialsAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.customer_token = None
        self.supplier_token = None
        self.customer_id = None
        self.supplier_id = None
        self.product_id = None
        self.order_id = None
        self.conversation_id = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {details}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, auth_token: str = None) -> tuple:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}"
                
            return True, response
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"
    
    def test_customer_registration(self):
        """Test customer account registration"""
        customer_data = {
            "email": "ahmed.customer@example.com",
            "password": "SecurePass123!",
            "full_name": "أحمد محمد العتيبي",
            "phone": "+966501234567",
            "role": "customer",
            "delivery_address": "حي الملك فهد، الرياض، المملكة العربية السعودية",
            "city": "الرياض"
        }
        
        success, response = self.make_request("POST", "/auth/register", customer_data)
        
        if not success:
            self.log_test("Customer Registration", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.customer_token = data["access_token"]
                self.customer_id = data["user"]["id"]
                self.log_test("Customer Registration", True, "Customer registered successfully", data["user"])
                return True
            else:
                self.log_test("Customer Registration", False, "Missing token or user data in response")
                return False
        else:
            self.log_test("Customer Registration", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_supplier_registration(self):
        """Test supplier account registration"""
        supplier_data = {
            "email": "supplier.alwatan@example.com",
            "password": "SupplierPass123!",
            "full_name": "محمد عبدالله الشمري",
            "phone": "+966502345678",
            "role": "supplier",
            "company_name": "شركة الوطن لمواد البناء",
            "commercial_registration": "1010123456",
            "tax_number": "300123456789003",
            "business_description": "متخصصون في توريد جميع أنواع مواد البناء والتشييد بأعلى جودة وأفضل الأسعار",
            "categories": ["concrete", "rebar", "blocks", "sand"],
            "location": {"lat": 24.7136, "lng": 46.6753},
            "city": "الرياض"
        }
        
        success, response = self.make_request("POST", "/auth/register", supplier_data)
        
        if not success:
            self.log_test("Supplier Registration", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.supplier_token = data["access_token"]
                self.supplier_id = data["user"]["id"]
                self.log_test("Supplier Registration", True, "Supplier registered successfully", data["user"])
                return True
            else:
                self.log_test("Supplier Registration", False, "Missing token or user data in response")
                return False
        else:
            self.log_test("Supplier Registration", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_customer_login(self):
        """Test customer login"""
        login_data = {
            "email": "ahmed.customer@example.com",
            "password": "SecurePass123!"
        }
        
        success, response = self.make_request("POST", "/auth/login", login_data)
        
        if not success:
            self.log_test("Customer Login", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.log_test("Customer Login", True, "Customer login successful")
                return True
            else:
                self.log_test("Customer Login", False, "Missing access token in response")
                return False
        else:
            self.log_test("Customer Login", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_supplier_login(self):
        """Test supplier login"""
        login_data = {
            "email": "supplier.alwatan@example.com",
            "password": "SupplierPass123!"
        }
        
        success, response = self.make_request("POST", "/auth/login", login_data)
        
        if not success:
            self.log_test("Supplier Login", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.log_test("Supplier Login", True, "Supplier login successful")
                return True
            else:
                self.log_test("Supplier Login", False, "Missing access token in response")
                return False
        else:
            self.log_test("Supplier Login", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_get_categories(self):
        """Test getting construction material categories"""
        success, response = self.make_request("GET", "/categories")
        
        if not success:
            self.log_test("Get Categories", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "categories" in data and len(data["categories"]) > 0:
                categories_count = len(data["categories"])
                self.log_test("Get Categories", True, f"Retrieved {categories_count} categories successfully")
                return True
            else:
                self.log_test("Get Categories", False, "No categories found in response")
                return False
        else:
            self.log_test("Get Categories", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_create_product(self):
        """Test creating a new product (supplier only)"""
        if not self.supplier_token:
            self.log_test("Create Product", False, "No supplier token available")
            return False
            
        product_data = {
            "name": "خرسانة جاهزة عالية الجودة - درجة 350",
            "description": "خرسانة جاهزة عالية الجودة مقاومة 350 كجم/سم² مناسبة لجميع أعمال البناء والتشييد. تتميز بالقوة والمتانة وسهولة الصب.",
            "category": "concrete",
            "price": 280.0,
            "unit": "متر مكعب",
            "minimum_order": 5,
            "available_quantity": 1000,
            "images": [
                "https://example.com/concrete1.jpg",
                "https://example.com/concrete2.jpg"
            ],
            "specifications": {
                "مقاومة_الضغط": "350 كجم/سم²",
                "نوع_الاسمنت": "اسمنت بورتلاندي عادي",
                "حجم_الحصى": "20 مم",
                "نسبة_الماء_الاسمنت": "0.45",
                "زمن_الشك": "45 دقيقة"
            },
            "keywords": ["خرسانة", "جاهزة", "عالية الجودة", "350", "بناء", "تشييد"]
        }
        
        success, response = self.make_request("POST", "/products", product_data, self.supplier_token)
        
        if not success:
            self.log_test("Create Product", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                self.product_id = data["id"]
                self.log_test("Create Product", True, f"Product created successfully with ID: {self.product_id}")
                return True
            else:
                self.log_test("Create Product", False, "Missing product ID in response")
                return False
        else:
            self.log_test("Create Product", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_search_and_filter_products(self):
        """Test product search and filtering"""
        # Test 1: Search by category
        success, response = self.make_request("GET", "/products", {"category": "concrete"})
        
        if not success:
            self.log_test("Search Products by Category", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                self.log_test("Search Products by Category", True, f"Found {len(data)} concrete products")
            else:
                self.log_test("Search Products by Category", False, "Invalid response format")
                return False
        else:
            self.log_test("Search Products by Category", False, f"HTTP {response.status_code}: {response.text}")
            return False
        
        # Test 2: Search by text
        success, response = self.make_request("GET", "/products", {"search": "خرسانة"})
        
        if not success:
            self.log_test("Search Products by Text", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                self.log_test("Search Products by Text", True, f"Found {len(data)} products matching 'خرسانة'")
            else:
                self.log_test("Search Products by Text", False, "Invalid response format")
                return False
        else:
            self.log_test("Search Products by Text", False, f"HTTP {response.status_code}: {response.text}")
            return False
        
        # Test 3: Filter by price range
        success, response = self.make_request("GET", "/products", {"min_price": 100, "max_price": 500})
        
        if not success:
            self.log_test("Filter Products by Price", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                self.log_test("Filter Products by Price", True, f"Found {len(data)} products in price range 100-500")
                return True
            else:
                self.log_test("Filter Products by Price", False, "Invalid response format")
                return False
        else:
            self.log_test("Filter Products by Price", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_add_to_cart(self):
        """Test adding product to cart (customer only)"""
        if not self.customer_token or not self.product_id:
            self.log_test("Add to Cart", False, "Missing customer token or product ID")
            return False
            
        success, response = self.make_request("POST", f"/cart/add?product_id={self.product_id}&quantity=10", auth_token=self.customer_token)
        
        if not success:
            self.log_test("Add to Cart", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                self.log_test("Add to Cart", True, "Product added to cart successfully")
                return True
            else:
                self.log_test("Add to Cart", False, "Missing success message in response")
                return False
        else:
            self.log_test("Add to Cart", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_get_cart(self):
        """Test getting cart contents"""
        if not self.customer_token:
            self.log_test("Get Cart", False, "No customer token available")
            return False
            
        success, response = self.make_request("GET", "/cart", auth_token=self.customer_token)
        
        if not success:
            self.log_test("Get Cart", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                items_count = len(data["items"])
                self.log_test("Get Cart", True, f"Retrieved cart with {items_count} items")
                return True
            else:
                self.log_test("Get Cart", False, "Missing items in cart response")
                return False
        else:
            self.log_test("Get Cart", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_create_order(self):
        """Test creating a new order (customer only)"""
        if not self.customer_token or not self.supplier_id or not self.product_id:
            self.log_test("Create Order", False, "Missing required data (customer token, supplier ID, or product ID)")
            return False
            
        order_data = {
            "supplier_id": self.supplier_id,
            "items": [
                {
                    "product_id": self.product_id,
                    "quantity": 10,
                    "price": 280.0,
                    "name": "خرسانة جاهزة عالية الجودة - درجة 350"
                }
            ],
            "delivery_address": "حي الملك فهد، الرياض، المملكة العربية السعودية",
            "delivery_notes": "يرجى التنسيق قبل التسليم بـ 24 ساعة"
        }
        
        success, response = self.make_request("POST", "/orders", order_data, self.customer_token)
        
        if not success:
            self.log_test("Create Order", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                self.order_id = data["id"]
                total_amount = data.get("total_amount", 0)
                self.log_test("Create Order", True, f"Order created successfully with ID: {self.order_id}, Total: {total_amount} SAR")
                return True
            else:
                self.log_test("Create Order", False, "Missing order ID in response")
                return False
        else:
            self.log_test("Create Order", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_update_order_status(self):
        """Test updating order status (supplier only)"""
        if not self.supplier_token or not self.order_id:
            self.log_test("Update Order Status", False, "Missing supplier token or order ID")
            return False
            
        success, response = self.make_request("PUT", f"/orders/{self.order_id}/status?status=confirmed", auth_token=self.supplier_token)
        
        if not success:
            self.log_test("Update Order Status", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                self.log_test("Update Order Status", True, "Order status updated to confirmed")
                return True
            else:
                self.log_test("Update Order Status", False, "Missing success message in response")
                return False
        else:
            self.log_test("Update Order Status", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_send_chat_message(self):
        """Test sending chat message"""
        if not self.customer_token or not self.supplier_id:
            self.log_test("Send Chat Message", False, "Missing customer token or supplier ID")
            return False
            
        message_data = {
            "receiver_id": self.supplier_id,
            "message_type": "text",
            "content": "السلام عليكم، أريد الاستفسار عن توفر خرسانة جاهزة بكمية 50 متر مكعب"
        }
        
        success, response = self.make_request("POST", "/chat/send", message_data, self.customer_token)
        
        if not success:
            self.log_test("Send Chat Message", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "id" in data and "conversation_id" in data:
                self.conversation_id = data["conversation_id"]
                self.log_test("Send Chat Message", True, f"Message sent successfully, Conversation ID: {self.conversation_id}")
                return True
            else:
                self.log_test("Send Chat Message", False, "Missing message ID or conversation ID in response")
                return False
        else:
            self.log_test("Send Chat Message", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_get_conversations(self):
        """Test getting chat conversations"""
        if not self.customer_token:
            self.log_test("Get Conversations", False, "No customer token available")
            return False
            
        success, response = self.make_request("GET", "/chat/conversations", auth_token=self.customer_token)
        
        if not success:
            self.log_test("Get Conversations", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "conversations" in data:
                conversations_count = len(data["conversations"])
                self.log_test("Get Conversations", True, f"Retrieved {conversations_count} conversations")
                return True
            else:
                self.log_test("Get Conversations", False, "Missing conversations in response")
                return False
        else:
            self.log_test("Get Conversations", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_create_review(self):
        """Test creating product/supplier review"""
        if not self.customer_token or not self.order_id:
            self.log_test("Create Review", False, "Missing customer token or order ID")
            return False
            
        review_data = {
            "product_id": self.product_id,
            "supplier_id": self.supplier_id,
            "order_id": self.order_id,
            "rating": 5,
            "comment": "منتج ممتاز وجودة عالية، التسليم في الوقت المحدد والتعامل احترافي جداً. أنصح بالتعامل مع هذا المورد."
        }
        
        success, response = self.make_request("POST", "/reviews", review_data, self.customer_token)
        
        if not success:
            self.log_test("Create Review", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "id" in data and "rating" in data:
                self.log_test("Create Review", True, f"Review created successfully with rating: {data['rating']}/5")
                return True
            else:
                self.log_test("Create Review", False, "Missing review ID or rating in response")
                return False
        else:
            self.log_test("Create Review", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_customer_dashboard_stats(self):
        """Test customer dashboard statistics"""
        if not self.customer_token:
            self.log_test("Customer Dashboard Stats", False, "No customer token available")
            return False
            
        success, response = self.make_request("GET", "/dashboard/stats", auth_token=self.customer_token)
        
        if not success:
            self.log_test("Customer Dashboard Stats", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            expected_fields = ["total_orders", "pending_orders", "cart_items"]
            if all(field in data for field in expected_fields):
                self.log_test("Customer Dashboard Stats", True, f"Stats: {data['total_orders']} orders, {data['pending_orders']} pending, {data['cart_items']} cart items")
                return True
            else:
                self.log_test("Customer Dashboard Stats", False, "Missing required fields in dashboard stats")
                return False
        else:
            self.log_test("Customer Dashboard Stats", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def test_supplier_dashboard_stats(self):
        """Test supplier dashboard statistics"""
        if not self.supplier_token:
            self.log_test("Supplier Dashboard Stats", False, "No supplier token available")
            return False
            
        success, response = self.make_request("GET", "/dashboard/stats", auth_token=self.supplier_token)
        
        if not success:
            self.log_test("Supplier Dashboard Stats", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            expected_fields = ["total_products", "total_orders", "pending_orders", "total_revenue"]
            if all(field in data for field in expected_fields):
                self.log_test("Supplier Dashboard Stats", True, f"Stats: {data['total_products']} products, {data['total_orders']} orders, Revenue: {data['total_revenue']} SAR")
                return True
            else:
                self.log_test("Supplier Dashboard Stats", False, "Missing required fields in dashboard stats")
                return False
        else:
            self.log_test("Supplier Dashboard Stats", False, f"HTTP {response.status_code}: {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting Comprehensive Backend API Testing for Construction Materials Marketplace")
        print("=" * 80)
        
        # Authentication Tests
        print("\n📝 AUTHENTICATION TESTS")
        print("-" * 40)
        self.test_customer_registration()
        self.test_supplier_registration()
        self.test_customer_login()
        self.test_supplier_login()
        
        # Core API Tests
        print("\n🏗️ CORE API TESTS")
        print("-" * 40)
        self.test_get_categories()
        self.test_create_product()
        self.test_search_and_filter_products()
        
        # Cart and Orders Tests
        print("\n🛒 CART & ORDERS TESTS")
        print("-" * 40)
        self.test_add_to_cart()
        self.test_get_cart()
        self.test_create_order()
        self.test_update_order_status()
        
        # Communication Tests
        print("\n💬 COMMUNICATION TESTS")
        print("-" * 40)
        self.test_send_chat_message()
        self.test_get_conversations()
        self.test_create_review()
        
        # Dashboard Tests
        print("\n📊 DASHBOARD TESTS")
        print("-" * 40)
        self.test_customer_dashboard_stats()
        self.test_supplier_dashboard_stats()
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        return passed_tests, failed_tests, self.test_results

def main():
    """Main function to run all tests"""
    tester = ConstructionMaterialsAPITester()
    passed, failed, results = tester.run_all_tests()
    
    # Save detailed results to file
    with open("/app/test_results_detailed.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: /app/test_results_detailed.json")
    
    # Return exit code based on test results
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())