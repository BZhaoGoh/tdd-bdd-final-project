# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
    def test_read_a_product(self):
        """It should Read a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        # Fetch it back
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)

    def test_update_a_product(self):
        """It should Update a Product"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
    # Change it an save it
        product.description = "testing"
        original_id = product.id
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "testing")
    # Fetch it back and make sure the id hasn't changed
    # but the data did change
        products = Product.all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].id, original_id)
        self.assertEqual(products[0].description, "testing")

    def test_update_product_with_empty_id(self):
        """It should Create a product without an ID"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
    # Attempt to update the product without an ID
        with self.assertRaises(DataValidationError) as context:
            product.update()
    # Assert that the correct exception was raised
        self.assertEqual(str(context.exception), "Update called with empty ID field")

    def test_delete_a_product(self):
        """It should Delete a Product"""
        product = ProductFactory()
        product.create()
        self.assertEqual(len(Product.all()), 1)
        # delete the product and make sure it isn't in the database
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """It should List all Products in the database"""
        products = Product.all()
        self.assertEqual(products, [])
        # Create 5 Products
        for _ in range(5):
            product = ProductFactory()
            product.create()
        # See if we get back 5 products
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_by_name(self):
        """It should Find a Product by Name"""
        products = ProductFactory.create_batch(5)
        for product in products:
            product.create()
        name = products[0].name
        count = len([product for product in products if product.name == name])
        found = Product.find_by_name(name)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.name, name)

    def test_find_by_availability(self):
        """It should Find Products by Availability"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        available = products[0].available
        count = len([product for product in products if product.available == available])
        found = Product.find_by_availability(available)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.available, available)

    def test_find_by_category(self):
        """It should Find Products by Category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_deserialize_with_valid_data(self):
        """Test With Valid Data"""
        # Prepare valid data
        valid_data = {
            "name": "Test Product",
            "description": "Test Description",
            "price": "10.0",
            "available": True,
            "category": Category.CLOTHS.name
        }
        # Create a Product instance
        product = Product()
        # Attempt to deserialize the valid data
        try:
            deserialized_product = product.deserialize(valid_data)
        except DataValidationError:
            self.fail("Deserialization should not raise an exception for valid data")

        # Assert that the deserialization was successful
        self.assertIsInstance(deserialized_product, Product)
        self.assertEqual(deserialized_product.name, "Test Product")
        self.assertEqual(deserialized_product.description, "Test Description")
        self.assertEqual(deserialized_product.price, Decimal("10.0"))
        self.assertEqual(deserialized_product.available, True)
        self.assertEqual(deserialized_product.category, Category.CLOTHS)

    def test_deserialize_with_invalid_data(self):
        """Prepare invalid data (missing "name" field)"""
        invalid_data = {
            "name": "name",
            "description": "Test Description",
            "price": "10.0",
            "available": "Not a boolean",
            "category": Category.CLOTHS.name
        }

        # Create a Product instance
        product = Product()

        # Attempt to deserialize the invalid data
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Assert that the correct exception was raised
        expected_error_message = "Invalid type for boolean [available]: <class 'str'>"
        self.assertEqual(str(context.exception), expected_error_message)

    def test_deserialize_with_type_error(self):
        """Prepare data with a Type Error"""
        invalid_data = {""}

        # Create a Product instance
        product = Product()

        # Attempt to deserialize the invalid data
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Assert that the correct exception was raised
        expected_error_message = "Invalid product: body of request contained bad or no data"
        self.assertIn(expected_error_message, str(context.exception))

    def test_deserialize_with_missing_name(self):
        """Prepare data with a missing attribute"""
        invalid_data = {
            "description": "Test Description",
            "price": "10.0",
            "available": True,
            "category": Category.CLOTHS.name
        }

        # Create a Product instance
        product = Product()

        # Attempt to deserialize the invalid data
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Assert that the correct exception was raised
        expected_error_message = "Invalid product: missing name"
        self.assertIn(expected_error_message, str(context.exception))

    def test_deserialize_with_missing_description(self):
        """Prepare data with a missing attribute"""
        invalid_data = {
            "name": "Test Description",
            "price": "10.0",
            "available": True,
            "category": Category.CLOTHS.name
        }

        # Create a Product instance
        product = Product()

        # Attempt to deserialize the invalid data
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Assert that the correct exception was raised
        expected_error_message = "Invalid product: missing description"
        self.assertIn(expected_error_message, str(context.exception))

    def test_deserialize_with_missing_price(self):
        """Prepare data with a missing attribute"""
        invalid_data = {
            "description": "Test Description",
            "name": "10.0",
            "available": True,
            "category": Category.CLOTHS.name
        }

        # Create a Product instance
        product = Product()

        # Attempt to deserialize the invalid data
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Assert that the correct exception was raised
        expected_error_message = "Invalid product: missing price"
        self.assertIn(expected_error_message, str(context.exception))

    def test_deserialize_with_missing_available(self):
        """Prepare data with a missing attribute"""
        invalid_data = {
            "description": "Test Description",
            "price": "10.0",
            "name": "True",
            "category": Category.CLOTHS.name
        }

        # Create a Product instance
        product = Product()

        # Attempt to deserialize the invalid data
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Assert that the correct exception was raised
        expected_error_message = "Invalid product: missing available"
        self.assertIn(expected_error_message, str(context.exception))

    def test_deserialize_with_missing_category(self):
        """Prepare data with a missing attribute"""
        invalid_data = {
            "description": "Test Description",
            "price": "10.0",
            "available": True,
            "name": "Category.CLOTHS.name"
        }

        # Create a Product instance
        product = Product()

        # Attempt to deserialize the invalid data
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Assert that the correct exception was raised
        expected_error_message = "Invalid product: missing category"
        self.assertIn(expected_error_message, str(context.exception))

    def test_deserialize_with_invalid_attribute(self):
        """Prepare data with a missing attribute"""
        invalid_data = {
            "name": "name",
            "description": "Test Description",
            "price": "10.0",
            "available": True,
            "category": "Category.CLOTHS.name"
        }

        # Create a Product instance
        product = Product()

        # Attempt to deserialize the invalid data
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Assert that the correct exception was raised
        expected_error_message = "Invalid attribute: Category.CLOTHS.name"
        self.assertIn(expected_error_message, str(context.exception))

    def test_deserialize_with_key_error(self):
        """Prepare data with a key error"""
        invalid_data = {
            "name": "name",
            "description": "Test Description",
            "price": "10.0",
            "available": True,
        }

        # Create a Product instance
        product = Product()

        # Attempt to deserialize the invalid data
        with self.assertRaises(DataValidationError) as context:
            product.deserialize(invalid_data)

        # Assert that the correct exception was raised
        expected_error_message = "Invalid product: missing category"
        self.assertIn(expected_error_message, str(context.exception))

    def test_find_by_price(self):
        """Create products with different prices"""
        product1 = Product(name="Product1", description="Description1", price=10.0, available=True, category=Category.CLOTHS)
        product2 = Product(name="Product2", description="Description2", price=20.0, available=True, category=Category.FOOD)

        # Add products to the database
        product1.create()
        product2.create()

        # Query products by price
        products_with_price_20 = Product.find_by_price(20.0).all()

        # Assert that the correct products are returned for a valid price
        self.assertEqual(len(products_with_price_20), 1)
        self.assertIn(product2, products_with_price_20)
