from fastapi import APIRouter, Depends, HTTPException, Header, Query, Path, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc
from typing import List, Optional
import os
from datetime import datetime

from database import get_db
from models import BlogPost, BlogCategory
from schemas import BlogPostResponse, BlogPostList, BlogCategoryResponse, BlogPostCreate, BlogPostUpdate

router = APIRouter()

def get_admin_auth(x_admin_password: str = Header(None)):
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not x_admin_password or x_admin_password != admin_password:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    return True

# Public Endpoints
@router.get("/posts", response_model=List[BlogPostList])
async def list_posts(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(10),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    query = select(BlogPost).where(BlogPost.status == "published").order_by(desc(BlogPost.published_at))
    
    if category:
        query = query.where(BlogPost.category == category)
    if tag:
        query = query.where(BlogPost.tags.like(f"%{tag}%"))
    
    result = await db.execute(query.limit(limit).offset(offset))
    return result.scalars().all()

@router.get("/posts/{slug}", response_model=BlogPostResponse)
async def get_post(slug: str = Path(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Increment views
    post.views += 1
    await db.commit()
    await db.refresh(post)
    
    return post

@router.get("/posts/{slug}/related", response_model=List[BlogPostList])
async def get_related_posts(slug: str, db: AsyncSession = Depends(get_db)):
    # Get current post's category
    result = await db.execute(select(BlogPost.category).where(BlogPost.slug == slug))
    category = result.scalar_one_or_none()
    
    if not category:
        return []
        
    # Find other posts in same category
    query = select(BlogPost).where(
        BlogPost.category == category, 
        BlogPost.slug != slug,
        BlogPost.status == "published"
    ).limit(3)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/categories", response_model=List[BlogCategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    # Get categories with live post counts
    cats_result = await db.execute(select(BlogCategory).order_by(BlogCategory.name))
    cats = cats_result.scalars().all()

    # Count published posts per category
    counts_result = await db.execute(
        select(BlogPost.category, func.count(BlogPost.id).label("cnt"))
        .where(BlogPost.status == "published")
        .group_by(BlogPost.category)
    )
    counts = {row.category: row.cnt for row in counts_result}

    # Inject live counts
    for cat in cats:
        cat.post_count = counts.get(cat.name, 0)

    return cats

@router.get("/featured", response_model=List[BlogPostList])
async def get_featured_posts(db: AsyncSession = Depends(get_db)):
    # 3 most viewed published posts
    query = select(BlogPost).where(BlogPost.status == "published").order_by(desc(BlogPost.views)).limit(3)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/rss.xml")
async def get_rss_feed(db: AsyncSession = Depends(get_db)):
    query = select(BlogPost).where(BlogPost.status == "published").order_by(desc(BlogPost.published_at)).limit(20)
    result = await db.execute(query)
    posts = result.scalars().all()
    
    rss_items = []
    for post in posts:
        pub_date = post.published_at.strftime("%a, %d %b %Y %H:%M:%S GMT") if post.published_at else ""
        rss_items.append(f"""
        <item>
            <title>{post.title}</title>
            <link>https://threadangle.com/blog/{post.slug}</link>
            <description>{post.excerpt}</description>
            <pubDate>{pub_date}</pubDate>
            <guid>https://threadangle.com/blog/{post.slug}</guid>
        </item>""")
    
    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
    <channel>
        <title>Threadangle Blog</title>
        <link>https://threadangle.com/blog</link>
        <description>Mastering the angle of viral content. Strategy, productivity, and growth hacks for modern creators.</description>
        <language>en-us</language>
        <lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")}</lastBuildDate>
        {"".join(rss_items)}
    </channel>
    </rss>"""
    
    return Response(content=rss_feed, media_type="application/xml")

# Admin Endpoints
@router.post("/admin/posts", response_model=BlogPostResponse)
async def create_post(
    post_data: BlogPostCreate, 
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(get_admin_auth)
):
    # Auto-calculate read time
    words = len(post_data.content.split())
    read_time = max(1, (words // 200) + (1 if words % 200 > 0 else 0))
    
    new_post = BlogPost(
        **post_data.dict(),
        read_time_minutes=read_time
    )
    
    if new_post.status == "published":
        new_post.published_at = datetime.utcnow()
        
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post

@router.put("/admin/posts/{post_id}", response_model=BlogPostResponse)
async def update_post(
    post_id: int,
    post_data: BlogPostUpdate,
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(get_admin_auth)
) :
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    for key, value in post_data.dict(exclude_unset=True).items():
        setattr(post, key, value)
        
    # Recalculate read time if content changed
    if post_data.content:
        words = len(post.content.split())
        post.read_time_minutes = max(1, (words // 200) + (1 if words % 200 > 0 else 0))
        
    if post.status == "published" and not post.published_at:
        post.published_at = datetime.utcnow()
        
    await db.commit()
    await db.refresh(post)
    return post

@router.delete("/admin/posts/{post_id}")
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    is_admin: bool = Depends(get_admin_auth)
):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    await db.delete(post)
    await db.commit()
    return {"message": "Post deleted"}
