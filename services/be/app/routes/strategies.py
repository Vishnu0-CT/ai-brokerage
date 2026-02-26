"""
Strategy Routes

API endpoints for strategy CRUD, AI parsing, and templates.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.seed import DEFAULT_USER_ID
from app.services.strategy_service import StrategyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


def get_strategy_service(
    session: AsyncSession = Depends(get_session),
) -> StrategyService:
    return StrategyService(session)


# Request/Response models
class StrategyCreateRequest(BaseModel):
    name: str
    description: str | None = None
    entry_conditions: list[dict] | None = None
    exit_conditions: list[dict] | None = None
    stop_loss: dict | None = None
    target: dict | None = None
    position_size: dict | None = None
    max_positions: int = 1
    natural_language_input: str | None = None


class StrategyUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    entry_conditions: list[dict] | None = None
    exit_conditions: list[dict] | None = None
    stop_loss: dict | None = None
    target: dict | None = None
    position_size: dict | None = None
    max_positions: int | None = None
    natural_language_input: str | None = None


class StrategyParseRequest(BaseModel):
    description: str


@router.get("")
async def list_strategies(
    status: str | None = Query(None, description="Filter by status (active, paused, paper_trading)"),
    svc: StrategyService = Depends(get_strategy_service),
):
    """List all strategies for the user."""
    strategies = await svc.get_strategies(DEFAULT_USER_ID, status=status)
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "status": s.status,
            "entry_conditions": s.entry_conditions,
            "exit_conditions": s.exit_conditions,
            "stop_loss": s.stop_loss,
            "target": s.target,
            "position_size": s.position_size,
            "max_positions": s.max_positions,
            "paper_trading_stats": s.paper_trading_stats,
            "natural_language_input": s.natural_language_input,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in strategies
    ]


@router.post("")
async def create_strategy(
    body: StrategyCreateRequest,
    svc: StrategyService = Depends(get_strategy_service),
):
    """Create a new trading strategy."""
    strategy = await svc.create_strategy(
        user_id=DEFAULT_USER_ID,
        name=body.name,
        description=body.description,
        entry_conditions=body.entry_conditions,
        exit_conditions=body.exit_conditions,
        stop_loss=body.stop_loss,
        target=body.target,
        position_size=body.position_size,
        max_positions=body.max_positions,
        natural_language_input=body.natural_language_input,
    )
    
    return {
        "id": str(strategy.id),
        "name": strategy.name,
        "description": strategy.description,
        "status": strategy.status,
        "entry_conditions": strategy.entry_conditions,
        "exit_conditions": strategy.exit_conditions,
        "stop_loss": strategy.stop_loss,
        "target": strategy.target,
        "position_size": strategy.position_size,
        "max_positions": strategy.max_positions,
        "paper_trading_stats": strategy.paper_trading_stats,
        "natural_language_input": strategy.natural_language_input,
        "created_at": strategy.created_at.isoformat(),
        "updated_at": strategy.updated_at.isoformat(),
    }


@router.get("/templates")
async def get_templates(
    svc: StrategyService = Depends(get_strategy_service),
):
    """Get all strategy templates."""
    return svc.get_templates()


@router.get("/templates/categories")
async def get_template_categories(
    svc: StrategyService = Depends(get_strategy_service),
):
    """Get strategy templates organized by category."""
    return svc.get_template_categories()


@router.get("/templates/{template_id}")
async def get_template(
    template_id: str,
    svc: StrategyService = Depends(get_strategy_service),
):
    """Get a specific strategy template."""
    template = svc.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/parse")
async def parse_strategy(
    body: StrategyParseRequest,
    svc: StrategyService = Depends(get_strategy_service),
):
    """Parse natural language strategy description into structured format."""
    return await svc.parse_natural_language(body.description)


@router.get("/{strategy_id}")
async def get_strategy(
    strategy_id: uuid.UUID,
    svc: StrategyService = Depends(get_strategy_service),
):
    """Get a specific strategy by ID."""
    strategy = await svc.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return {
        "id": str(strategy.id),
        "name": strategy.name,
        "description": strategy.description,
        "status": strategy.status,
        "entry_conditions": strategy.entry_conditions,
        "exit_conditions": strategy.exit_conditions,
        "stop_loss": strategy.stop_loss,
        "target": strategy.target,
        "position_size": strategy.position_size,
        "max_positions": strategy.max_positions,
        "paper_trading_stats": strategy.paper_trading_stats,
        "natural_language_input": strategy.natural_language_input,
        "created_at": strategy.created_at.isoformat(),
        "updated_at": strategy.updated_at.isoformat(),
    }


@router.put("/{strategy_id}")
async def update_strategy(
    strategy_id: uuid.UUID,
    body: StrategyUpdateRequest,
    svc: StrategyService = Depends(get_strategy_service),
):
    """Update an existing strategy."""
    updates = body.model_dump(exclude_unset=True)
    strategy = await svc.update_strategy(strategy_id, **updates)
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    return {
        "id": str(strategy.id),
        "name": strategy.name,
        "description": strategy.description,
        "status": strategy.status,
        "entry_conditions": strategy.entry_conditions,
        "exit_conditions": strategy.exit_conditions,
        "stop_loss": strategy.stop_loss,
        "target": strategy.target,
        "position_size": strategy.position_size,
        "max_positions": strategy.max_positions,
        "paper_trading_stats": strategy.paper_trading_stats,
        "natural_language_input": strategy.natural_language_input,
        "created_at": strategy.created_at.isoformat(),
        "updated_at": strategy.updated_at.isoformat(),
    }


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: uuid.UUID,
    svc: StrategyService = Depends(get_strategy_service),
):
    """Delete a strategy."""
    success = await svc.delete_strategy(strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"success": True}


@router.get("/{strategy_id}/versions")
async def get_strategy_versions(
    strategy_id: uuid.UUID,
    svc: StrategyService = Depends(get_strategy_service),
):
    """Get version history for a strategy."""
    return await svc.get_strategy_versions(strategy_id)
