import asyncio
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from database import AsyncSessionLocal, Base, engine
from models import CMSContent, BlogCategory, BlogPost

async def seed_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as db:
        # 1. Seed CMS Content
        cms_items = [
            # HOME - HERO
            ("home", "hero", "hero_badge", "Find the angle. Go viral.", "text", "Hero Badge"),
            ("home", "hero", "hero_headline", "Turn Any Content Into Viral Social Posts — In Seconds", "text", "Hero Headline"),
            ("home", "hero", "hero_subheadline", "Paste a URL or text. Get a Twitter thread, LinkedIn post, and TikTok script instantly. Threadangle finds the perfect angle for every platform.", "textarea", "Hero Subheadline"),
            ("home", "hero", "hero_cta_primary", "Start Free — No Credit Card", "text", "Primary CTA"),
            ("home", "hero", "hero_cta_secondary", "See How It Works", "text", "Secondary CTA"),
            ("home", "hero", "hero_social_proof", "Join 1,200+ creators saving 5+ hours per week", "text", "Social Proof Text"),
            
            # HOME - HOW IT WORKS
            ("home", "how_it_works", "how_title", "How It Works", "text", "Section Title"),
            ("home", "how_it_works", "step1_title", "Paste", "text", "Step 1 Title"),
            ("home", "how_it_works", "step1_description", "Drop in your blog URL or any text content", "textarea", "Step 1 Description"),
            ("home", "how_it_works", "step2_title", "Choose", "text", "Step 2 Title"),
            ("home", "how_it_works", "step2_description", "Select your platforms and content tone", "textarea", "Step 2 Description"),
            ("home", "how_it_works", "step3_title", "Create", "text", "Step 3 Title"),
            ("home", "how_it_works", "step3_description", "Get ready-to-post content in 20 seconds", "textarea", "Step 3 Description"),

            # HOME - FEATURES
            ("home", "features", "features_title", "Everything You Need to Go Viral", "text", "Features Title"),
            ("home", "features", "feature1_title", "Twitter Threads", "text", "Feature 1 Title"),
            ("home", "features", "feature1_description", "10-tweet threads with viral hooks, numbered points, and strong CTAs", "textarea", "Feature 1 Description"),
            ("home", "features", "feature2_title", "LinkedIn Posts", "text", "Feature 2 Title"),
            ("home", "features", "feature2_description", "Professional 200-300 word posts that drive engagement and followers", "textarea", "Feature 2 Description"),
            ("home", "features", "feature3_title", "TikTok Scripts", "text", "Feature 3 Title"),
            ("home", "features", "feature3_description", "Full scene-by-scene video scripts with hooks, b-roll suggestions, and captions", "textarea", "Feature 3 Description"),
            ("home", "features", "feature4_title", "Multiple Tones", "text", "Feature 4 Title"),
            ("home", "features", "feature4_description", "Professional, casual, viral, or educational — you choose the angle", "textarea", "Feature 4 Description"),

            # HOME - SOCIAL PROOF
            ("home", "social_proof", "stats_users", "1,200+", "text", "Total Users Stat"),
            ("home", "social_proof", "stats_users_label", "Creators Using Threadangle", "text", "Users Label"),
            ("home", "social_proof", "stats_generations", "50,000+", "text", "Total Generations Stat"),
            ("home", "social_proof", "stats_generations_label", "Posts Generated", "text", "Generations Label"),
            ("home", "social_proof", "stats_time_saved", "5+ Hours", "text", "Time Saved Stat"),
            ("home", "social_proof", "stats_time_saved_label", "Saved Per Week Per User", "text", "Time Saved Label"),

            # HOME - TESTIMONIALS
            ("home", "testimonials", "testimonials", json.dumps([
                {"name": "Sarah K.", "role": "Content Creator", "avatar_initials": "SK", "text": "Threadangle saves me 6 hours every week. I just paste my blog URL and all my social posts are done.", "platform": "Twitter"},
                {"name": "Marcus T.", "role": "Marketing Manager", "avatar_initials": "MT", "text": "The LinkedIn posts it generates get 3x more engagement than what I was writing manually.", "platform": "LinkedIn"},
                {"name": "Priya M.", "role": "Solopreneur", "avatar_initials": "PM", "text": "I was skeptical but the TikTok scripts are genuinely good. My last video got 40k views.", "platform": "TikTok"}
            ]), "json", "Testimonials Data"),

            # HOME - CTA
            ("home", "cta", "bottom_cta_headline", "Ready to Find Your Angle?", "text", "Bottom CTA Headline"),
            ("home", "cta", "bottom_cta_subtext", "Join thousands of creators turning content into viral posts every day.", "textarea", "Bottom CTA Subtext"),
            ("home", "cta", "bottom_cta_button", "Create My Free Account", "text", "Bottom CTA Button"),

            # GLOBAL
            ("global", "announcement_bar", "announcement_bar_enabled", "false", "boolean", "Show Announcement Bar"),
            ("global", "announcement_bar", "announcement_bar_text", "🎉 New: TikTok script generation is now live! Try it free.", "text", "Announcement Text"),
            ("global", "announcement_bar", "announcement_bar_link", "/pricing", "url", "Announcement Link"),
            ("global", "announcement_bar", "announcement_bar_color", "#3B82F6", "text", "Bar Background Color"),
            ("global", "footer", "footer_tagline", "Find the angle. Go viral.", "text", "Footer Tagline"),
            ("global", "footer", "footer_copyright", f"© {datetime.now().year} Kriangle. All rights reserved.", "text", "Copyright Text"),
            ("global", "footer", "footer_product_credit", "Threadangle is a product by Kriangle", "text", "Product Credit"),

            # PRICING
            ("pricing", "header", "pricing_headline", "Simple, Transparent Pricing", "text", "Pricing Headline"),
            ("pricing", "header", "pricing_subheadline", "Start free. Upgrade when you are ready. Cancel anytime.", "textarea", "Pricing Subheadline"),
            ("pricing", "plans", "plan_free_name", "Free", "text", "Free Plan Name"),
            ("pricing", "plans", "plan_free_price", "0", "text", "Free Plan Price"),
            ("pricing", "plans", "plan_free_description", "Perfect for trying Threadangle", "text", "Free Plan Description"),
            ("pricing", "plans", "plan_free_features", json.dumps(["3 generations per month", "Twitter threads", "LinkedIn posts", "No credit card required"]), "json", "Free Features"),
            ("pricing", "plans", "plan_free_cta", "Get Started Free", "text", "Free CTA"),
            ("pricing", "plans", "plan_starter_name", "Starter", "text", "Starter Plan Name"),
            ("pricing", "plans", "plan_starter_price", "12", "text", "Starter Plan Price"),
            ("pricing", "plans", "plan_starter_description", "For creators who post consistently", "text", "Starter Plan Description"),
            ("pricing", "plans", "plan_starter_features", json.dumps(["Unlimited generations", "Twitter threads", "LinkedIn posts", "TikTok scripts", "All 4 tones", "Generation history", "Email support"]), "json", "Starter Features"),
            ("pricing", "plans", "plan_starter_cta", "Upgrade to Starter", "text", "Starter CTA"),
            ("pricing", "plans", "plan_pro_name", "Pro", "text", "Pro Plan Name"),
            ("pricing", "plans", "plan_pro_price", "19", "text", "Pro Plan Price"),
            ("pricing", "plans", "plan_pro_description", "For power users and small teams", "text", "Pro Plan Description"),
            ("pricing", "plans", "plan_pro_features", json.dumps(["Everything in Starter", "Enhanced TikTok scripts with b-roll", "Scene-by-scene video breakdowns", "Priority generation queue", "Early access to new features"]), "json", "Pro Features"),
            ("pricing", "plans", "plan_pro_cta", "Upgrade to Pro", "text", "Pro CTA"),
            ("pricing", "plans", "pricing_badge", "MOST POPULAR", "text", "Popular Badge Text"),

            # CONTACT
            ("contact", "header", "contact_headline", "Get in Touch", "text", "Contact Headline"),
            ("contact", "header", "contact_subheadline", "Have a question, feedback, or just want to say hello? We would love to hear from you.", "textarea", "Contact Subheadline"),
            ("contact", "info", "contact_email", "hello@kriangle.com", "text", "Official Email"),
            ("contact", "info", "contact_response_time", "Within 24 hours", "text", "Response Time"),
            ("contact", "info", "contact_hours", "Monday to Saturday", "text", "Operating Hours"),
            ("contact", "info", "contact_made_by", "Kriangle", "text", "Author Organization"),
        ]

        for p, s, k, v, t, l in cms_items:
            db.add(CMSContent(page=p, section=s, content_key=k, content_value=v, content_type=t, label=l))

        # 2. Seed Blog Categories
        categories = [
            ("Content Strategy", "content-strategy", "Repurposing and long-term planning."),
            ("Twitter Growth", "twitter-growth", "How to win on X."),
            ("LinkedIn Tips", "linkedin-tips", "Professional networking and content."),
            ("TikTok & Video", "tiktok-video", "Scripts and short-form video tips."),
            ("AI Tools", "ai-tools", "Using AI to speed up your workflow."),
            ("Creator Economy", "creator-economy", "How to monetize your audience.")
        ]
        for n, s, d in categories:
            db.add(BlogCategory(name=n, slug=s, description=d))

        # 3. Seed Blog Posts
        posts = [
            {
                "title": "How to Turn a Blog Post Into a Twitter Thread (The Fast Way in 2026)",
                "slug": "how-to-turn-blog-post-into-twitter-thread",
                "category": "Twitter Growth",
                "tags": "twitter thread, content repurposing, blog to thread",
                "excerpt": "Step-by-step guide to turning any blog post into a viral Twitter thread. Manual method + AI shortcut. Takes 20 seconds with Threadangle.",
                "read_time_minutes": 7,
                "status": "published",
                "meta_title": "How to Turn a Blog Post Into a Twitter Thread in 2026 | Threadangle",
                "meta_description": "Step-by-step guide to turning any blog post into a viral Twitter thread. Manual method + AI shortcut. Takes 20 seconds with Threadangle.",
                "content": """
                    <p>Repurposing your content is no longer optional in 2026. Creators who repurpose their long-form blog posts into short-form social content get 3x more reach than those who don't.</p>
                    <h2>Why Twitter Threads Outperform Single Tweets</h2>
                    <p>Algorithmically, threads keep users on the platform longer. Engagement data shows that threads receive 5x more retweets than single images or links.</p>
                    <h2>The Manual Method Step by Step</h2>
                    <ol>
                        <li>Identify the 5-7 key points in your blog post.</li>
                        <li>Write a "Hook" tweet that promises a specific outcome.</li>
                        <li>Break down each point into 280 characters.</li>
                        <li>Add "Bridges" between tweets to keep the flow.</li>
                        <li>Include a Call to Action (CTA) at the end.</li>
                    </ol>
                    <div style="background: #111; padding: 20px; border-radius: 12px; border: 1px border-accent; margin: 20px 0;">
                        <strong>Want to skip the manual work?</strong> Threadangle turns any blog URL into a complete Twitter thread in 20 seconds. Try free — no credit card.
                    </div>
                    <h2>The AI Method — How to Do It in 20 Seconds</h2>
                    <p>Using tools like Threadangle, you can simply paste your URL and let the AI find the "viral angle" for you.</p>
                    <h2>Writing Hooks That Actually Get Clicks</h2>
                    <ul>
                        <li>The "Negative" Hook: "Stop doing X if you want Y."</li>
                        <li>The "Data" Hook: "I analyzed 1,000 posts and found Z."</li>
                        <li>The "Transformation" Hook: "How I went from A to B in 30 days."</li>
                    </ul>
                    <p>Conclusion: Find your angle and go viral today.</p>
                """
            },
            {
                "title": "The 7 Best Twitter Thread Generators in 2026 (Free and Paid)",
                "slug": "best-twitter-thread-generators-2026",
                "category": "AI Tools",
                "tags": "twitter thread generator, AI writing tools, social media tools",
                "excerpt": "Compared the top Twitter thread generators of 2026. Features, pricing, and which one is best for creators, marketers, and solopreneurs.",
                "read_time_minutes": 8,
                "status": "published",
                "meta_title": "7 Best Twitter Thread Generators in 2026 — Free & Paid | Threadangle",
                "meta_description": "Compared the top Twitter thread generators of 2026. Features, pricing, and which one is best for creators, marketers, and solopreneurs.",
                "content": """
                    <p>Saving time is the name of the game. Here is our comparison of the top tools this year.</p>
                    <h2>What to Look for in a Thread Generator</h2>
                    <ul>
                        <li>Accuracy of context extraction.</li>
                        <li>Platform-specific formatting.</li>
                        <li>Tone customization.</li>
                        <li>Ease of use.</li>
                    </ul>
                    <h2>The 7 Best Tools</h2>
                    <p>1. <strong>Threadangle</strong> - Best overall for repurposing URLs.</p>
                    <p>2. Typefully - Great for drafting manually.</p>
                    <p>3. Hypefury - Best for scheduling.</p>
                    <p>4. Tweet Hunter - Powerful analytics.</p>
                    <p>5. Chirr App - Simple and clean.</p>
                    <p>6. Taplio - Best for LinkedIn-Twitter cross-posting.</p>
                    <p>7. Buffer - Good all-in-one scheduler.</p>
                    <h2>Free vs Paid — Which Should You Choose</h2>
                    <p>If you post < 3 times a month, free is fine. Power users need paid tools.</p>
                """
            },
            {
                "title": "How to Write a LinkedIn Post That Gets 10x More Views in 2026",
                "slug": "how-to-write-linkedin-post-more-views",
                "category": "LinkedIn Tips",
                "tags": "linkedin post generator, linkedin growth, linkedin content",
                "excerpt": "Proven LinkedIn post formula used by top creators. Hook, body, CTA structure. Includes AI shortcut to generate posts automatically.",
                "read_time_minutes": 6,
                "status": "published",
                "meta_title": "How to Write LinkedIn Posts That Get 10x More Views | Threadangle",
                "meta_description": "Proven LinkedIn post formula used by top creators. Hook, body, CTA structure. Includes AI shortcut to generate posts automatically.",
                "content": """
                    <p>LinkedIn is the new town square for professionals. Here is how to win.</p>
                    <h2>The Anatomy of a Viral LinkedIn Post</h2>
                    <p>It starts with the first 3 lines. If they don't click "See More", you've lost.</p>
                    <h2>The Hook — Your First Line Makes or Breaks Everything</h2>
                    <p>Use "I was today years old when I learned..." or "Unpopular opinion: ..."</p>
                    <h2>The Body — How to Structure for Maximum Readability</h2>
                    <p>One sentence per line. Lots of white space.</p>
                    <h2>Best Times to Post on LinkedIn in 2026</h2>
                    <p>Tuesdays at 9 AM remains the sweet spot.</p>
                """
            },
            {
                "title": "Content Repurposing: How to Turn One Piece of Content Into 10",
                "slug": "content-repurposing-guide-2026",
                "category": "Content Strategy",
                "tags": "content repurposing, content strategy, social media",
                "excerpt": "Complete guide to content repurposing. How top creators turn one blog post into Twitter threads, LinkedIn posts, TikToks, newsletters and more.",
                "read_time_minutes": 9,
                "status": "published",
                "meta_title": "Content Repurposing Guide 2026: Turn 1 Post Into 10 | Threadangle",
                "meta_description": "Complete guide to content repurposing. How top creators turn one blog post into Twitter threads, LinkedIn posts, TikToks, newsletters and more.",
                "content": """
                    <p>Stop running on the content hamster wheel. Create once, publish everywhere.</p>
                    <h2>The Content Repurposing Pyramid</h2>
                    <p>Start with a core Pillar Piece (Blog/Video) and break it down into micro-content.</p>
                    <h2>How to Turn a Blog Post Into 10 Pieces of Content</h2>
                    <ul>
                        <li>1x Twitter Thread</li>
                        <li>3x Single Tweets</li>
                        <li>1x LinkedIn Post</li>
                        <li>1x TikTok Script</li>
                        <li>1x Newsletter update</li>
                        <li>3x Stories</li>
                    </ul>
                """
            },
            {
                "title": "TikTok Script Formula: The Hook-Problem-Solution-CTA Framework",
                "slug": "tiktok-script-formula-hook-problem-solution-cta",
                "category": "TikTok & Video",
                "tags": "tiktok script, tiktok content, video script generator",
                "excerpt": "The proven 4-part TikTok script formula used by viral creators. With examples, timing breakdowns, and an AI tool to generate scripts automatically.",
                "read_time_minutes": 6,
                "status": "published",
                "meta_title": "TikTok Script Formula: Hook Problem Solution CTA | Threadangle",
                "meta_description": "The proven 4-part TikTok script formula used by viral creators. With examples, timing breakdowns, and an AI tool to generate scripts automatically.",
                "content": """
                    <p>Most TikToks fail in the first 3 seconds because they lack a hook. Don't be "most people".</p>
                    <h2>The 4-Part Framework Explained</h2>
                    <p>Hook -> Problem -> Solution -> CTA.</p>
                    <h2>Part 1 — The Hook (0-3 seconds)</h2>
                    <p>Visual hooks (something moving) + Audio hooks (a strong statement).</p>
                    <h2>Part 4 — The CTA (40-50 seconds)</h2>
                    <p>Don't just say "follow me". Say "Follow for more tips on X if you want to achieve Y."</p>
                """
            }
        ]

        for p_data in posts:
            db.add(BlogPost(**p_data, published_at=datetime.utcnow()))

        await db.commit()
    print("Database seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
