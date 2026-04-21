import { useCMS } from '../hooks/useCMS';
import { useSEO } from '../hooks/useSEO';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

export default function TermsOfService() {
  const { content } = useCMS('terms', {
    terms_title: 'Terms of Service — Threadangle',
    terms_last_updated: 'Last updated: March 2026',
    terms_sections: [
      { heading: 'Acceptance of Terms', body: 'By accessing or using Threadangle, you agree to be bound by these Terms of Service. If you disagree with any part of the terms, you do not have permission to access the Service.' },
      { heading: 'Description of Service', body: 'Threadangle is an AI content generation tool that transforms URLs and text inputs into formatted social media posts and scripts for various platforms.' },
      { heading: 'Free and Paid Plans', body: 'We offer a free tier that includes 5 content generations. To unlock additional generation capabilities and access to advanced features, users must subscribe to one of our paid plans.' },
      { heading: 'Acceptable Use', body: 'You agree not to use the Service to generate spam, malicious content, illegal material, or to violate the rights of others. Reselling API access or utilizing automated scripts to systematically harvest data or bypass generation limits is strictly prohibited.' },
      { heading: 'Content Ownership', body: 'You retain all ownership rights to the content you generate using Threadangle. We do not claim any proprietary rights over the text or ideas you produce through the Service.' },
      { heading: 'Payment Terms', body: 'Paid subscriptions are billed on a monthly basis. You may cancel your subscription at any time, and the cancellation will take effect at the end of the current billing cycle. We do not offer refunds or credits for partial months of service.' },
      { heading: 'Limitation of Liability', body: 'In no event shall Threadangle, its directors, employees, or partners be liable for any indirect, incidental, special, consequential or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting from your access to or use of or inability to access or use the Service.' },
      { heading: 'Changes to Terms', body: 'We reserve the right to modify or replace these Terms at any time. If a revision is material, we will provide at least 30 days notice prior to any new terms taking effect.' },
      { heading: 'Contact', body: 'If you have any questions about these Terms, please contact us at hello@kriangle.com.' }
    ]
  });
  const { content: seo } = useCMS('seo', {
    terms_meta_title: 'Terms of Service — Threadangle',
    terms_meta_description: 'Read the terms governing your use of Threadangle.'
  });

  useSEO({ title: seo.terms_meta_title, description: seo.terms_meta_description });
  const sections = Array.isArray(content.terms_sections) ? content.terms_sections : [];

  return (
    <div className="min-h-screen bg-dark text-white font-sans selection:bg-accent/30 selection:text-white pb-20">
      <Navbar />
      <div className="max-w-[720px] mx-auto pt-20 px-6">
        <h1 className="text-4xl font-bold mb-2">{content.terms_title}</h1>
        <p className="text-gray-400 text-sm mb-12">{content.terms_last_updated}</p>

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
