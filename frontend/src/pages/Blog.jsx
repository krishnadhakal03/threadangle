import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Blog = () => {
    const [posts, setPosts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [loading, setLoading] = useState(true);
    const [featuredPost, setFeaturedPost] = useState(null);
    const [email, setEmail] = useState('');
    const [subStatus, setSubStatus] = useState('idle'); // idle | loading | success | error
    const [subError, setSubError] = useState('');
    const [inputShake, setInputShake] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const [postsData, categoriesData] = await Promise.all([
                    api.getPosts(selectedCategory, null, 50),
                    api.getCategories()
                ]);

                setPosts(postsData);
                setCategories(categoriesData);

                if (postsData.length > 0) {
                    setFeaturedPost(postsData[0]);
                }
            } catch (err) {
                console.error('Failed to fetch blog data:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [selectedCategory]);

    const handleCategoryClick = (category) => {
        setSelectedCategory(category === selectedCategory ? null : category);
        setSearchQuery('');
    };

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    const handleSubscribe = async () => {
        setSubError('');
        if (!emailRegex.test(email)) {
            setSubError('Please enter a valid email address.');
            setInputShake(true);
            setTimeout(() => setInputShake(false), 600);
            return;
        }
        setSubStatus('loading');
        try {
            const res = await fetch(`${API_BASE}/api/newsletter/subscribe`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            const data = await res.json();
            if (data.success) {
                setSubStatus('success');
                setEmail('');
            } else {
                setSubStatus('idle');
                setSubError(data.message || 'Something went wrong. Try again.');
            }
        } catch {
            setSubStatus('idle');
            setSubError('Network error. Please try again.');
        }
    };

    const filteredPosts = posts.filter(post => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        return (
            post.title.toLowerCase().includes(q) ||
            post.excerpt.toLowerCase().includes(q) ||
            post.category.toLowerCase().includes(q)
        );
    });

    const displayedFeatured = !selectedCategory && !searchQuery && filteredPosts.length > 0 ? filteredPosts[0] : null;
    const gridPosts = displayedFeatured
        ? filteredPosts.filter(p => p.id !== displayedFeatured.id)
        : filteredPosts;

    return (
        <div className="min-h-screen bg-[#09090B] text-white font-sans selection:bg-accent/30 selection:text-white pb-20 block">
            <Navbar />
            {/* Blog Header */}
            <div className="pt-24 pb-16 px-6 relative overflow-hidden">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-gradient-to-b from-accent/10 to-transparent pointer-events-none opacity-50 blur-3xl"></div>
                <div className="max-w-4xl mx-auto text-center relative z-10">
                    <div className="inline-flex items-center gap-2 bg-accent/10 border border-accent/20 px-3 py-1 rounded-full text-[10px] font-bold text-accent uppercase tracking-widest mb-6 animate-in fade-in slide-in-from-top-4 duration-700">
                        Threadangle Blog
                    </div>
                    <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-500 leading-tight">
                        Find the angle.<br className="hidden md:block" /> Master the scroll.
                    </h1>
                    <p className="text-gray-400 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
                        Strategies, tips, and insights to help you transform any content into viral social posts and grow your audience.
                    </p>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6">
                {/* Search Bar */}
                <div className="max-w-xl mx-auto mb-8 relative">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        placeholder="Search articles..."
                        className="w-full bg-[#111113] border border-[#27272A] rounded-xl px-5 py-3.5 text-white placeholder:text-[#52525B] text-sm focus:outline-none focus:border-[#3B82F6] transition-all"
                    />
                    {searchQuery && (
                        <button
                            onClick={() => setSearchQuery('')}
                            className="absolute right-4 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white transition-colors text-lg leading-none"
                        >
                            ×
                        </button>
                    )}
                </div>

                {/* Categories */}
                <div className="flex flex-nowrap overflow-x-auto justify-center gap-3 mb-14 pb-2 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200 scrollbar-none">
                    <button
                        onClick={() => { setSelectedCategory(null); setSearchQuery(''); }}
                        className={`flex-shrink-0 px-5 py-2 rounded-full text-xs font-bold uppercase tracking-widest transition-all ${!selectedCategory ? 'bg-[#3B82F6] text-white shadow-lg shadow-[#3B82F6]/20' : 'bg-[#111113] border border-[#27272A] text-[#71717A] hover:text-[#A1A1AA]'}`}
                    >
                        All
                    </button>
                    {categories.map(cat => (
                        <button
                            key={cat.id}
                            onClick={() => handleCategoryClick(cat.name)}
                            className={`flex-shrink-0 px-5 py-2 rounded-full text-xs font-bold uppercase tracking-widest transition-all ${selectedCategory === cat.name ? 'bg-[#3B82F6] text-white shadow-lg shadow-[#3B82F6]/20' : 'bg-[#111113] border border-[#27272A] text-[#71717A] hover:text-[#A1A1AA]'}`}
                        >
                            {cat.name}
                        </button>
                    ))}
                </div>

                {loading ? (
                    <div className="flex flex-col items-center justify-center py-32 gap-6">
                        <div className="w-12 h-12 border-4 border-[#3B82F6] border-t-transparent rounded-full animate-spin"></div>
                        <p className="text-gray-500 font-bold uppercase tracking-widest animate-pulse">Loading amazing content...</p>
                    </div>
                ) : (
                    <>
                        {/* Featured Post */}
                        {displayedFeatured && (
                            <div className="mb-20 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
                                <Link to={`/blog/${displayedFeatured.slug}`} className="group relative flex flex-col md:flex-row bg-[#18181B] border border-[#27272A] rounded-[2.5rem] overflow-hidden hover:border-[#3B82F6]/30 transition-all hover:shadow-2xl hover:shadow-[#3B82F6]/5">
                                    <div className="w-full md:w-3/5 aspect-video md:aspect-[16/10] overflow-hidden">
                                        <img
                                            src={displayedFeatured.featured_image_url || "https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&q=80"}
                                            alt={displayedFeatured.title}
                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                                        />
                                    </div>
                                    <div className="w-full md:w-2/5 p-8 md:p-12 flex flex-col justify-center relative">
                                        <span className="absolute top-6 right-6 bg-[#3B82F6]/10 border border-[#3B82F6]/30 px-3 py-1 rounded-full text-[10px] font-black text-[#3B82F6] uppercase tracking-[0.2em]">
                                            FEATURED
                                        </span>
                                        <div className="flex items-center gap-3 mb-6">
                                            <span className="bg-[#3B82F6]/10 border border-[#3B82F6]/20 px-3 py-1 rounded-full text-[10px] font-bold text-[#3B82F6] uppercase tracking-widest">
                                                {displayedFeatured.category}
                                            </span>
                                        </div>
                                        <h2 className="text-2xl md:text-3xl font-bold mb-6 group-hover:text-[#3B82F6] transition-colors leading-tight line-clamp-4">
                                            {displayedFeatured.title}
                                        </h2>
                                        <p className="text-gray-400 text-base mb-8 line-clamp-4">
                                            {displayedFeatured.excerpt}
                                        </p>
                                        <div className="flex items-center justify-between mt-auto">
                                            <div className="flex items-center gap-4">
                                                <div className="w-10 h-10 bg-[#3B82F6]/20 rounded-full flex items-center justify-center font-bold text-[#3B82F6] italic">
                                                    {(displayedFeatured.author_name || 'T')[0]}
                                                </div>
                                                <div>
                                                    <p className="text-sm font-bold text-white">{displayedFeatured.author_name || 'Threadangle Team'}</p>
                                                    <p className="text-[10px] text-gray-500 font-bold uppercase">{displayedFeatured.read_time_minutes} min read</p>
                                                </div>
                                            </div>
                                            <span className="text-white font-bold group-hover:translate-x-2 transition-transform">Read →</span>
                                        </div>
                                    </div>
                                </Link>
                            </div>
                        )}

                        {/* Posts Grid */}
                        {gridPosts.length > 0 ? (
                            <div className="blog-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {gridPosts.map((post, idx) => (
                                    <Link
                                        key={post.id}
                                        to={`/blog/${post.slug}`}
                                        className="group flex flex-col bg-[#111113] border border-[#27272A] rounded-2xl overflow-hidden hover:border-[#3B82F6]/30 transition-all hover:translate-y-[-4px] hover:scale-[1.01] animate-in fade-in slide-in-from-bottom-8 duration-700"
                                        style={{ animationDelay: `${idx * 80}ms` }}
                                    >
                                        <div className="aspect-[16/10] overflow-hidden relative">
                                            <img
                                                src={post.featured_image_url || "https://images.unsplash.com/photo-1499750310107-5fef28a66643?auto=format&fit=crop&q=80"}
                                                alt={post.title}
                                                className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
                                            />
                                            <div className="absolute top-3 left-3 bg-[#09090B]/80 backdrop-blur-md px-3 py-1 rounded-full text-[9px] font-bold text-white uppercase tracking-[0.15em] border border-white/10">
                                                {post.category}
                                            </div>
                                        </div>
                                        <div className="p-6 flex flex-col flex-1">
                                            <h3 className="text-base font-semibold mb-3 group-hover:text-[#3B82F6] transition-colors line-clamp-2 leading-snug">
                                                {post.title}
                                            </h3>
                                            <p className="text-[#A1A1AA] text-sm mb-5 line-clamp-3 leading-relaxed">
                                                {post.excerpt}
                                            </p>
                                            <div className="flex items-center justify-between mt-auto pt-4 border-t border-[#27272A]">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-7 h-7 bg-[#3B82F6]/20 rounded-full flex items-center justify-center text-xs font-bold text-[#3B82F6]">
                                                        {(post.author_name || 'T')[0]}
                                                    </div>
                                                    <div>
                                                        <p className="text-[10px] font-bold text-white uppercase tracking-wider">{post.author_name || 'Threadangle Team'}</p>
                                                        <p className="text-[9px] text-[#71717A] font-bold">{post.read_time_minutes} min read</p>
                                                    </div>
                                                </div>
                                                <span className="text-xs font-bold text-[#3B82F6] group-hover:translate-x-1 transition-transform">Read →</span>
                                            </div>
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        ) : (
                            /* Improved Empty State */
                            <div className="flex flex-col items-center justify-center py-16">
                                <div className="w-full max-w-md bg-[#111113] border border-dashed border-[#27272A] rounded-xl px-10 py-16 text-center">
                                    <div className="text-5xl mb-6">📝</div>
                                    <h3 className="text-xl font-bold text-white mb-3">No posts in this category yet</h3>
                                    <p className="text-[#71717A] text-sm leading-relaxed mb-8">
                                        We are working on it. Check back soon or browse all posts.
                                    </p>
                                    <button
                                        onClick={() => { setSelectedCategory(null); setSearchQuery(''); }}
                                        className="bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white font-bold text-sm px-6 py-3 rounded-xl transition-all"
                                    >
                                        Browse All Posts
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Newsletter CTA */}
            <div className="max-w-7xl mx-auto px-6 mt-32">
                <div className="bg-[#3B82F6] rounded-[3rem] p-12 md:p-20 text-center relative overflow-hidden shadow-2xl shadow-[#3B82F6]/20">
                    <div className="absolute top-0 left-0 w-full h-full bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,0.05)_50%,transparent_75%)] bg-[length:50px_50px] opacity-20"></div>
                    <div className="relative z-10 max-w-2xl mx-auto">
                        <h2 className="text-[28px] font-bold text-white tracking-tight mb-6">Get the Viral Secret</h2>
                        <p className="text-white/80 text-lg md:text-xl mb-10 font-medium">
                            Weekly social media strategies delivered straight to your inbox. No fluff, just angles.
                        </p>
                        {subStatus === 'success' ? (
                            <p className="text-white text-lg font-medium">✅ You are in! Check your inbox for the first angle.</p>
                        ) : (
                            <>
                                <div className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={e => setEmail(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && handleSubscribe()}
                                        placeholder="your@email.com"
                                        disabled={subStatus === 'loading'}
                                        className={`flex-1 bg-white/10 border border-white/20 rounded-2xl px-6 py-4 text-white placeholder:text-white/40 focus:bg-white/20 outline-none transition-all disabled:opacity-60 ${inputShake ? 'input-shake' : ''}`}
                                    />
                                    <button
                                        onClick={handleSubscribe}
                                        disabled={subStatus === 'loading'}
                                        className="bg-[#09090B] text-[#FAFAFA] font-bold uppercase tracking-widest px-8 py-4 rounded-2xl hover:bg-[#18181B] transition-all disabled:opacity-60"
                                    >
                                        {subStatus === 'loading' ? 'Subscribing...' : 'Subscribe'}
                                    </button>
                                </div>
                                {subError && (
                                    <p className="text-red-300 text-sm mt-3">{subError}</p>
                                )}
                                <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)', marginTop: '8px', textAlign: 'center' }}>
                                    No spam. Unsubscribe anytime.
                                </p>
                            </>
                        )}
                    </div>
                </div>
            </div>

            <div className="mt-32">
                <Footer />
            </div>
        </div>
    );
};

export default Blog;
