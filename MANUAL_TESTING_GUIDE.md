# Threadangle Manual Testing Guide

This guide outlines the manual testing procedures for the Threadangle application to ensure a smooth user experience from landing to conversion.

## 1. Authentication Flow
- **Signup:**
    - Navigate to `/signup`.
    - Try signing up with a short password (<8 chars) → *Expect: Error message.*
    - Sign up with a valid email/password → *Expect: Redirect to dashboard.*
- **Login:**
    - Logout and navigate to `/login`.
    - Login with wrong password → *Expect: Error message.*
    - Login with correct credentials → *Expect: Redirect to dashboard.*
- **Session Persistence:**
    - Refresh the dashboard page → *Expect: User remains logged in.*

## 2. Public SEO Hook Generator
- **Accessibility:**
    - Navigate to `/free-hook-generator` (while logged out).
- **Functionality:**
    - Enter a topic (e.g., "AI for Business") and select a category.
    - Click "Generate 5 Hooks" → *Expect: Loading state then 5 hook cards.*
- **Rate Limiting:**
    - Generate hooks 3 times in a row.
    - On the 4th attempt → *Expect: "Too many requests" or similar message.*
- **Conversion:**
    - Click "Unlock Premium Features" button → *Expect: Redirect to signup.*

## 3. Core Content Generation (Dashboard)
- **Text Input:**
    - Enter a long paragraph of text.
    - Select "Viral" tone and "Twitter" platform.
    - Click "Generate" → *Expect: AI output card for Twitter.*
- **URL Input:**
    - Enter a blog post URL (e.g., `https://example.com/some-article`).
    - Select "Professional" tone and "LinkedIn" platform.
    - Click "Generate" → *Expect: Success message and LinkedIn output card.*
- **Multi-Platform:**
    - Select "LinkedIn", "Twitter", and "TikTok".
    - Click "Generate" → *Expect: Output for all three platforms.*

## 4. History Management
- **Persistence:**
    - Go to the "History" page.
    - Verify your recent generations appear in the list.
- **Viewing Details:**
    - Click on a history item → *Expect: Detailed view of generated content.*

## 5. Subscription & Payment (Simulated)
- **Pricing:**
    - Go to the "Pricing" page.
    - Click "Upgrade" on the Pro plan.
- **Stripe Checkout:**
    - *Expect: Redirect to Stripe checkout page.*
- **Cancel Flow:**
    - Click "Back" on the Stripe page → *Expect: Return to Threadangle with no plan change.*

## 6. Footer & Brand Assets
- **Attribution:**
    - Scroll to the bottom of any page.
    - Verify: "Threadangle is a product by Kriangle" is present and styled correctly.

---
*Last Updated: March 2026*

## 7. SESSION 11 FEATURES (NEW)

### FAQ Section
- **Location**: Landing Page (bottom)
- **Steps**: Scroll to bottom. Click FAQ items. Ensure only one opens at a time.

### Onboarding Flow
- **Location**: Post-signup
- **Steps**: Sign up with a new email. 3-step modal should appear. Step 2: "Generate" should actually call API and show output in Step 3.

### Welcome Email
- **Steps**: Sign up. Check logs. Backend should log "Sending welcome email to...".

### Password Reset
- **Location**: /forgot-password
- **Steps**: Enter email. Check logs for reset token link. Go to /reset-password?token=... and reset. Login with new password.

### Contact Us
- **Location**: `/contact`
- **Steps**: Fill form. Try sending with message < 20 chars (should error). Send valid message. Check `contacts` table in DB. Try sending 4 times within 1 hour from same IP (4th should 429).

### Email Branding & Flow
- **Welcome Email**: Sign up with a real email and verify welcome email arrives with correct branding.
- **Contact Auto-reply**: Submit contact form and verify auto-reply arrives.
- **Stripe Upgrade**: Complete a Stripe test upgrade and verify upgrade confirmation email arrives.
- **Mobile Check**: Check all emails look correct in Gmail on mobile.
- **Branding Check**: Verify all emails show "Threadangle is a product by Kriangle" in footer.

### Admin Panel (Advanced)
- **Location**: `/admin`
- **Tabs**:
    - **Overview**: Verify stats (Users, Generations, Contacts) and recent activity feed.
    - **Content**: 
        - Select a page (e.g., "Home").
        - Edit a field (e.g., Hero Headline).
        - Click "Save Changes" → *Expect: Loading state and success message.*
        - Verify change on public page.
    - **Blog**:
        - **Create**: Click "+ Create New Post". Fill title, content, and category. Click "Publish".
        - **Verify**: Check `/blog` listing page for the new post. View full article at `/blog/[slug]`.
        - **Edit**: Click "Edit" on an existing post, change title, and update.
        - **Delete**: Click "Delete" and confirm → *Expect: Post removed from list.*

### Blog & SEO
- **Landing Page**: Verify "Latest from the Blog" section shows 3 most recent posts.
- **Blog Listing**: Test category filters.
- **Blog Post**:
    - Verify dynamic title in browser tab.
    - Verify "Related Posts" section at bottom.
- **SEO Assets**:
    - Visit `/robots.txt` → *Expect: Valid text file.*
    - Visit `/sitemap.xml` → *Expect: Valid XML listing pages.*
    - Visit `/api/blog/rss.xml` (Backend) → *Expect: Valid RSS XML feed.*

---
*Last Updated: March 2026*

## 8. LANDING PAGE REVAMP & STYLING
- **Hero Section**: 
    - Go to `/`. Verify that the login form card is gone and replaced by the primary "Start Free — No Credit Card Required" button and secondary "Sign In" link.
- **Navbar & Navigation**: 
    - The new navbar should be sticky at the top, blurring the background on scroll.
    - Check that the links to Features (#features), Pricing (#pricing), Free Tools (/free-hook-generator), Blog (/blog), and Contact (/contact) are functional.
    - Verify that resizing the window to mobile width collapses the navbar into a hamburger menu, and toggling it displays the dropdown perfectly.
- **New Footer**: 
    - Scroll to the bottom of any page to check the new 4-column footer.
    - Verify the copyright line is clean: "Threadangle is a product by Kriangle · © 2026 Kriangle. All rights reserved."
- **Legal Pages**:
    - Visit `/privacy` and ensure the Privacy Policy page renders the content without markdown errors.
    - Visit `/terms` and ensure the Terms of Service page renders correctly.
    - Verify footer links point to these new legal pages.
- **FAQ Section**: 
    - Verify the updated visual style on the Landing page FAQ (subtle border, distinct dark background `#111113`, generous padding, and the specific "GOT QUESTIONS?" label).
