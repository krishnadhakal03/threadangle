import React, { useState, useEffect } from 'react';
import { useParams, Navigate, Link } from 'react-router-dom';
import { api } from '../utils/api';
import { useCMS } from '../hooks/useCMS';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import SignupModal from '../components/SignupModal';
import SocialPlatformIcon from '../components/SocialPlatformIcon';

const BlogPost = () => {
    const { slug } = useParams();
    const [post, setPost] = useState(null);
    const [relatedPosts, setRelatedPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const [readProgress, setReadProgress] = useState(0);
    const [showMidCTA, setShowMidCTA] = useState(false);
    const [midCTADismissed, setMidCTADismissed] = useState(false);
    const [copied, setCopied] = useState(false);
    const [nlEmail, setNlEmail] = useState('');
    const [nlSubStatus, setNlSubStatus] = useState('idle'); // idle | loading | success | error
    const [nlSubError, setNlSubError] = useState('');
    const [nlInputShake, setNlInputShake] = useState(false);
    const [showSignupModal, setShowSignupModal] = useState(false);

    const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    const handleNlSubscribe = async () => {
        setNlSubError('');
        if (!emailRegex.test(nlEmail)) {
            setNlSubError('Please enter a valid email address.');
            setNlInputShake(true);
            setTimeout(() => setNlInputShake(false), 600);
            return;
        }
        setNlSubStatus('loading');
        try {
            const res = await fetch(`${API_BASE}/api/newsletter/subscribe`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: nlEmail }),
            });
            const data = await res.json();
            if (data.success) {
                setNlSubStatus('success');
                setNlEmail('');
            } else {
                setNlSubStatus('idle');
                setNlSubError(data.message || 'Something went wrong. Try again.');
            }
        } catch {
            setNlSubStatus('idle');
            setNlSubError('Network error. Please try again.');
        }
    };

    const { content } = useCMS('global', {
        footer_product_credit: "Threadangle is a product by Kriangle"
    });

    useEffect(() => {
        const fetchPost = async () => {
            setLoading(true);
            setError(false);
            try {
                const data = await api.getPost(slug);
                if (!data) {
                    setError(true);
                    return;
                }
                setPost(data);

                // Fetch related posts: all posts, filter out current, prefer same category
                try {
                    const allPosts = await api.getPosts(null, null, 50);
                    const related = allPosts
                        .filter(p => p.slug !== slug)
                        .sort((a, b) => (b.category === data.category ? 1 : 0) - (a.category === data.category ? 1 : 0))
                        .slice(0, 3);
                    setRelatedPosts(related);
                } catch (e) {
                    console.error('Failed to fetch related posts:', e);
                }

                // Update SEO metadata
                if (data.meta_title) document.title = data.meta_title;
                const metaDesc = document.querySelector('meta[name="description"]');
                if (metaDesc && data.meta_description) {
                    metaDesc.setAttribute('content', data.meta_description);
                }
            } catch (err) {
                console.error("Failed to fetch post:", err);
                setError(true);
            } finally {
                setLoading(false);
            }
        };
        fetchPost();
        
        // Scroll to top on load
        window.scrollTo(0, 0);
    }, [slug]);

    useEffect(() => {
        const handleScroll = () => {
            const total = document.body.scrollHeight - window.innerHeight;
            if (total <= 0) return;
            const progress = (window.scrollY / total) * 100;
            setReadProgress(Math.min(progress, 100));
            if (progress > 35) setShowMidCTA(true);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen bg-dark flex flex-col items-center justify-center text-white gap-6">
                <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
                <p className="text-gray-500 font-bold uppercase tracking-widest">Reading post...</p>
            </div>
        );
    }

    if (error || !post) {
        return <Navigate to="/blog" />;
    }

    return (
        <div className="min-h-screen bg-[#09090B] text-white font-sans selection:bg-accent/30 selection:text-white block pb-20">
            <Navbar />

            {/* Reading Progress Bar */}
            <div style={{ position: 'fixed', top: '64px', left: 0, right: 0, height: '3px', background: '#27272A', zIndex: 99 }}>
                <div style={{ height: '100%', background: '#3B82F6', width: `${readProgress}%`, transition: 'width 0.1s ease' }} />
            </div>

            {/* Breadcrumb */}
            <nav style={{ padding: '16px 0', borderBottom: '1px solid #1C1C1F', marginBottom: '0' }}>
                <div style={{ maxWidth: '760px', margin: '0 auto', padding: '0 24px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', color: '#71717A' }}>
                    <Link to="/" style={{ color: '#71717A', textDecoration: 'none' }} onMouseOver={e => e.currentTarget.style.color='#FAFAFA'} onMouseOut={e => e.currentTarget.style.color='#71717A'}>Home</Link>
                    <span>›</span>
                    <Link to="/blog" style={{ color: '#71717A', textDecoration: 'none' }} onMouseOver={e => e.currentTarget.style.color='#FAFAFA'} onMouseOut={e => e.currentTarget.style.color='#71717A'}>Blog</Link>
                    <span>›</span>
                    <span style={{ color: '#A1A1AA' }}>{post?.title}</span>
                </div>
            </nav>
            {/* Article Header */}
            <header className="pt-24 pb-16 px-6 relative">
                <div className="max-w-4xl mx-auto">
                    <div className="flex items-center gap-4 mb-8 animate-in fade-in slide-in-from-top-4 duration-700">
                        <span className="bg-accent/10 border border-accent/20 px-3 py-1 rounded-full text-[10px] font-bold text-accent uppercase tracking-widest">
                            {post.category}
                        </span>
                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">
                            {post.read_time_minutes} min read
                        </span>
                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">
                            {post.views} views
                        </span>
                    </div>
                    <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight mb-8 leading-tight animate-in fade-in slide-in-from-top-4 duration-700 delay-100">
                        {post.title}
                    </h1>
                    <div className="flex items-center gap-4 animate-in fade-in duration-700 delay-200">
                        <div className="w-12 h-12 bg-accent/20 rounded-full flex items-center justify-center font-bold text-accent italic text-xl">
                            {(post.author_name || 'T')[0]}
                        </div>
                        <div>
                            <p className="text-sm font-bold text-white uppercase tracking-widest">{post.author_name || 'Threadangle Team'}</p>
                            <p className="text-xs text-gray-500 font-medium">Published on {new Date(post.published_at).toLocaleDateString()}</p>
                        </div>
                    </div>
                </div>
            </header>

            {/* Featured Image */}
            <div className="max-w-6xl mx-auto px-6 mb-16 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
                <div className="aspect-[21/9] rounded-[2.5rem] overflow-hidden border border-border/50 shadow-2xl">
                    <img 
                        src={post.featured_image_url || "https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&q=80"} 
                        alt={post.title}
                        className="w-full h-full object-cover"
                    />
                </div>
            </div>

            {/* Article Content */}
            <div className="max-w-4xl mx-auto px-6 relative">
                <article className="prose prose-invert prose-lg max-w-none">
                    <p className="text-xl md:text-2xl text-gray-400 font-medium leading-relaxed italic border-l-4 border-accent pl-8 mb-12">
                        {post.excerpt}
                    </p>
                    
                    <div 
                        className="text-gray-300 leading-[1.8] space-y-8 text-lg blog-content"
                        dangerouslySetInnerHTML={{ __html: post.content }}
                    />
                </article>

                {/* Tags */}
                {post.tags && post.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-16 pt-8 border-t border-border/10">
                        {String(post.tags).split(',').map(tag => tag.trim()).filter(Boolean).map(tag => (
                            <span key={tag} className="px-4 py-1.5 rounded-full bg-card/50 border border-border/50 text-xs font-bold text-gray-500 uppercase tracking-widest">
                                #{tag}
                            </span>
                        ))}
                    </div>
                )}

                {/* Social Share */}
                <div className="mt-12">
                    <p style={{ fontSize: '13px', color: '#71717A', marginBottom: '12px' }}>Found this useful? Share it.</p>
                    <div className="flex flex-wrap gap-3">
                        <a
                            href={`https://twitter.com/intent/tweet?text=${encodeURIComponent(`${post?.title} via @threadangle`)}&url=${encodeURIComponent(window.location.href)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#18181B', border: '1px solid #27272A', borderRadius: '999px', padding: '8px 16px', fontSize: '14px', color: '#FAFAFA', textDecoration: 'none', transition: 'border-color 0.15s' }}
                            onMouseOver={e => e.currentTarget.style.borderColor='#3B82F6'}
                            onMouseOut={e => e.currentTarget.style.borderColor='#27272A'}
                        >
                            🐦 Share on Twitter
                        </a>
                        <a
                            href={`https://linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.href)}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#18181B', border: '1px solid #27272A', borderRadius: '999px', padding: '8px 16px', fontSize: '14px', color: '#FAFAFA', textDecoration: 'none', transition: 'border-color 0.15s' }}
                            onMouseOver={e => e.currentTarget.style.borderColor='#3B82F6'}
                            onMouseOut={e => e.currentTarget.style.borderColor='#27272A'}
                        >
                            <SocialPlatformIcon platform="linkedin" className="w-4 h-4" /> Share on LinkedIn
                        </a>
                        <button
                            onClick={() => { navigator.clipboard.writeText(window.location.href); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
                            style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#18181B', border: '1px solid #27272A', borderRadius: '999px', padding: '8px 16px', fontSize: '14px', color: '#FAFAFA', cursor: 'pointer', transition: 'border-color 0.15s' }}
                            onMouseOver={e => e.currentTarget.style.borderColor='#3B82F6'}
                            onMouseOut={e => e.currentTarget.style.borderColor='#27272A'}
                        >
                            🔗 {copied ? 'Copied!' : 'Copy Link'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Related Posts */}
            {relatedPosts.length > 0 && (
                <div className="max-w-7xl mx-auto px-6 mt-16">
                    <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#FAFAFA', marginBottom: '24px' }}>Continue Reading</h2>
                    <div className="flex gap-6 overflow-x-auto pb-4 md:grid md:grid-cols-3 md:overflow-x-visible scrollbar-none">
                        {relatedPosts.map(p => (
                            <Link 
                                key={p.id} 
                                to={`/blog/${p.slug}`}
                                className="group flex-shrink-0 w-[280px] md:w-auto flex flex-col bg-[#111113] border border-[#27272A] rounded-2xl overflow-hidden hover:border-[#3B82F6]/30 transition-all"
                            >
                                <div className="aspect-[16/10] overflow-hidden">
                                    <img 
                                        src={p.featured_image_url || "https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&q=80"} 
                                        alt={p.title}
                                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                    />
                                </div>
                                <div className="p-5 flex flex-col flex-1">
                                    <span className="text-[10px] font-bold text-[#3B82F6] uppercase tracking-widest mb-2">{p.category}</span>
                                    <h3 className="text-sm font-semibold mb-2 group-hover:text-[#3B82F6] transition-colors line-clamp-2 leading-snug">{p.title}</h3>
                                    <p className="text-[#71717A] text-xs line-clamp-2 mb-3 leading-relaxed">{p.excerpt}</p>
                                    <div className="flex items-center justify-between mt-auto pt-3 border-t border-[#27272A]">
                                        <span className="text-[10px] text-[#52525B] font-bold uppercase">{p.read_time_minutes} min read</span>
                                        <span className="text-xs font-bold text-[#3B82F6] group-hover:translate-x-1 transition-transform">Read →</span>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>
                </div>
            )}

            {/* Newsletter CTA */}
            <div className="max-w-4xl mx-auto px-6 mt-16">
                <div className="bg-card/30 border border-border/50 rounded-[2.5rem] p-10 md:p-16 relative overflow-hidden text-center">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-accent/5 rounded-full blur-3xl -mr-32 -mt-32"></div>
                    <div className="relative z-10">
                        <h2 className="text-3xl font-bold mb-6 tracking-tight">Master the viral angle</h2>
                        <p className="text-gray-400 mb-10 max-w-lg mx-auto">
                            Join creators getting weekly angles straight to their inbox.
                        </p>
                        {nlSubStatus === 'success' ? (
                            <p className="text-green-400 font-medium text-lg">✅ You're in! Check your inbox.</p>
                        ) : (
                            <>
                                <div className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
                                    <input
                                        type="email"
                                        value={nlEmail}
                                        onChange={e => setNlEmail(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && handleNlSubscribe()}
                                        placeholder="your@email.com"
                                        disabled={nlSubStatus === 'loading'}
                                        className={`flex-1 bg-dark/60 border border-border rounded-xl px-5 py-3.5 text-white outline-none focus:border-accent transition-all disabled:opacity-60 ${nlInputShake ? 'input-shake' : ''}`}
                                    />
                                    <button
                                        onClick={handleNlSubscribe}
                                        disabled={nlSubStatus === 'loading'}
                                        className="bg-accent text-white font-bold px-8 py-3.5 rounded-xl hover:bg-accent/90 transition-all shadow-lg shadow-accent/20 disabled:opacity-60"
                                    >
                                        {nlSubStatus === 'loading' ? 'Subscribing…' : 'Get Weekly Tips →'}
                                    </button>
                                </div>
                                {nlSubError && (
                                    <p className="text-red-400 text-sm mt-3">{nlSubError}</p>
                                )}
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* Footer */}
            <div className="mt-24">
                <Footer />
            </div>

            {/* Mid-Article Sticky CTA Banner */}
            {showMidCTA && !midCTADismissed && (
                <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, background: '#1e3a5f', borderTop: '1px solid #2563EB', padding: '14px 24px', zIndex: 50, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
                    <p style={{ color: '#FAFAFA', fontSize: '15px', fontWeight: 500, margin: 0 }}>⚡ Generate your own posts like this in 20 seconds →</p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <button onClick={() => setShowSignupModal(true)} style={{ background: '#3B82F6', color: '#FAFAFA', fontWeight: 700, fontSize: '13px', padding: '8px 18px', borderRadius: '8px', border: 'none', cursor: 'pointer', whiteSpace: 'nowrap' }}>Try Free</button>
                        <button onClick={() => setMidCTADismissed(true)} style={{ background: 'none', border: 'none', color: '#A1A1AA', fontSize: '20px', cursor: 'pointer', lineHeight: 1, padding: '0 4px' }} aria-label="Dismiss">×</button>
                    </div>
                </div>
            )}

            <SignupModal isOpen={showSignupModal} onClose={() => setShowSignupModal(false)} />

            <style dangerouslySetInnerHTML={{ __html: `
                .blog-content h2 { font-size: 24px; font-weight: 700; color: #FAFAFA; margin: 32px 0 16px; line-height: 1.3; }
                .blog-content h3 { font-size: 20px; font-weight: 600; color: #FAFAFA; margin: 24px 0 12px; }
                .blog-content p { font-size: 16px; color: #A1A1AA; line-height: 1.8; margin-bottom: 16px; }
                .blog-content ul, .blog-content ol { margin: 16px 0 16px 24px; color: #A1A1AA; }
                .blog-content li { font-size: 16px; line-height: 1.7; margin-bottom: 8px; }
                .blog-content strong { color: #FAFAFA; font-weight: 600; }
                .blog-content a { color: #3B82F6; text-decoration: underline; }
                .blog-content blockquote { border-left: 3px solid #3B82F6; padding: 12px 20px; background: #18181B; border-radius: 0 8px 8px 0; margin: 24px 0; }
                .blog-content table { width: 100%; border-collapse: collapse; margin: 24px 0; }
                .blog-content th { background: #18181B; color: #FAFAFA; padding: 12px; text-align: left; border: 1px solid #27272A; }
                .blog-content td { padding: 12px; border: 1px solid #27272A; color: #A1A1AA; }
            `}} />
        </div>
    );
};

export default BlogPost;
