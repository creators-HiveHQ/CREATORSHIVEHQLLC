import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog';
import { toast } from 'sonner';
import { 
  Sparkles, Brain, BarChart3, Zap, Shield, Users, 
  ChevronRight, Check, Star, ArrowRight, Copy, Share2,
  Twitter, Linkedin, MessageCircle, Play, ChevronDown
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const creatorTypes = [
  { id: 'youtuber', name: 'YouTuber', icon: '🎬' },
  { id: 'instagrammer', name: 'Instagram Creator', icon: '📸' },
  { id: 'tiktoker', name: 'TikToker', icon: '🎵' },
  { id: 'podcaster', name: 'Podcaster', icon: '🎙️' },
  { id: 'blogger', name: 'Blogger/Writer', icon: '✍️' },
  { id: 'streamer', name: 'Streamer', icon: '🎮' },
  { id: 'musician', name: 'Musician', icon: '🎸' },
  { id: 'artist', name: 'Visual Artist', icon: '🎨' },
  { id: 'educator', name: 'Educator/Coach', icon: '📚' },
  { id: 'business', name: 'Business Owner', icon: '💼' },
  { id: 'other', name: 'Other', icon: '✨' },
];

const features = [
  {
    icon: Brain,
    title: 'ARRIS AI Assistant',
    description: 'Your personal AI strategist that learns your style and provides tailored insights for content and business growth.',
    color: 'from-purple-500 to-indigo-500'
  },
  {
    icon: BarChart3,
    title: 'Smart Analytics',
    description: 'Pattern recognition engine that identifies trends, predicts opportunities, and automates your workflow.',
    color: 'from-blue-500 to-cyan-500'
  },
  {
    icon: Zap,
    title: 'Proposal Generator',
    description: 'Create professional brand proposals in minutes with AI-powered suggestions and insights.',
    color: 'from-amber-500 to-orange-500'
  },
  {
    icon: Shield,
    title: 'Multi-Brand Management',
    description: 'Manage multiple brand identities from one dashboard with separate analytics and personas.',
    color: 'from-green-500 to-emerald-500'
  },
  {
    icon: Users,
    title: 'Creator Network',
    description: 'Connect with brands, collaborate with other creators, and grow your professional network.',
    color: 'from-pink-500 to-rose-500'
  },
  {
    icon: Sparkles,
    title: 'Custom AI Personas',
    description: 'Create custom ARRIS personalities tailored to your brand voice and content style.',
    color: 'from-violet-500 to-purple-500'
  }
];

const pricingTiers = [
  {
    name: 'Starter',
    price: 19,
    description: 'Perfect for new creators',
    features: ['5 AI insights/month', 'Basic analytics', '1 brand profile', 'Email support'],
    popular: false
  },
  {
    name: 'Pro',
    price: 49,
    description: 'For growing creators',
    features: ['25 AI insights/month', 'Advanced analytics', '2 brand profiles', 'Priority support', 'Referral system'],
    popular: true
  },
  {
    name: 'Premium',
    price: 99,
    description: 'For professional creators',
    features: ['100 AI insights/month', 'Full analytics suite', '3 brand profiles', '24/7 support', 'API access'],
    popular: false
  },
  {
    name: 'Elite',
    price: 199,
    description: 'For agencies & top creators',
    features: ['Unlimited AI insights', 'Custom AI personas', '5 brand profiles', 'Dedicated manager', 'Full API access', 'White-label options'],
    popular: false
  }
];

const testimonials = [
  {
    name: 'Sarah M.',
    role: 'YouTube Creator',
    avatar: '👩‍🦰',
    content: 'ARRIS helped me identify the perfect posting schedule and content themes. My engagement increased by 340% in just 2 months!',
    rating: 5
  },
  {
    name: 'Marcus J.',
    role: 'Instagram Influencer',
    avatar: '👨‍🦱',
    content: 'The proposal generator saved me hours every week. I went from landing 1-2 brand deals to 5-6 monthly.',
    rating: 5
  },
  {
    name: 'Elena K.',
    role: 'Podcast Host',
    avatar: '👩',
    content: 'Managing multiple brands was a nightmare until I found Creators Hive. Now everything is organized in one place.',
    rating: 5
  }
];

const faqs = [
  {
    question: 'What is ARRIS AI?',
    answer: 'ARRIS is your AI-powered creative assistant that learns your style, analyzes your content performance, and provides personalized recommendations to grow your creator business.'
  },
  {
    question: 'How does the waitlist work?',
    answer: 'Sign up with your email and get a unique referral code. Share it with friends to earn priority points and move up the list. The more referrals, the sooner you get access!'
  },
  {
    question: 'Is my data safe?',
    answer: 'Absolutely. We use enterprise-grade encryption and never share your personal data with third parties. Your content insights are yours alone.'
  },
  {
    question: 'Can I manage multiple brands?',
    answer: 'Yes! Depending on your plan, you can manage 1-5 separate brand profiles, each with its own analytics, AI persona, and settings.'
  },
  {
    question: 'What platforms do you support?',
    answer: 'We support YouTube, Instagram, TikTok, Twitter, LinkedIn, Twitch, and more. Our AI can analyze content across all major platforms.'
  },
  {
    question: 'Do you offer a free trial?',
    answer: 'Early waitlist members will receive an extended free trial. Join now to secure your spot and get exclusive launch benefits!'
  }
];

export default function LandingPage() {
  const [showWaitlistModal, setShowWaitlistModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [waitlistData, setWaitlistData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedFaq, setExpandedFaq] = useState(null);
  const [stats, setStats] = useState({ total: 0 });
  
  // Form state
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    creatorType: '',
    niche: ''
  });

  // Get referral code from URL
  const urlParams = new URLSearchParams(window.location.search);
  const referralCode = urlParams.get('ref');

  const heroRef = useRef(null);
  const featuresRef = useRef(null);
  const pricingRef = useRef(null);

  useEffect(() => {
    // Fetch waitlist stats
    const fetchStats = async () => {
      try {
        const response = await fetch(`${API_URL}/api/waitlist/stats`);
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    };
    fetchStats();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.email || !formData.name || !formData.creatorType) {
      toast.error('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/waitlist/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          creator_type: formData.creatorType,
          referral_code: referralCode
        })
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        setWaitlistData(data);
        setShowWaitlistModal(false);
        setShowSuccessModal(true);
        toast.success('Welcome to the waitlist!');
      } else {
        toast.error(data.error || 'Failed to join waitlist');
        if (data.position) {
          setWaitlistData(data);
          setShowWaitlistModal(false);
          setShowSuccessModal(true);
        }
      }
    } catch (error) {
      toast.error('Something went wrong. Please try again.');
    }
    setLoading(false);
  };

  const copyReferralLink = () => {
    const link = `${window.location.origin}?ref=${waitlistData?.referral_code}`;
    navigator.clipboard.writeText(link);
    toast.success('Referral link copied!');
  };

  const shareOnTwitter = () => {
    const text = encodeURIComponent(`I just joined the @CreatorsHiveHQ waitlist! 🚀 Join me and get early access to AI-powered creator tools. Use my link:`);
    const url = encodeURIComponent(`${window.location.origin}?ref=${waitlistData?.referral_code}`);
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank');
  };

  const shareOnLinkedIn = () => {
    const url = encodeURIComponent(`${window.location.origin}?ref=${waitlistData?.referral_code}`);
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, '_blank');
  };

  const scrollToSection = (ref) => {
    ref.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#0a0a1a] text-white overflow-x-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-transparent to-indigo-900/20" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a1a]/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <span className="font-bold text-xl">Creators Hive HQ</span>
            </div>
            
            <div className="hidden md:flex items-center gap-8">
              <button onClick={() => scrollToSection(featuresRef)} className="text-gray-400 hover:text-white transition">Features</button>
              <button onClick={() => scrollToSection(pricingRef)} className="text-gray-400 hover:text-white transition">Pricing</button>
              <a href="/login" className="text-gray-400 hover:text-white transition">Login</a>
              <Button 
                onClick={() => setShowWaitlistModal(true)}
                className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
                data-testid="nav-join-waitlist"
              >
                Join Waitlist
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section ref={heroRef} className="relative z-10 pt-32 pb-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          {referralCode && (
            <Badge className="mb-6 bg-purple-500/20 text-purple-300 border-purple-500/30 py-1 px-4">
              You were referred by a friend! Join for priority access
            </Badge>
          )}
          
          <h1 className="text-4xl sm:text-5xl lg:text-7xl font-bold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-white via-purple-200 to-indigo-200 bg-clip-text text-transparent">
              Your AI-Powered
            </span>
            <br />
            <span className="bg-gradient-to-r from-purple-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Creator Command Center
            </span>
          </h1>
          
          <p className="text-lg sm:text-xl text-gray-400 max-w-3xl mx-auto mb-8">
            Meet ARRIS — your personal AI strategist that analyzes content, generates insights, 
            and helps you grow your creator business 10x faster.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12">
            <Button 
              size="lg"
              onClick={() => setShowWaitlistModal(true)}
              className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-lg px-8 py-6 rounded-xl shadow-lg shadow-purple-500/25"
              data-testid="hero-join-waitlist"
            >
              Join the Waitlist
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
            <Button 
              size="lg"
              variant="outline"
              className="border-gray-700 hover:bg-gray-800/50 text-lg px-8 py-6 rounded-xl"
            >
              <Play className="mr-2 h-5 w-5" />
              Watch Demo
            </Button>
          </div>
          
          <div className="flex items-center justify-center gap-8 text-sm text-gray-400">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-purple-400" />
              <span><strong className="text-white">{stats.total || '1,000+' }</strong> creators on waitlist</span>
            </div>
            <div className="flex items-center gap-2">
              <Star className="h-4 w-4 text-yellow-400" />
              <span><strong className="text-white">4.9/5</strong> early tester rating</span>
            </div>
          </div>
        </div>

        {/* Hero Image/Preview */}
        <div className="max-w-6xl mx-auto mt-16 px-4">
          <div className="relative rounded-2xl overflow-hidden border border-purple-500/20 shadow-2xl shadow-purple-500/10">
            <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a1a] via-transparent to-transparent z-10" />
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 p-4 sm:p-8">
              {/* Mock Dashboard Preview */}
              <div className="bg-gray-900/80 rounded-xl p-6 border border-gray-700">
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center">
                    <Brain className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">ARRIS AI</h3>
                    <p className="text-sm text-gray-400">Analyzing your content patterns...</p>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="bg-gray-800/50 rounded-lg p-4 border border-purple-500/20">
                    <p className="text-purple-300 text-sm mb-2">🎯 Content Insight</p>
                    <p className="text-gray-300">Your tech review videos perform 2.3x better when posted on Tuesdays at 4 PM. Consider scheduling your next upload then!</p>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-gray-800/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-white">+340%</p>
                      <p className="text-xs text-gray-400">Engagement</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-white">12</p>
                      <p className="text-xs text-gray-400">Brand Deals</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-4 text-center">
                      <p className="text-2xl font-bold text-white">$24K</p>
                      <p className="text-xs text-gray-400">Revenue</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section ref={featuresRef} className="relative z-10 py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-purple-500/20 text-purple-300 border-purple-500/30">Features</Badge>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Everything You Need to <span className="text-purple-400">Succeed</span>
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Powerful tools designed specifically for content creators who want to level up their game.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => (
              <Card 
                key={idx}
                className="bg-gray-900/50 border-gray-800 hover:border-purple-500/30 transition-all duration-300 group"
              >
                <CardContent className="p-6">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                    <feature.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
                  <p className="text-gray-400">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ARRIS Demo Section */}
      <section className="relative z-10 py-20 px-4 bg-gradient-to-b from-transparent via-purple-900/10 to-transparent">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <Badge className="mb-4 bg-purple-500/20 text-purple-300 border-purple-500/30">Meet ARRIS</Badge>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6">
                Your Personal <span className="text-purple-400">AI Strategist</span>
              </h2>
              <p className="text-gray-400 text-lg mb-8">
                ARRIS learns your unique style, analyzes your content performance, and provides 
                personalized recommendations that actually work.
              </p>
              
              <div className="space-y-4">
                {[
                  'Analyzes content patterns across all platforms',
                  'Predicts optimal posting times for maximum reach',
                  'Generates brand proposal drafts in minutes',
                  'Identifies trending topics in your niche',
                  'Creates custom AI personas for your brand'
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center">
                      <Check className="h-4 w-4 text-purple-400" />
                    </div>
                    <span className="text-gray-300">{item}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/20 to-indigo-500/20 rounded-3xl blur-3xl" />
              <Card className="relative bg-gray-900/80 border-purple-500/20 overflow-hidden">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-6 pb-4 border-b border-gray-700">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center">
                      <Brain className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <p className="font-semibold text-white">ARRIS</p>
                      <p className="text-xs text-gray-400">AI Assistant</p>
                    </div>
                    <Badge className="ml-auto bg-green-500/20 text-green-400 border-green-500/30">Online</Badge>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex justify-end">
                      <div className="bg-purple-500/20 rounded-2xl rounded-tr-none p-4 max-w-[80%]">
                        <p className="text-gray-200">What content should I create this week?</p>
                      </div>
                    </div>
                    
                    <div className="flex">
                      <div className="bg-gray-800 rounded-2xl rounded-tl-none p-4 max-w-[80%]">
                        <p className="text-gray-200 mb-3">
                          Based on your analytics, I recommend focusing on these topics:
                        </p>
                        <ul className="space-y-2 text-sm">
                          <li className="flex items-center gap-2">
                            <span className="text-purple-400">1.</span>
                            <span className="text-gray-300">AI tools comparison (trending +45%)</span>
                          </li>
                          <li className="flex items-center gap-2">
                            <span className="text-purple-400">2.</span>
                            <span className="text-gray-300">Behind-the-scenes content (high engagement)</span>
                          </li>
                          <li className="flex items-center gap-2">
                            <span className="text-purple-400">3.</span>
                            <span className="text-gray-300">Q&A with your audience (builds loyalty)</span>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section ref={pricingRef} className="relative z-10 py-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-purple-500/20 text-purple-300 border-purple-500/30">Pricing</Badge>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Plans for Every <span className="text-purple-400">Creator</span>
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Start free, upgrade as you grow. All plans include core ARRIS features.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {pricingTiers.map((tier, idx) => (
              <Card 
                key={idx}
                className={`relative bg-gray-900/50 border-gray-800 ${
                  tier.popular ? 'border-purple-500 ring-2 ring-purple-500/20' : ''
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-purple-500 text-white border-0">Most Popular</Badge>
                  </div>
                )}
                <CardContent className="p-6">
                  <h3 className="text-xl font-semibold text-white mb-2">{tier.name}</h3>
                  <p className="text-sm text-gray-400 mb-4">{tier.description}</p>
                  <div className="mb-6">
                    <span className="text-4xl font-bold text-white">${tier.price}</span>
                    <span className="text-gray-400">/month</span>
                  </div>
                  <ul className="space-y-3 mb-6">
                    {tier.features.map((feature, fidx) => (
                      <li key={fidx} className="flex items-center gap-2 text-sm">
                        <Check className="h-4 w-4 text-purple-400 flex-shrink-0" />
                        <span className="text-gray-300">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button 
                    className={`w-full ${
                      tier.popular 
                        ? 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700' 
                        : 'bg-gray-800 hover:bg-gray-700'
                    }`}
                    onClick={() => setShowWaitlistModal(true)}
                  >
                    Join Waitlist
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="relative z-10 py-20 px-4 bg-gradient-to-b from-transparent via-purple-900/10 to-transparent">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-purple-500/20 text-purple-300 border-purple-500/30">Testimonials</Badge>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Loved by <span className="text-purple-400">Creators</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((testimonial, idx) => (
              <Card key={idx} className="bg-gray-900/50 border-gray-800">
                <CardContent className="p-6">
                  <div className="flex items-center gap-1 mb-4">
                    {[...Array(testimonial.rating)].map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <p className="text-gray-300 mb-6 italic">&ldquo;{testimonial.content}&rdquo;</p>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center text-xl">
                      {testimonial.avatar}
                    </div>
                    <div>
                      <p className="font-semibold text-white">{testimonial.name}</p>
                      <p className="text-sm text-gray-400">{testimonial.role}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="relative z-10 py-20 px-4">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-purple-500/20 text-purple-300 border-purple-500/30">FAQ</Badge>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Frequently Asked <span className="text-purple-400">Questions</span>
            </h2>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, idx) => (
              <div 
                key={idx}
                className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden"
              >
                <button
                  className="w-full p-6 text-left flex items-center justify-between"
                  onClick={() => setExpandedFaq(expandedFaq === idx ? null : idx)}
                >
                  <span className="font-semibold text-white">{faq.question}</span>
                  <ChevronDown className={`h-5 w-5 text-gray-400 transition-transform ${
                    expandedFaq === idx ? 'rotate-180' : ''
                  }`} />
                </button>
                {expandedFaq === idx && (
                  <div className="px-6 pb-6">
                    <p className="text-gray-400">{faq.answer}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-br from-purple-900/40 to-indigo-900/40 rounded-3xl p-8 sm:p-12 border border-purple-500/20">
            <h2 className="text-3xl sm:text-4xl font-bold mb-4">
              Ready to <span className="text-purple-400">Transform</span> Your Creator Journey?
            </h2>
            <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
              Join thousands of creators already on the waitlist. Get early access, exclusive benefits, 
              and be the first to experience ARRIS.
            </p>
            <Button 
              size="lg"
              onClick={() => setShowWaitlistModal(true)}
              className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-lg px-8 py-6 rounded-xl"
              data-testid="cta-join-waitlist"
            >
              Join the Waitlist Now
              <ChevronRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-12 px-4 border-t border-gray-800">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
                <span className="font-bold text-xl">Creators Hive HQ</span>
              </div>
              <p className="text-gray-400 text-sm">
                AI-powered tools for the next generation of content creators.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#features" className="hover:text-white transition">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition">Roadmap</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition">About</a></li>
                <li><a href="#" className="hover:text-white transition">Blog</a></li>
                <li><a href="#" className="hover:text-white transition">Careers</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition">Privacy</a></li>
                <li><a href="#" className="hover:text-white transition">Terms</a></li>
              </ul>
            </div>
          </div>
          
          <div className="pt-8 border-t border-gray-800 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-gray-400">
              © 2025 Creators Hive HQ. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="text-gray-400 hover:text-white transition">
                <Twitter className="h-5 w-5" />
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition">
                <Linkedin className="h-5 w-5" />
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* Waitlist Modal */}
      <Dialog open={showWaitlistModal} onOpenChange={setShowWaitlistModal}>
        <DialogContent className="bg-gray-900 border-gray-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-2xl text-white">Join the Waitlist</DialogTitle>
            <DialogDescription className="text-gray-400">
              Get early access and exclusive benefits. Share your link to move up the list!
            </DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Full Name *</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="John Doe"
                className="bg-gray-800 border-gray-700"
                data-testid="waitlist-name"
                required
              />
            </div>
            
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Email *</label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                placeholder="john@example.com"
                className="bg-gray-800 border-gray-700"
                data-testid="waitlist-email"
                required
              />
            </div>
            
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Creator Type *</label>
              <Select
                value={formData.creatorType}
                onValueChange={(value) => setFormData(prev => ({ ...prev, creatorType: value }))}
              >
                <SelectTrigger className="bg-gray-800 border-gray-700" data-testid="waitlist-type">
                  <SelectValue placeholder="Select your creator type" />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  {creatorTypes.map((type) => (
                    <SelectItem key={type.id} value={type.id}>
                      {type.icon} {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Your Niche (optional)</label>
              <Input
                value={formData.niche}
                onChange={(e) => setFormData(prev => ({ ...prev, niche: e.target.value }))}
                placeholder="e.g., Tech reviews, Fitness, Cooking"
                className="bg-gray-800 border-gray-700"
                data-testid="waitlist-niche"
              />
            </div>
            
            <Button 
              type="submit" 
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
              data-testid="waitlist-submit"
            >
              {loading ? 'Joining...' : 'Join Waitlist'}
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* Success Modal */}
      <Dialog open={showSuccessModal} onOpenChange={setShowSuccessModal}>
        <DialogContent className="bg-gray-900 border-gray-800 max-w-md">
          <DialogHeader>
            <DialogTitle className="text-2xl text-white text-center">
              🎉 You are In!
            </DialogTitle>
          </DialogHeader>
          
          <div className="text-center py-6">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl font-bold">#{waitlistData?.position || '?'}</span>
            </div>
            <p className="text-gray-400 mb-6">
              You are #{waitlistData?.position} on the waitlist. Share your link to move up!
            </p>
            
            <div className="bg-gray-800 rounded-lg p-4 mb-6">
              <p className="text-sm text-gray-400 mb-2">Your Referral Code</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-gray-900 px-4 py-2 rounded text-purple-400 font-mono">
                  {waitlistData?.referral_code}
                </code>
                <Button variant="ghost" size="sm" onClick={copyReferralLink}>
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            <p className="text-sm text-gray-400 mb-4">Share to earn priority points:</p>
            <div className="flex items-center justify-center gap-4">
              <Button variant="outline" size="sm" onClick={shareOnTwitter}>
                <Twitter className="h-4 w-4 mr-2" />
                Twitter
              </Button>
              <Button variant="outline" size="sm" onClick={shareOnLinkedIn}>
                <Linkedin className="h-4 w-4 mr-2" />
                LinkedIn
              </Button>
              <Button variant="outline" size="sm" onClick={copyReferralLink}>
                <Share2 className="h-4 w-4 mr-2" />
                Copy Link
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
