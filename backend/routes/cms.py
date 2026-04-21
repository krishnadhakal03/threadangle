from fastapi import APIRouter, Depends, HTTPException, Header, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Any, List
import os
import json
from datetime import datetime, timedelta

from database import get_db
from models import CMSContent
from schemas import CMSContentResponse, CMSContentUpdate

router = APIRouter()

# Simple in-memory cache: {page_name: (data, expiry_time)}
cms_cache: Dict[str, tuple] = {}
CACHE_EXPIRY_MINUTES = 10

def get_admin_auth(x_admin_password: str = Header(None)):
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not x_admin_password or x_admin_password != admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    return True

@router.get("/{page}")
async def get_cms_page(page: str = Path(...), db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    
    # Check cache
    if page in cms_cache:
        data, expiry = cms_cache[page]
        if now < expiry:
            return data

    result = await db.execute(select(CMSContent).where(CMSContent.page == page))
    contents = result.scalars().all()
    
    # Transform to key-value object
    response_data = {}
    for item in contents:
        val = item.content_value
        if item.content_type == "json":
            try:
                val = json.loads(val)
            except:
                pass
        elif item.content_type == "boolean":
            val = val.lower() == "true"
        elif item.content_type == "integer":
            try:
                val = int(val)
            except:
                pass
        response_data[item.content_key] = val
    
    # Update cache
    cms_cache[page] = (response_data, now + timedelta(minutes=CACHE_EXPIRY_MINUTES))
    
    return response_data

@router.get("/global")
async def get_cms_global(db: AsyncSession = Depends(get_db)):
    return await get_cms_page("global", db)

@router.put("/{page}/{content_key}")
async def update_cms_content(
    page: str, 
    content_key: str, 
    update_data: CMSContentUpdate,
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(get_admin_auth)
):
    result = await db.execute(
        select(CMSContent).where(CMSContent.page == page, CMSContent.content_key == content_key)
    )
    content = result.scalar_one_or_none()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content key not found")
        
    content.content_value = update_data.content_value
    await db.commit()
    
    # Clear cache for this page
    if page in cms_cache:
        del cms_cache[page]
        
    return {"message": "Content updated successfully"}

@router.get("/admin/all")
async def get_all_cms(
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(get_admin_auth)
):
    result = await db.execute(select(CMSContent).order_by(CMSContent.page, CMSContent.section))
    contents = result.scalars().all()
    
    grouped_data = {}
    for item in contents:
        if item.page not in grouped_data:
            grouped_data[item.page] = []
        grouped_data[item.page].append({
            "id": item.id,
            "section": item.section,
            "content_key": item.content_key,
            "content_value": item.content_value,
            "content_type": item.content_type,
            "label": item.label,
            "updated_at": item.updated_at
        })
    
    return grouped_data
