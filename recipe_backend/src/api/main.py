from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.now(timezone.utc).isoformat()


class RecipeBase(BaseModel):
    """Common recipe fields used for create/update."""

    title: str = Field(..., min_length=1, max_length=120, description="Recipe title")
    description: str = Field(
        default="",
        max_length=500,
        description="Short description shown on recipe card",
    )
    ingredients: List[str] = Field(
        default_factory=list,
        description="List of ingredient lines (e.g., '2 eggs')",
    )
    steps: List[str] = Field(
        default_factory=list,
        description="List of step lines (e.g., 'Whisk eggs')",
    )
    color: str = Field(
        default="#3b82f6",
        description="Hex color used for the recipe card accent",
        pattern=r"^#([A-Fa-f0-9]{6})$",
    )


class RecipeCreate(RecipeBase):
    """Payload for creating a recipe."""


class RecipeUpdate(BaseModel):
    """Payload for updating a recipe (partial update allowed)."""

    title: Optional[str] = Field(
        default=None, min_length=1, max_length=120, description="Recipe title"
    )
    description: Optional[str] = Field(
        default=None, max_length=500, description="Short description"
    )
    ingredients: Optional[List[str]] = Field(
        default=None, description="List of ingredient lines"
    )
    steps: Optional[List[str]] = Field(default=None, description="List of step lines")
    color: Optional[str] = Field(
        default=None,
        description="Hex color used for the recipe card accent",
        pattern=r"^#([A-Fa-f0-9]{6})$",
    )


class Recipe(RecipeBase):
    """Full recipe record stored in memory."""

    id: int = Field(..., description="Recipe identifier")
    created_at: str = Field(..., description="ISO timestamp when created")
    updated_at: str = Field(..., description="ISO timestamp when last updated")


openapi_tags = [
    {"name": "Health", "description": "Service health and basic info endpoints."},
    {"name": "Recipes", "description": "In-memory recipe CRUD for the current server session."},
]

app = FastAPI(
    title="Colorful Recipe Manager API",
    description=(
        "A simple in-memory recipe manager. Data is stored in server memory only (no persistence). "
        "Ideal for demo and single-session usage."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# CORS for local dev and hosted frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo simplicity; tighten in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (per server process lifetime)
_RECIPES: Dict[int, Recipe] = {}
_NEXT_ID: int = 1


# PUBLIC_INTERFACE
@app.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Returns a simple healthy message used for uptime checks.",
)
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/recipes",
    response_model=List[Recipe],
    tags=["Recipes"],
    summary="List recipes",
    description="Return all recipes currently stored in server memory.",
)
def list_recipes():
    """List all recipes."""
    # Return deterministic ordering by id.
    return [_RECIPES[k] for k in sorted(_RECIPES.keys())]


# PUBLIC_INTERFACE
@app.post(
    "/recipes",
    response_model=Recipe,
    tags=["Recipes"],
    summary="Create a recipe",
    description="Create a new recipe and store it in memory.",
)
def create_recipe(payload: RecipeCreate):
    """Create a recipe in memory."""
    global _NEXT_ID  # noqa: PLW0603 - simple in-memory counter

    recipe_id = _NEXT_ID
    _NEXT_ID += 1

    now = _utc_now_iso()
    recipe = Recipe(
        id=recipe_id,
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    _RECIPES[recipe_id] = recipe
    return recipe


# PUBLIC_INTERFACE
@app.get(
    "/recipes/{recipe_id}",
    response_model=Recipe,
    tags=["Recipes"],
    summary="Get a recipe",
    description="Fetch a single recipe by id.",
)
def get_recipe(
    recipe_id: int = Path(..., ge=1, description="Recipe identifier"),
):
    """Get a single recipe by id."""
    recipe = _RECIPES.get(recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


# PUBLIC_INTERFACE
@app.put(
    "/recipes/{recipe_id}",
    response_model=Recipe,
    tags=["Recipes"],
    summary="Update a recipe",
    description="Update an existing recipe (partial update supported).",
)
def update_recipe(
    payload: RecipeUpdate,
    recipe_id: int = Path(..., ge=1, description="Recipe identifier"),
):
    """Update a recipe by id (partial update)."""
    existing = _RECIPES.get(recipe_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    updated_data = existing.model_dump()
    patch = payload.model_dump(exclude_unset=True)
    updated_data.update(patch)
    updated_data["updated_at"] = _utc_now_iso()

    updated = Recipe(**updated_data)
    _RECIPES[recipe_id] = updated
    return updated


# PUBLIC_INTERFACE
@app.delete(
    "/recipes/{recipe_id}",
    tags=["Recipes"],
    summary="Delete a recipe",
    description="Delete a recipe by id.",
)
def delete_recipe(
    recipe_id: int = Path(..., ge=1, description="Recipe identifier"),
):
    """Delete a recipe by id."""
    if recipe_id not in _RECIPES:
        raise HTTPException(status_code=404, detail="Recipe not found")
    del _RECIPES[recipe_id]
    return {"deleted": True, "id": recipe_id}
