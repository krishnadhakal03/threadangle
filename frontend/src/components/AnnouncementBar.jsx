import React, { useState, useEffect } from 'react';
import { useCMS } from '../hooks/useCMS';

export default function AnnouncementBar() {
    const { content } = useCMS('global', {
        announcement_bar_enabled: false,
        announcement_bar_text: "",
        announcement_bar_link: "#",
        announcement_bar_color: "#3B82F6"
    });

    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        if (content.announcement_bar_enabled) {
            // Check session storage to see if user dismissed it
            const dismissed = sessionStorage.getItem('announcement_dismissed');
            if (!dismissed) {
                setIsVisible(true);
            }
        } else {
            setIsVisible(false);
        }
    }, [content.announcement_bar_enabled]);

    const handleDismiss = () => {
        setIsVisible(false);
        sessionStorage.setItem('announcement_dismissed', 'true');
    };

    if (!isVisible) return null;

    return (
        <div 
            className="relative z-50 text-white py-2 px-4 text-center text-sm font-bold flex items-center justify-center gap-4 transition-all animate-in slide-in-from-top duration-500"
            style={{ backgroundColor: content.announcement_bar_color }}
        >
            <a href={content.announcement_bar_link} className="hover:underline flex items-center gap-2">
                {content.announcement_bar_text}
                <span className="text-[10px] bg-white/20 px-2 py-0.5 rounded uppercase tracking-widest">Details →</span>
            </a>
            <button 
                onClick={handleDismiss}
                className="absolute right-4 hover:bg-black/10 rounded-full w-6 h-6 flex items-center justify-center transition-colors"
                title="Dismiss"
            >
                ✕
            </button>
        </div>
    );
}
