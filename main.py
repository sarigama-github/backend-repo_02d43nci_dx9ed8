import os
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_job(doc: dict) -> dict:
    if not isinstance(doc, dict):
        return doc
    d = doc.copy()
    _id = d.pop("_id", None)
    if _id is not None:
        d["id"] = str(_id)
    return d


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/jobs")
def list_jobs(q: Optional[str] = None, location: Optional[str] = None):
    """Return a list of jobs. If database is configured, read from 'job' collection,
    otherwise return an empty list (so the frontend can load gracefully)."""
    items: List[dict] = []
    try:
        from database import db
        if db is not None:
            query = {}
            filters = []
            if q:
                # Simple regex match on title/company/description
                filters.append({"title": {"$regex": q, "$options": "i"}})
                filters.append({"company": {"$regex": q, "$options": "i"}})
                filters.append({"description": {"$regex": q, "$options": "i"}})
            if location:
                filters.append({"location": {"$regex": location, "$options": "i"}})
            if filters:
                query = {"$or": filters}
            docs = list(db["job"].find(query).limit(100))
            items = [serialize_job(d) for d in docs]
        else:
            items = []
    except Exception:
        # If any error (e.g., no DATABASE_URL), return empty list so UI still loads
        items = []
    return {"items": items}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
