import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Item, Offer, Favorite, User

app = FastAPI(title="Better Vinted API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilities to convert Mongo ObjectId to string

def serialize_doc(doc: dict):
    if not doc:
        return doc
    doc = {**doc}
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    # Convert datetime to isoformat
    for k, v in list(doc.items()):
        try:
            if hasattr(v, "isoformat"):
                doc[k] = v.isoformat()
        except Exception:
            pass
    return doc


@app.get("/")
def read_root():
    return {"message": "Better Vinted backend is running"}


# Public listings feed with filters
class FeedQuery(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None
    size: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    limit: int = 24


@app.post("/api/feed")
def get_feed(query: FeedQuery):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    filters = {}
    if query.category:
        filters["category"] = query.category
    if query.size:
        filters["size"] = query.size
    if query.brand:
        filters["brand"] = query.brand
    if query.color:
        filters["color"] = query.color
    if query.min_price is not None or query.max_price is not None:
        price_filter = {}
        if query.min_price is not None:
            price_filter["$gte"] = query.min_price
        if query.max_price is not None:
            price_filter["$lte"] = query.max_price
        filters["price"] = price_filter
    if query.q:
        filters["$or"] = [
            {"title": {"$regex": query.q, "$options": "i"}},
            {"description": {"$regex": query.q, "$options": "i"}},
            {"tags": {"$elemMatch": {"$regex": query.q, "$options": "i"}}},
        ]

    results = db["item"].find(filters).sort("created_at", -1).limit(query.limit)
    return [serialize_doc(d) for d in results]


# Create a new listing
@app.post("/api/items")
def create_item(item: Item):
    inserted_id = create_document("item", item)
    return {"id": inserted_id}


# Get item details
@app.get("/api/items/{item_id}")
def get_item(item_id: str):
    try:
        oid = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid item id")

    doc = db["item"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Item not found")
    return serialize_doc(doc)


# Favorite an item
class FavoriteIn(BaseModel):
    user_id: str


@app.post("/api/items/{item_id}/favorite")
def favorite_item(item_id: str, payload: FavoriteIn):
    # Prevent duplicate favorites
    existing = db["favorite"].find_one({"user_id": payload.user_id, "item_id": item_id})
    if existing:
        return {"status": "already_favorited"}
    create_document("favorite", Favorite(user_id=payload.user_id, item_id=item_id))
    return {"status": "ok"}


# Make an offer on an item
@app.post("/api/items/{item_id}/offers")
def make_offer(item_id: str, offer: Offer):
    if offer.item_id != item_id:
        # Ensure payload item_id matches path
        offer.item_id = item_id
    inserted_id = create_document("offer", offer)
    return {"id": inserted_id}


# List offers for an item
@app.get("/api/items/{item_id}/offers")
def list_offers(item_id: str):
    offers = db["offer"].find({"item_id": item_id}).sort("created_at", -1)
    return [serialize_doc(o) for o in offers]


# Lightweight health check for DB connectivity
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db as _db
        if _db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set"
            response["database_name"] = _db.name
            response["connection_status"] = "Connected"
            response["collections"] = _db.list_collection_names()[:10]
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
