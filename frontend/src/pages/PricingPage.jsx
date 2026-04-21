import React from 'react';
import Pricing from '../components/Pricing';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const PricingPage = () => {
  return (
    <div className="min-h-screen bg-[#09090B] text-white font-sans selection:bg-accent/30 selection:text-white block">
      <Navbar />
      <div className="pt-16 pb-20">
        <Pricing />
      </div>
      <Footer />
    </div>
  );
};

export default PricingPage;
