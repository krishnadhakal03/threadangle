"""
Comprehensive CMS seed script.
Populates the database with all site content so every page is fully dynamic.

Run: python seed_cms.py
Idempotent — safe to run multiple times (won't overwrite values you've edited in admin).
"""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "threadangle.db")

# fmt: off
CMS_ENTRIES = [
    # ── HOME PAGE ────────────────────────────────────────────────────────────
    # Hero
    ("home", "hero", "hero_badge",         "Works for any creator — not just marketers",                     "text",     "Hero Badge Text"),
    ("home", "hero", "hero_headline",      "One Input. Five Platform-Ready Posts. In ~20 Seconds.",          "text",     "Hero Main Headline"),
    ("home", "hero", "hero_subheadline",   "Paste a blog post, YouTube video, or raw idea. Instantly get Twitter/X threads, LinkedIn posts, TikTok scripts, Instagram Reels captions & hashtags, and YouTube Shorts titles & descriptions — sounding like you, not a robot.", "textarea", "Hero Sub-Headline"),
    ("home", "hero", "hero_primary_cta",   "Start Free — 5 Generations",                                    "text",     "Hero Primary CTA Button"),
    ("home", "hero", "hero_secondary_cta", "See Interactive Demo",                                           "text",     "Hero Secondary CTA Button"),
    ("home", "hero", "hero_social_proof",  "Free plan includes 5 generations • No credit card required",     "text",     "Hero Social Proof Line"),

    # How It Works (3-step intro)
    ("home", "how", "how_title",           "How Threadangle Works",                                          "text",     "How It Works Section Title"),
    ("home", "how", "step1_title",         "Input",                                                          "text",     "Step 1 Title"),
    ("home", "how", "step1_description",   "Paste a URL, YouTube link, or raw text.",                        "text",     "Step 1 Description"),
    ("home", "how", "step2_title",         "Select Outputs",                                                 "text",     "Step 2 Title"),
    ("home", "how", "step2_description",   "Choose Twitter, LinkedIn, TikTok, Reels, and Shorts.",           "text",     "Step 2 Description"),
    ("home", "how", "step3_title",         "Generate + Refine",                                              "text",     "Step 3 Title"),
    ("home", "how", "step3_description",   "Edit instantly, save history, and schedule posts.",              "text",     "Step 3 Description"),

    # Complete Workflow (4-step feature section)
    ("home", "workflow", "features_title",             "Built for Real Publishing Workflows",                "text",     "Workflow Section Title"),
    ("home", "workflow", "workflow_step1_title",        "Voice Learning",                                    "text",     "Workflow Step 1 Title"),
    ("home", "workflow", "workflow_step1_description",  "Learns your writing style over time so generated content sounds exactly like you.", "textarea", "Workflow Step 1 Description"),
    ("home", "workflow", "workflow_step2_title",        "Generate in 20s",                                   "text",     "Workflow Step 2 Title"),
    ("home", "workflow", "workflow_step2_description",  "One click generates 5 platform-ready posts from any URL, video, or idea.", "textarea", "Workflow Step 2 Description"),
    ("home", "workflow", "workflow_step3_title",        "Edit & A/B Hooks",                                  "text",     "Workflow Step 3 Title"),
    ("home", "workflow", "workflow_step3_description",  "Refine content and generate hook variations to find what resonates.", "textarea", "Workflow Step 3 Description"),
    ("home", "workflow", "workflow_step4_title",        "Schedule & Publish",                                "text",     "Workflow Step 4 Title"),
    ("home", "workflow", "workflow_step4_description",  "Schedule to your calendar and auto-post to LinkedIn with one click.", "textarea", "Workflow Step 4 Description"),

    # Stats
    ("home", "stats", "stats_users",              "1,200+",                         "text", "Stat: User Count"),
    ("home", "stats", "stats_users_label",        "Creators Using Threadangle",     "text", "Stat: User Count Label"),
    ("home", "stats", "stats_generations",        "50,000+",                        "text", "Stat: Generations Count"),
    ("home", "stats", "stats_generations_label",  "Posts Generated",                "text", "Stat: Generations Label"),
    ("home", "stats", "stats_time_saved",         "5+ Hours",                       "text", "Stat: Time Saved"),
    ("home", "stats", "stats_time_saved_label",   "Saved Per Week Per User",        "text", "Stat: Time Saved Label"),

    # Testimonials (JSON array)
    ("home", "social_proof", "testimonials", json.dumps([
        {
            "name": "Jamie L.",
            "role": "Fitness Coach · @jamielifts",
            "initials": "JL",
            "text": "ok i didn't believe the hype but i pasted my workout blog post and got a full twitter thread + tiktok script in like 30 seconds. the tiktok sounded like me which was the surprising part",
            "platform": "TikTok"
        },
        {
            "name": "Marcus T.",
            "role": "B2B Marketing · @marcust_mktg",
            "initials": "MT",
            "text": "My LinkedIn engagement went up noticeably after I started using Threadangle. The hooks are sharper than what I write from scratch. Saves me about 2 hours every week.",
            "platform": "LinkedIn"
        },
        {
            "name": "Priya M.",
            "role": "Design Solopreneur · @priyamade",
            "initials": "PM",
            "text": "I do not have time to rewrite my blog for Instagram, LinkedIn and TikTok. Now I don't have to. One paste and it's done. The voice actually sounds like mine.",
            "platform": "Twitter"
        }
    ]), "json", "Testimonials (JSON array of {name, role, initials, text, platform})"),

    # FAQs (JSON array)
    ("home", "faq", "faq_title",   "Frequently Asked Questions",  "text", "FAQ Section Title"),
    ("home", "faq", "home_faqs", json.dumps([
        {"q": "What counts as one generation?",            "a": "One URL or text input equals one generation, regardless of how many platforms you select. Choosing Twitter, LinkedIn and TikTok together still uses only one generation."},
        {"q": "Do I need a credit card for the free plan?", "a": "No. Sign up with just your email and password. No payment details required until you choose to upgrade."},
        {"q": "What happens when I use all 5 free generations?", "a": "You will see an upgrade prompt. All your generated content remains in your history, and you can upgrade anytime to keep generating."},
        {"q": "Can I cancel my subscription anytime?",     "a": "Yes. Go to Settings and click Manage Subscription. You will be taken to the Stripe portal where you can cancel with one click. Your plan stays active until the end of the billing period."},
        {"q": "What AI model powers Threadangle?",         "a": "Threadangle uses Claude by Anthropic, one of the most capable AI models available. It is the same technology used by leading AI companies worldwide."},
        {"q": "Can I schedule posts inside Threadangle?",  "a": "Yes. You can schedule content from History and view your posting plan in Calendar. LinkedIn auto-posting is currently the active supported channel."},
        {"q": "What kind of content works best?",          "a": "Blog posts, articles, YouTube transcripts, newsletters, podcast notes, and raw drafts all work well. If it has substance, Threadangle can turn it into platform-ready content."},
        {"q": "Is my content stored or shared?",           "a": "Your generated content is stored privately in your account history. It is never shared with other users or used to train AI models."}
    ]), "json", "Landing Page FAQs (JSON array of {q, a})"),

    # Bottom CTA
    ("home", "cta", "bottom_cta_headline", "Launch Better Content Faster",                                    "text",     "Bottom CTA Headline"),
    ("home", "cta", "bottom_cta_subtext",  "Stop rewriting the same idea for every platform. Generate once, publish everywhere with platform-specific output.", "textarea", "Bottom CTA Sub-text"),
    ("home", "cta", "bottom_cta_button",   "Create Free Account",                                             "text",     "Bottom CTA Button Label"),

    # ── PRICING PAGE ─────────────────────────────────────────────────────────
    ("pricing", "hero", "pricing_headline",    "Simple, Transparent Pricing",                "text",     "Pricing Page Headline"),
    ("pricing", "hero", "pricing_subheadline", "Start free. Upgrade when you are ready. Cancel anytime.", "text", "Pricing Page Sub-headline"),

    ("pricing", "plans", "pricing_plans", json.dumps([
        {
            "name": "Free",
            "planId": "free",
            "price": "$0",
            "unit": "",
            "description": "Perfect for getting started.",
            "features": ["5 free generations", "Twitter threads", "LinkedIn posts", "No credit card required"],
            "button": "Get Started Free",
            "popular": False,
            "color": "gray"
        },
        {
            "name": "Starter",
            "planId": "solo",
            "price": "$12",
            "unit": "/month",
            "description": "For creators who post consistently.",
            "features": ["Unlimited generations", "Twitter threads", "LinkedIn posts", "TikTok scripts", "All 4 tones", "Generation history", "Email support"],
            "button": "Upgrade to Starter",
            "popular": True,
            "color": "accent"
        },
        {
            "name": "Pro",
            "planId": "founder",
            "price": "$19",
            "unit": "/month",
            "description": "For power users and small teams.",
            "features": ["Everything in Starter", "Enhanced TikTok scripts with b-roll", "Scene-by-scene video breakdowns", "Priority generation queue", "Early access to new features"],
            "button": "Upgrade to Pro",
            "popular": False,
            "color": "accent"
        }
    ]), "json", "Pricing Plans (JSON array — edit price, features, description)"),

    ("pricing", "comparison", "pricing_comparison", json.dumps([
        {"name": "Generations",       "free": "5",        "starter": "Unlimited", "pro": "Unlimited"},
        {"name": "Twitter Threads",   "free": True,       "starter": True,        "pro": True},
        {"name": "LinkedIn Posts",    "free": True,       "starter": True,        "pro": True},
        {"name": "TikTok Scripts",    "free": False,      "starter": True,        "pro": True},
        {"name": "Instagram Reels",   "free": False,      "starter": True,        "pro": True},
        {"name": "YouTube Shorts",    "free": False,      "starter": True,        "pro": True},
        {"name": "Voice Learning",    "free": False,      "starter": True,        "pro": True},
        {"name": "Content History",   "free": False,      "starter": True,        "pro": True},
        {"name": "Auto-Scheduling",   "free": False,      "starter": True,        "pro": True},
        {"name": "Video Scripts",     "free": False,      "starter": False,       "pro": True},
        {"name": "Priority Queue",    "free": False,      "starter": False,       "pro": True}
    ]), "json", "Feature Comparison Table (JSON array of {name, free, starter, pro})"),

    ("pricing", "faqs", "pricing_faqs", json.dumps([
        {"q": "Can I switch plans later?",                    "a": "Yes. You can upgrade or downgrade at any time from your account Settings page. Changes take effect immediately."},
        {"q": "What happens to my content if I cancel?",      "a": "Your generated content history is saved for 30 days after cancellation. You can export it anytime before that."},
        {"q": "Do you offer refunds?",                        "a": "We do not offer refunds on the current billing period but you can cancel anytime to stop future charges. No questions asked."},
        {"q": "Is there a free trial for paid plans?",        "a": "The free plan gives you 5 generations to try the product with no credit card required. That is your trial."}
    ]), "json", "Pricing Page FAQs (JSON array of {q, a})"),

    # ── CONTACT PAGE ─────────────────────────────────────────────────────────
    ("contact", "hero",    "contact_headline",       "Get in Touch",                                                                  "text",     "Contact Page Headline"),
    ("contact", "hero",    "contact_subheadline",    "Have a question, feedback, or just want to say hello? We would love to hear from you.", "textarea", "Contact Page Sub-headline"),
    ("contact", "info",    "contact_email",          "hello@kriangle.com",                                                            "text",     "Support Email Address"),
    ("contact", "info",    "contact_response_time",  "Within 24 hours",                                                               "text",     "Response Time"),
    ("contact", "info",    "contact_hours",          "Monday to Saturday",                                                            "text",     "Support Hours"),
    ("contact", "info",    "contact_made_by",        "Kriangle",                                                                      "text",     "Made By (Company Name Display)"),

    ("contact", "faqs", "contact_faqs", json.dumps([
        {"q": "How do I cancel my subscription?",  "a": "Go to Settings → Manage Subscription. You'll be taken to the Stripe portal where you can cancel with one click."},
        {"q": "Why is my generation failing?",      "a": "Make sure your URL is publicly accessible or try using raw text instead. YouTube transcripts require a publicly available video."},
        {"q": "Can I get a refund?",               "a": "We don't offer refunds on the current billing period, but you can cancel anytime to stop future charges."}
    ]), "json", "Contact Page Quick Answers (JSON array of {q, a})"),

    # ── ABOUT PAGE ───────────────────────────────────────────────────────────
    ("about", "hero", "about_badge", "OUR STORY", "text", "About Hero Badge"),
    ("about", "hero", "about_headline", "Built by a Creator, For Creators", "text", "About Hero Headline"),
    ("about", "hero", "about_subheadline", "Threadangle started because I was spending 3 hours every week turning my blog posts into social content. There had to be a better way.", "textarea", "About Hero Subheadline"),
    ("about", "founder", "about_founder_title", "Hi, I am the founder of Kriangle", "text", "Founder Block Title"),
    ("about", "founder", "about_founder_subtitle", "Solo developer · Building in public", "text", "Founder Block Subtitle"),
    ("about", "founder", "about_founder_story", "I am a solo developer building Threadangle in public. I got tired of watching great content die because creators did not have time to repurpose it. Threadangle is the tool I wished existed — paste your content, get platform-perfect posts in 20 seconds, and spend your time creating instead of formatting.", "textarea", "Founder Story"),
    ("about", "stats", "about_stat_1_value", "20 seconds", "text", "About Stat 1 Value"),
    ("about", "stats", "about_stat_1_label", "Average generation time", "text", "About Stat 1 Label"),
    ("about", "stats", "about_stat_2_value", "3 platforms", "text", "About Stat 2 Value"),
    ("about", "stats", "about_stat_2_label", "Twitter, LinkedIn, TikTok", "text", "About Stat 2 Label"),
    ("about", "mission", "about_mission_badge", "WHY WE EXIST", "text", "Mission Badge"),
    ("about", "mission", "about_mission_title", "Our Mission", "text", "Mission Title"),
    ("about", "mission", "about_mission_body", "Every creator has great ideas. Not every creator has time to adapt those ideas for every platform. Threadangle exists to remove that barrier — so your ideas reach more people, on more platforms, with less effort.", "textarea", "Mission Body"),
    ("about", "values", "about_values_title", "What We Believe", "text", "Values Section Title"),
    ("about", "values", "about_values", json.dumps([
        {"icon": "⚡", "title": "Speed matters", "body": "Your time is the most valuable thing you have. We measure success in seconds, not minutes."},
        {"icon": "🎯", "title": "Platform context", "body": "A Twitter thread is not a LinkedIn post. Each platform has its own language and we speak all of them."},
        {"icon": "🔨", "title": "Built in public", "body": "We share our progress, our numbers, and our mistakes openly. No corporate speak. Just honest building."}
    ]), "json", "About Values Cards (JSON array of {icon,title,body})"),
    ("about", "cta", "about_cta_title", "Want to Try It?", "text", "About CTA Title"),
    ("about", "cta", "about_cta_body", "5 free generations. No credit card. No commitment.", "text", "About CTA Body"),
    ("about", "cta", "about_cta_button", "Start Free — No Credit Card", "text", "About CTA Button Text"),

    # ── PRIVACY PAGE ─────────────────────────────────────────────────────────
    ("privacy", "hero", "privacy_title", "Privacy Policy — Threadangle", "text", "Privacy Title"),
    ("privacy", "hero", "privacy_last_updated", "Last updated: March 2026", "text", "Privacy Last Updated"),
    ("privacy", "body", "privacy_sections", json.dumps([
        {"heading": "Information We Collect", "body": "We collect information that you provide directly to us, such as when you create an account, update your profile, use our services, or communicate with us. This includes your email address, basic usage data, and payment information handled securely via Stripe."},
        {"heading": "How We Use Your Information", "body": "We use the information we collect to provide, maintain, and improve our services, communicate with you (such as sending essential account emails), and personalize your experience with Threadangle."},
        {"heading": "Data Storage", "body": "All user data is stored securely on encrypted AWS servers. We implement appropriate technical and organizational measures to protect the security of your personal information against unauthorized access or disclosure."},
        {"heading": "Third Party Services", "body": "We use trusted third-party services to operate Threadangle: Stripe for secure payment processing, Anthropic for AI content generation, and Zoho for transactional email delivery. These services handle your data in accordance with their own privacy policies."},
        {"heading": "Cookies", "body": "We use minimal cookies on our website. Cookies are utilized exclusively for essential authentication purposes to keep you securely logged into your account during your session. We do not use tracking or advertising cookies."},
        {"heading": "Your Rights", "body": "You have the right to access, update, delete, or export your personal data at any time. If you wish to exercise any of these rights, please contact us directly at our support email."},
        {"heading": "Contact", "body": "If you have any questions or concerns about this Privacy Policy or how we handle your data, please contact us at hello@kriangle.com."}
    ]), "json", "Privacy Sections (JSON array of {heading,body})"),

    # ── TERMS PAGE ───────────────────────────────────────────────────────────
    ("terms", "hero", "terms_title", "Terms of Service — Threadangle", "text", "Terms Title"),
    ("terms", "hero", "terms_last_updated", "Last updated: March 2026", "text", "Terms Last Updated"),
    ("terms", "body", "terms_sections", json.dumps([
        {"heading": "Acceptance of Terms", "body": "By accessing or using Threadangle, you agree to be bound by these Terms of Service. If you disagree with any part of the terms, you do not have permission to access the Service."},
        {"heading": "Description of Service", "body": "Threadangle is an AI content generation tool that transforms URLs and text inputs into formatted social media posts and scripts for various platforms."},
        {"heading": "Free and Paid Plans", "body": "We offer a free tier that includes 5 content generations. To unlock additional generation capabilities and access to advanced features, users must subscribe to one of our paid plans."},
        {"heading": "Acceptable Use", "body": "You agree not to use the Service to generate spam, malicious content, illegal material, or to violate the rights of others. Reselling API access or utilizing automated scripts to systematically harvest data or bypass generation limits is strictly prohibited."},
        {"heading": "Content Ownership", "body": "You retain all ownership rights to the content you generate using Threadangle. We do not claim any proprietary rights over the text or ideas you produce through the Service."},
        {"heading": "Payment Terms", "body": "Paid subscriptions are billed on a monthly basis. You may cancel your subscription at any time, and the cancellation will take effect at the end of the current billing cycle. We do not offer refunds or credits for partial months of service."},
        {"heading": "Limitation of Liability", "body": "In no event shall Threadangle, its directors, employees, or partners be liable for any indirect, incidental, special, consequential or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting from your access to or use of or inability to access or use the Service."},
        {"heading": "Changes to Terms", "body": "We reserve the right to modify or replace these Terms at any time. If a revision is material, we will provide at least 30 days notice prior to any new terms taking effect."},
        {"heading": "Contact", "body": "If you have any questions about these Terms, please contact us at hello@kriangle.com."}
    ]), "json", "Terms Sections (JSON array of {heading,body})"),

    # ── GLOBAL SETTINGS ───────────────────────────────────────────────────────
    ("global", "brand",   "site_name",            "Threadangle",                      "text", "Site / Product Name"),
    ("global", "brand",   "site_tagline",         "Find the angle. Go viral.",        "text", "Site Tagline"),
    ("global", "brand",   "support_email",        "hello@kriangle.com",               "text", "Support Email"),
    ("global", "brand",   "company_name",         "Kriangle",                         "text", "Company / Founder Name"),
    ("global", "brand",   "founder_name",         "Solo Founder",                     "text", "Founder Job Title"),
    ("global", "brand",   "navbar_signin_text",   "Sign In",                          "text", "Navbar Sign-In Button Text"),
    ("global", "brand",   "navbar_cta_text",      "Start Free",                       "text", "Navbar CTA Button Text"),

    # Social URLs (single source of truth — used by Footer, Contact, etc.)
    ("global", "social",  "twitter_url",          "https://twitter.com/threadangle",          "url",  "Twitter / X Profile URL"),
    ("global", "social",  "linkedin_url",         "https://linkedin.com/company/threadangle", "url",  "LinkedIn Page URL"),
    ("global", "social",  "tiktok_url",           "https://tiktok.com/@threadangle",          "url",  "TikTok Profile URL"),
    ("global", "social",  "youtube_url",          "https://youtube.com/@threadangle",         "url",  "YouTube Channel URL"),

    # Footer
    ("global", "footer",  "footer_tagline",        "Find the angle. Go viral.",                                               "text",     "Footer Brand Tagline"),
    ("global", "footer",  "footer_description",    "Turn any content into viral Twitter threads, LinkedIn posts, and TikTok scripts in 20 seconds.", "textarea", "Footer Brand Description"),
    ("global", "footer",  "footer_copyright",      "© 2026 Kriangle. All rights reserved.",                                   "text",     "Footer Copyright Line"),
    ("global", "footer",  "footer_product_credit", "Threadangle is a product by Kriangle",                                    "text",     "Footer Product Credit Line"),
    ("global", "footer",  "footer_built_by",       "Built in public by Kriangle",                                             "text",     "Footer Built-By Note"),

    # ── SEO SETTINGS ─────────────────────────────────────────────────────────
    ("seo", "pages", "home_meta_title",        "Threadangle — Turn Any Content Into Viral Social Posts In Seconds",          "text",     "Home Page: <title>"),
    ("seo", "pages", "home_meta_description",  "Paste a blog post, YouTube link, or idea. Get Twitter threads, LinkedIn posts, TikTok scripts, Reels, and Shorts in ~20 seconds.", "textarea", "Home Page: meta description"),
    ("seo", "pages", "home_og_image",          "",                                                                           "url",      "Home Page: OG image URL"),

    ("seo", "pages", "pricing_meta_title",        "Pricing — Threadangle",                                                   "text",     "Pricing Page: <title>"),
    ("seo", "pages", "pricing_meta_description",  "Simple, transparent pricing. Start free with 5 generations. Upgrade anytime. No contracts.", "textarea", "Pricing Page: meta description"),
    ("seo", "pages", "pricing_og_image",          "",                                                                        "url",      "Pricing Page: OG image URL"),

    ("seo", "pages", "contact_meta_title",        "Contact — Threadangle",                                                   "text",     "Contact Page: <title>"),
    ("seo", "pages", "contact_meta_description",  "Get in touch with the Threadangle team. We reply within 24 hours.",       "textarea", "Contact Page: meta description"),
    ("seo", "pages", "contact_og_image",          "",                                                                        "url",      "Contact Page: OG image URL"),

    ("seo", "pages", "about_meta_title",          "About — Threadangle",                                                     "text",     "About Page: <title>"),
    ("seo", "pages", "about_meta_description",    "Threadangle is built by Kriangle to help creators turn content into viral social posts at scale.", "textarea", "About Page: meta description"),
    ("seo", "pages", "about_og_image",            "",                                                                        "url",      "About Page: OG image URL"),

    ("seo", "pages", "blog_meta_title",           "Blog — Threadangle",                                                      "text",     "Blog Page: <title>"),
    ("seo", "pages", "blog_meta_description",     "Tips and strategies for social media content creation, going viral, and growing your audience.", "textarea", "Blog Page: meta description"),
    ("seo", "pages", "blog_og_image",             "",                                                                        "url",      "Blog Page: OG image URL"),

    ("seo", "pages", "privacy_meta_title",        "Privacy Policy — Threadangle",                                           "text",     "Privacy Page: <title>"),
    ("seo", "pages", "privacy_meta_description",  "Learn how Threadangle collects, stores, and protects your data.",       "textarea", "Privacy Page: meta description"),
    ("seo", "pages", "terms_meta_title",          "Terms of Service — Threadangle",                                          "text",     "Terms Page: <title>"),
    ("seo", "pages", "terms_meta_description",    "Read the terms governing your use of Threadangle.",                     "textarea", "Terms Page: meta description"),

    # ── EMAIL SETTINGS / TEMPLATES ─────────────────────────────────────────
    ("email", "branding", "email_brand_name", "Threadangle", "text", "Email Brand Name"),
    ("email", "branding", "email_brand_tagline", "Find the angle. Go viral.", "text", "Email Brand Tagline"),
    ("email", "branding", "email_footer_links", "kriangle.com|https://kriangle.com,Contact Us|https://kriangle.com/contact,Pricing|https://kriangle.com/pricing", "textarea", "Footer Links (label|url comma-separated)"),
    ("email", "branding", "email_brand_credit", "Threadangle is a product by Kriangle · © 2026 Kriangle. All rights reserved.", "text", "Email Footer Brand Credit"),
    ("email", "subjects", "email_subject_welcome", "Your Threadangle account is ready ⚡", "text", "Welcome Email Subject"),
    ("email", "subjects", "email_subject_reset", "Reset your Threadangle password", "text", "Password Reset Subject"),
    ("email", "subjects", "email_subject_contact_auto", "We received your message — Threadangle", "text", "Contact Auto-reply Subject"),
    ("email", "subjects", "email_subject_admin_contact_prefix", "New Threadangle Contact:", "text", "Admin Contact Notification Subject Prefix"),
    ("email", "subjects", "email_subject_upgrade_template", "You are now on Threadangle {plan} ⚡", "text", "Upgrade Subject Template ({plan} supported)"),
    ("email", "subjects", "email_subject_subscription_confirmation", "🎉 You're now on Threadangle {plan}!", "text", "Subscription Confirmation Subject Template ({plan} supported)"),
    ("email", "subjects", "email_subject_cancellation", "Your Threadangle subscription has been cancelled", "text", "Cancellation Email Subject"),
    ("email", "subjects", "email_subject_usage_limit", "You've used all your free generations ⚡", "text", "Usage Limit Email Subject"),
    ("email", "subjects", "email_subject_voice_learned", "🎤 Threadangle has learned your voice!", "text", "Voice Learned Email Subject"),
    ("email", "subjects", "email_subject_auto_post_success", "✅ Your post went live!", "text", "Auto-post Success Subject"),
    ("email", "subjects", "email_subject_auto_post_failure", "⚠️ Auto-post partially failed", "text", "Auto-post Failure Subject"),

    ("email", "templates", "email_body_welcome", "", "textarea", "Welcome Email Body HTML (blank = built-in default)"),
    ("email", "templates", "email_body_reset", "", "textarea", "Password Reset Body HTML (use {reset_url}; blank = default)"),
    ("email", "templates", "email_body_contact_auto", "", "textarea", "Contact Auto-reply Body HTML (use {name},{subject_text})"),
    ("email", "templates", "email_body_admin_contact", "", "textarea", "Admin Contact Notification Body HTML (use {name},{user_email},{subject_text},{message_text},{timestamp})"),
    ("email", "templates", "email_body_upgrade_confirmation", "", "textarea", "Upgrade Confirmation Body HTML (use {plan_name},{amount},{next_billing_date})"),
    ("email", "templates", "email_body_subscription_confirmation", "", "textarea", "Subscription Confirmation Body HTML (use {plan_name},{generation_limit},{plan_emoji})"),
    ("email", "templates", "email_body_cancellation", "", "textarea", "Cancellation Body HTML (use {plan_name})"),
    ("email", "templates", "email_body_usage_limit", "", "textarea", "Usage Limit Body HTML (use {name})"),
    ("email", "templates", "email_body_voice_learned", "", "textarea", "Voice Learned Body HTML (use {display_name})"),
    ("email", "templates", "email_body_auto_post_success", "", "textarea", "Auto-post Success Body HTML (use {name_part},{platform_list},{content_preview})"),
    ("email", "templates", "email_body_auto_post_failure", "", "textarea", "Auto-post Failure Body HTML (use {name_part},{failed_platforms_html})"),

    ("email", "support", "email_support_address", "hello@kriangle.com", "text", "Support Email Address in Email Templates"),
    ("email", "support", "email_reply_note", "Questions? Reply to this email — we read every message personally.", "text", "Email Footer Reply Note"),

    # ── PLATFORM SETTINGS ────────────────────────────────────────────────────
    ("settings", "limits", "free_plan_limit",     "5",   "integer", "Free Plan: generation limit per period"),
    ("settings", "limits", "starter_plan_limit",  "30",  "integer", "Starter Plan: generation limit per period"),
    ("settings", "limits", "pro_plan_limit",      "100", "integer", "Pro Plan: generation limit per period"),

    ("settings", "features", "voice_learning_enabled",  "true",  "boolean", "Enable Voice Learning feature"),
    ("settings", "features", "scheduling_enabled",      "true",  "boolean", "Enable Content Scheduling feature"),
    ("settings", "features", "video_enabled",           "true",  "boolean", "Enable AI Video (Beta) feature"),
    ("settings", "features", "auto_posting_enabled",    "true",  "boolean", "Enable Auto-Posting feature"),
]
# fmt: on


def seed():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted, skipped = 0, 0
    for page, section, key, value, ctype, label in CMS_ENTRIES:
        # Only insert if key doesn't already have a value — don't overwrite admin edits
        cursor.execute("SELECT id, content_value FROM cms_content WHERE content_key = ?", (key,))
        existing = cursor.fetchone()
        if existing is None:
            cursor.execute(
                """INSERT INTO cms_content
                   (page, section, content_key, content_value, content_type, label, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                (page, section, key, value, ctype, label),
            )
            inserted += 1
        else:
            # Update label/section/type metadata even if value is unchanged
            cursor.execute(
                "UPDATE cms_content SET page=?, section=?, content_type=?, label=? WHERE content_key=?",
                (page, section, ctype, label, key),
            )
            skipped += 1

    conn.commit()
    conn.close()
    print(f"✅ CMS seed complete — {inserted} entries inserted, {skipped} already existed (values preserved)")


if __name__ == "__main__":
    seed()
