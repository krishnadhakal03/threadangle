import React from 'react';
import { Link } from 'react-router-dom';
import ThreadangleLogo from './ThreadangleLogo';
import { useCMS } from '../hooks/useCMS';

export default function Footer() {
  const { content } = useCMS('global', {
    footer_tagline: 'Find the angle. Go viral.',
    footer_description: 'Turn any content into viral Twitter threads, LinkedIn posts, and TikTok scripts in 20 seconds.',
    footer_copyright: '© 2026 Kriangle. All rights reserved.',
    footer_product_credit: 'Threadangle is a product by Kriangle',
    footer_built_by: 'Built in public by Kriangle',
    twitter_url: 'https://twitter.com/threadangle',
    linkedin_url: 'https://linkedin.com/company/threadangle',
    tiktok_url: 'https://tiktok.com/@threadangle',
  });

  return (
    <footer className="bg-[#09090B] pt-[64px] pb-[40px] px-6 border-t border-[#1C1C1F]">
      <div className="max-w-6xl mx-auto">
        {/* Main Footer Columns */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 text-center md:text-left mb-16">
          
          {/* Column 1 - Brand */}
          <div className="flex flex-col items-center md:items-start space-y-4">
            <Link to="/" className="flex items-center">
              <ThreadangleLogo size={28} showText={true} textSize={16} />
            </Link>
            <p style={{ color: '#D4D4D8', fontSize: '14px', fontWeight: 500 }}>{content.footer_tagline}</p>
            <p style={{ color: '#A1A1AA', fontSize: '14px', lineHeight: 1.6 }} className="max-w-xs md:max-w-[200px]">
              {content.footer_description}
            </p>
          </div>

          {/* Column 2 - Product */}
          <div className="flex flex-col items-center md:items-start space-y-4">
            <h4 style={{ color: '#71717A', fontSize: '11px', letterSpacing: '2px', fontWeight: 600 }} className="uppercase mb-2">PRODUCT</h4>
            <Link to="/dashboard" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">Dashboard</Link>
            <Link to="/pricing" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">Pricing</Link>
            <Link to="/demo" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">Interactive Demo</Link>
            <Link to="/blog" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">Blog</Link>
          </div>

          {/* Column 3 - Company */}
          <div className="flex flex-col items-center md:items-start space-y-4">
            <h4 style={{ color: '#71717A', fontSize: '11px', letterSpacing: '2px', fontWeight: 600 }} className="uppercase mb-2">COMPANY</h4>
            <Link to="/about" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">About</Link>
            <Link to="/contact" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">Contact</Link>
            <Link to="/privacy" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">Privacy Policy</Link>
            <Link to="/terms" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">Terms of Service</Link>
          </div>

          {/* Column 4 - Connect */}
          <div className="flex flex-col items-center md:items-start space-y-4">
            <h4 style={{ color: '#71717A', fontSize: '11px', letterSpacing: '2px', fontWeight: 600 }} className="uppercase mb-2">CONNECT</h4>
            <a href={content.twitter_url} target="_blank" rel="noopener noreferrer" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">Twitter / X</a>
            <a href={content.linkedin_url} target="_blank" rel="noopener noreferrer" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">LinkedIn</a>
            <a href={content.tiktok_url} target="_blank" rel="noopener noreferrer" style={{ color: '#A1A1AA', transition: 'color 0.15s' }} className="text-sm hover:text-[#FAFAFA]">TikTok</a>
            <p style={{ color: '#52525B', fontSize: '11px', letterSpacing: '1.5px' }} className="uppercase mt-4">{content.footer_built_by}</p>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="border-t border-[#27272A] pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p style={{ color: '#6B7280', fontSize: '13px' }}>
            {content.footer_copyright}
          </p>
          <p style={{ color: '#6B7280', fontSize: '13px' }}>
            {content.footer_product_credit}
          </p>
        </div>

      </div>
    </footer>
  );
}
