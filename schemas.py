"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

# Core user schema
class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

# Generic product example kept for reference
class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Marketplace specific schemas
class Item(BaseModel):
    """Second-hand listing items (like clothing, shoes, accessories). Collection name: "item""" 
    title: str = Field(..., description="Listing title")
    description: Optional[str] = Field(None, description="Listing description")
    price: float = Field(..., ge=0, description="Price in USD")
    category: str = Field(..., description="Category (e.g., Tops, Bottoms, Shoes)")
    size: Optional[str] = Field(None, description="Size (e.g., S, M, 42)")
    condition: Optional[str] = Field(None, description="Condition (New, Like New, Good, Fair)")
    brand: Optional[str] = Field(None, description="Brand name")
    color: Optional[str] = Field(None, description="Primary color")
    image_url: Optional[str] = Field(None, description="Main image URL")
    seller_id: Optional[str] = Field(None, description="User id of the seller")
    tags: Optional[List[str]] = Field(default_factory=list, description="Search tags")

class Favorite(BaseModel):
    """User favorites for quick access. Collection name: "favorite"""
    user_id: str = Field(..., description="User id")
    item_id: str = Field(..., description="Favorited item id")

class Offer(BaseModel):
    """Offers made by buyers to sellers. Collection name: "offer"""
    item_id: str = Field(..., description="Item id this offer is for")
    buyer_id: str = Field(..., description="User id of the buyer")
    amount: float = Field(..., ge=0, description="Offered amount")
    message: Optional[str] = Field(None, description="Optional message from buyer")
    status: str = Field("pending", description="Offer status: pending/accepted/declined")

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
