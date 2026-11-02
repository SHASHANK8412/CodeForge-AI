import React from 'react';
import Navbar from '../components/landing/Navbar';
import Hero from '../components/landing/Hero';
import ProductPreview from '../components/landing/ProductPreview';
import Features from '../components/landing/Features';
import HowItWorks from '../components/landing/HowItWorks';
import Architecture from '../components/landing/Architecture';
import WhyAIForge from '../components/landing/WhyAIForge';
import Technology from '../components/landing/Technology';
import CTA from '../components/landing/CTA';
import Footer from '../components/landing/Footer';

export default function LandingPage({ setView }) {
  const handleStartBuilding = () => {
    if (setView) {
      setView('mission-control');
    } else {
      window.location.href = '/mission-control';
    }
  };

  const handleLaunchMission = (missionText) => {
    if (setView) {
      setView('ai-os');
    } else {
      window.location.href = '/ai-os';
    }
  };

  const handleScrollToArchitecture = () => {
    const el = document.getElementById('architecture');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleScrollToFeatures = () => {
    const el = document.getElementById('features');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 font-sans selection:bg-cyan-500 selection:text-white">
      <Navbar onStartBuilding={handleStartBuilding} />
      <Hero 
        onStartBuilding={handleStartBuilding} 
        onScrollToArchitecture={handleScrollToArchitecture} 
        onLaunchMission={handleLaunchMission}
      />
      <ProductPreview />
      <Features />
      <HowItWorks />
      <Architecture />
      <WhyAIForge />
      <Technology />
      <CTA onStartBuilding={handleStartBuilding} onExplore={handleScrollToFeatures} />
      <Footer />
    </div>
  );
}
