import { useCMS } from '../hooks/useCMS';
import { useSEO } from '../hooks/useSEO';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function PrivacyPolicy() {
  const { content } = useCMS('privacy', {
    privacy_title: 'Privacy Policy — Threadangle',
    privacy_last_updated: 'Last updated: March 2026',
    privacy_sections: [
      { heading: 'Information We Collect', body: 'We collect information that you provide directly to us, such as when you create an account, update your profile, use our services, or communicate with us. This includes your email address, basic usage data, and payment information handled securely via Stripe.' },
      { heading: 'How We Use Your Information', body: 'We use the information we collect to provide, maintain, and improve our services, communicate with you (such as sending essential account emails), and personalize your experience with Threadangle.' },
      { heading: 'Data Storage', body: 'All user data is stored securely on encrypted AWS servers. We implement appropriate technical and organizational measures to protect the security of your personal information against unauthorized access or disclosure.' },
      { heading: 'Third Party Services', body: 'We use trusted third-party services to operate Threadangle: Stripe for secure payment processing, Anthropic for AI content generation, and Zoho for transactional email delivery. These services handle your data in accordance with their own privacy policies.' },
      { heading: 'Cookies', body: 'We use minimal cookies on our website. Cookies are utilized exclusively for essential authentication purposes to keep you securely logged into your account during your session. We do not use tracking or advertising cookies.' },
      { heading: 'Your Rights', body: 'You have the right to access, update, delete, or export your personal data at any time. If you wish to exercise any of these rights, please contact us directly at our support email.' },
      { heading: 'Contact', body: 'If you have any questions or concerns about this Privacy Policy or how we handle your data, please contact us at hello@kriangle.com.' }
    ]
  });
  const { content: seo } = useCMS('seo', {
    privacy_meta_title: 'Privacy Policy — Threadangle',
    privacy_meta_description: 'Learn how Threadangle collects, stores, and protects your data.'
  });

  useSEO({ title: seo.privacy_meta_title, description: seo.privacy_meta_description });
  const sections = Array.isArray(content.privacy_sections) ? content.privacy_sections : [];

  return (
    <div className="min-h-screen bg-dark text-white font-sans selection:bg-accent/30 selection:text-white pb-20">
      <Navbar />
      <div className="max-w-[720px] mx-auto pt-20 px-6">
        <h1 className="text-4xl font-bold mb-2">{content.privacy_title}</h1>
        <p className="text-gray-400 text-sm mb-12">{content.privacy_last_updated}</p>

        {sections.map((section, index) => (
          <div key={`${section.heading}-${index}`}>
            <h2 className="text-2xl font-semibold mt-8 mb-4">{section.heading}</h2>
            <p className="text-gray-300 mb-6 leading-relaxed whitespace-pre-wrap">{section.body}</p>
          </div>
        ))}
      </div>
      <Footer />
    </div>
  );
}
