from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List, Optional, Any
from datetime import datetime

# CMS Schemas
class CMSContentBase(BaseModel):
    page: str
    section: str
    content_key: str
    content_value: str
    content_type: str
    label: str

class CMSContentUpdate(BaseModel):
    content_value: str

class CMSContentResponse(CMSContentBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

# Blog Schemas
class BlogCategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class BlogCategoryResponse(BlogCategoryBase):
    id: int
    post_count: int

    class Config:
        from_attributes = True

class BlogPostBase(BaseModel):
    title: str
    slug: str
    excerpt: str
    content: str
    category: str
    tags: Optional[str] = None
    featured_image_url: Optional[str] = None
    status: str = "draft"
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None

class BlogPostCreate(BlogPostBase):
    author_name: str = "Threadangle Team"
    author_avatar_initials: str = "TT"

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    featured_image_url: Optional[str] = None
    status: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    og_image_url: Optional[str] = None

class BlogPostResponse(BlogPostBase):
    id: int
    author_name: str
    author_avatar_initials: str
    read_time_minutes: int
    views: int
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BlogPostList(BaseModel):
    id: int
    title: str
    slug: str
    excerpt: str
    category: str
    author_name: str
    read_time_minutes: int
    views: int
    published_at: Optional[datetime]
    featured_image_url: Optional[str]

    class Config:
        from_attributes = True
