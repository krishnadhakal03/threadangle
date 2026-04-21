from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Boolean, Date, Time, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    plan = Column(String, default="free") # free / starter / pro
    usage_count = Column(Integer, default=0)
    usage_reset_date = Column(DateTime)
    stripe_customer_id = Column(String, nullable=True)
    onboarding_completed = Column(Integer, default=0)
    reset_token = Column(String, nullable=True)
    reset_token_expiry = Column(DateTime, nullable=True)
    google_id = Column(String, nullable=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Voice learning fields
    voice_profile = Column(Text, nullable=True)          # JSON string of learned patterns
    voice_learned = Column(Boolean, default=False)
    successful_generations_count = Column(Integer, default=0)
    voice_learned_at = Column(DateTime, nullable=True)
    # Personalization fields
    niche_tags = Column(Text, nullable=True)             # JSON array of selected niches
    voice_samples_submitted = Column(Boolean, default=False)  # True if user submitted samples during onboarding
    # Admin overrides
    custom_limit = Column(Integer, nullable=True)        # Per-user generation limit override (None = use plan default)

class Generation(Base):
    __tablename__ = "generations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    input_type = Column(String) # url / text
    input_content = Column(String)
    twitter_output = Column(JSON, nullable=True)
    linkedin_output = Column(JSON, nullable=True)
    tiktok_output = Column(JSON, nullable=True)
    hashtags = Column(JSON, nullable=True)
    status = Column(String, default="success")  # success / failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Edited versions (user modifications)
    twitter_content_edited = Column(Text, nullable=True)
    linkedin_content_edited = Column(Text, nullable=True)
    tiktok_content_edited = Column(Text, nullable=True)
    has_edits = Column(Boolean, default=False)
    last_edited_at = Column(DateTime, nullable=True)
    # Instagram Reels metadata
    reels_title = Column(Text, nullable=True)
    reels_description = Column(Text, nullable=True)
    reels_hashtags = Column(Text, nullable=True)
    reels_title_edited = Column(Text, nullable=True)
    reels_description_edited = Column(Text, nullable=True)
    reels_hashtags_edited = Column(Text, nullable=True)
    # YouTube Shorts metadata
    shorts_title = Column(Text, nullable=True)
    shorts_description = Column(Text, nullable=True)
    shorts_tags = Column(Text, nullable=True)
    shorts_title_edited = Column(Text, nullable=True)
    shorts_description_edited = Column(Text, nullable=True)
    shorts_tags_edited = Column(Text, nullable=True)
    # Hook variations (JSON string)
    hook_variations = Column(Text, nullable=True)
    hook_variations_generated = Column(Boolean, default=False)
    # Content scheduling fields
    scheduled_date = Column(Date, nullable=True)           # Which day to post
    scheduled_time = Column(Time, nullable=True)           # What time to post
    posted = Column(Boolean, default=False)                # Has user posted this?
    posted_at = Column(DateTime, nullable=True)            # When they marked it posted
    scheduled_platforms = Column(Text, nullable=True)      # JSON array e.g. ["twitter", "linkedin"]
    # Auto-posting fields
    auto_post_enabled = Column(Boolean, default=False)
    auto_post_platforms = Column(Text, nullable=True)      # JSON array: ["twitter", "linkedin"]
    auto_post_time = Column(DateTime, nullable=True)       # When to auto-post
    auto_posted = Column(Boolean, default=False)
    auto_posted_at = Column(DateTime, nullable=True)
    auto_post_results = Column(Text, nullable=True)        # JSON: {platform: {success, post_id, error}}
    # Video generation fields
    video_run_id = Column(String, nullable=True)
    video_file = Column(String, nullable=True)
    video_duration_seconds = Column(Integer, nullable=True)
    video_thumbnail = Column(String, nullable=True)  # Path to generated thumbnail image
    video_scenes_json = Column(Text, nullable=True)
    video_plan_json = Column(Text, nullable=True)
    video_platform_meta_json = Column(Text, nullable=True)
    # SEO metadata
    seo_title = Column(String(100), nullable=True)
    seo_description = Column(Text, nullable=True)
    seo_tags = Column(Text, nullable=True)  # JSON array
    seo_hashtags = Column(Text, nullable=True)  # JSON array
    thumbnail_text = Column(String(50), nullable=True)
    # Cost tracking
    runway_credits_used = Column(Float, default=0.0)
    elevenlabs_credits_used = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    # Performance tracking
    youtube_views = Column(Integer, default=0)
    youtube_retention = Column(Float, default=0.0)
    youtube_ctr = Column(Float, default=0.0)
    # Batch generation metadata
    batch_id = Column(String, nullable=True, index=True)
    topic = Column(String, nullable=True)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    stripe_subscription_id = Column(String, unique=True)
    plan = Column(String)
    status = Column(String)
    current_period_end = Column(DateTime)

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    subject = Column(String)
    message = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CMSContent(Base):
    __tablename__ = "cms_content"
    id = Column(Integer, primary_key=True, index=True)
    page = Column(String, index=True) # home, pricing, contact, global
    section = Column(String) # hero, features, etc.
    content_key = Column(String, unique=True, index=True)
    content_value = Column(Text)
    content_type = Column(String) # text, textarea, url, boolean, json
    label = Column(String)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class BlogCategory(Base):
    __tablename__ = "blog_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    slug = Column(String, unique=True, index=True)
    description = Column(String)
    post_count = Column(Integer, default=0)

class BlogPost(Base):
    __tablename__ = "blog_posts"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    slug = Column(String, unique=True, index=True)
    excerpt = Column(Text)
    content = Column(Text)
    author_name = Column(String, default="Threadangle Team")
    author_avatar_initials = Column(String, default="TT")
    category = Column(String)
    tags = Column(String) # comma separated
    featured_image_url = Column(String, nullable=True)
    status = Column(String, default="draft") # draft / published
    meta_title = Column(String)
    meta_description = Column(String)
    og_image_url = Column(String, nullable=True)
    read_time_minutes = Column(Integer, default=0)
    views = Column(Integer, default=0)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class OAuthState(Base):
    """Persisted OAuth state tokens — survives backend restarts."""
    __tablename__ = "oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    platform = Column(String, nullable=False)  # 'twitter', 'linkedin', 'instagram'
    code_verifier = Column(String, nullable=True)  # Twitter PKCE
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Which platform
    platform = Column(String, nullable=False)  # 'twitter', 'linkedin', 'instagram'
    
    # OAuth tokens (encrypted)
    access_token = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    token_expires_at = Column(DateTime, nullable=True)
    
    # Platform-specific user info
    platform_user_id = Column(String, nullable=True)  # Their Twitter/LinkedIn ID
    platform_username = Column(String, nullable=True)  # @username or profile name
    platform_profile_pic = Column(String, nullable=True)  # Profile picture URL
    
    # Status
    is_active = Column(Boolean, default=True)
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime, nullable=True)


class BatchJob(Base):
    """Persistent record for multi-video batch generation."""
    __tablename__ = "batch_jobs"

    id = Column(String, primary_key=True, index=True)   # uuid
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_videos = Column(Integer, default=0)
    completed_videos = Column(Integer, default=0)
    failed_videos = Column(Integer, default=0)
    status = Column(String, default="queued")            # queued|processing|done|failed
    niche = Column(String, nullable=True)
    topics_json = Column(Text, nullable=True)            # JSON list of topic strings
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime, nullable=True)


class ABTest(Base):
    """A/B test variants — scripts and metadata, no auto-generation."""
    __tablename__ = "ab_tests"

    id = Column(String, primary_key=True, index=True)   # uuid
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic = Column(String, nullable=False)
    niche = Column(String, nullable=True)
    variants_json = Column(Text, nullable=True)          # JSON list of variant dicts
    winner_variant_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
