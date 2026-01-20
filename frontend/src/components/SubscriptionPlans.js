/**
 * Creator Subscription Page
 * Self-Funding Loop - Subscription plans and checkout flow
 */

import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useCreatorAuth } from "@/components/CreatorDashboard";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ============== PRICING PAGE ==============

export const SubscriptionPlans = () => {
  const { creator, isAuthenticated } = useCreatorAuth();
  const [plans, setPlans] = useState([]);
  const [currentStatus, setCurrentStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(null);
  const [billingCycle, setBillingCycle] = useState("monthly");
  const navigate = useNavigate();
  
  // Elite Contact Form State
  const [showContactModal, setShowContactModal] = useState(false);
  const [contactForm, setContactForm] = useState({
    message: "",
    company_name: "",
    team_size: ""
  });
  const [contactSubmitting, setContactSubmitting] = useState(false);
  const [contactSuccess, setContactSuccess] = useState(false);
  const [contactError, setContactError] = useState("");

  const getAuthHeaders = () => {
    const token = localStorage.getItem("creator_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch plans (public)
      const plansRes = await axios.get(`${API}/subscriptions/plans`);
      setPlans(plansRes.data.plans);
      
      // Fetch current status if authenticated
      if (isAuthenticated) {
        const headers = getAuthHeaders();
        const statusRes = await axios.get(`${API}/subscriptions/my-status`, { headers });
        setCurrentStatus(statusRes.data);
      }
    } catch (error) {
      console.error("Error fetching subscription data:", error);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSubscribe = async (planId) => {
    if (!isAuthenticated) {
      navigate("/creator/login");
      return;
    }

    setCheckoutLoading(planId);
    
    try {
      const headers = getAuthHeaders();
      const response = await axios.post(
        `${API}/subscriptions/checkout`,
        {
          plan_id: planId,
          origin_url: window.location.origin
        },
        { headers }
      );
      
      // Redirect to Stripe Checkout
      window.location.href = response.data.checkout_url;
      
    } catch (error) {
      console.error("Checkout error:", error);
      alert(error.response?.data?.detail || "Failed to start checkout");
    } finally {
      setCheckoutLoading(null);
    }
  };

  const getFilteredPlans = () => {
    return plans.filter(plan => {
      if (plan.plan_id === "free") return true;
      if (plan.plan_id === "elite") return true; // Always show Elite
      return plan.billing_cycle === billingCycle;
    });
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case "starter": return "bg-blue-500";
      case "pro": return "bg-purple-500";
      case "premium": return "bg-amber-500";
      case "elite": return "bg-gradient-to-r from-amber-500 to-orange-500";
      default: return "bg-slate-400";
    }
  };

  const handleContactUs = () => {
    if (!isAuthenticated) {
      alert("Please log in to contact us about Elite plan");
      navigate("/creator/login");
      return;
    }
    setShowContactModal(true);
    setContactSuccess(false);
    setContactError("");
  };

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    
    if (!contactForm.message.trim()) {
      setContactError("Please enter a message");
      return;
    }
    
    setContactSubmitting(true);
    setContactError("");
    
    try {
      const headers = getAuthHeaders();
      await axios.post(`${API}/elite/contact`, contactForm, { headers });
      
      setContactSuccess(true);
      setContactForm({ message: "", company_name: "", team_size: "" });
      
      // Close modal after 3 seconds
      setTimeout(() => {
        setShowContactModal(false);
        setContactSuccess(false);
      }, 3000);
      
    } catch (error) {
      console.error("Contact form error:", error);
      setContactError(error.response?.data?.detail || "Failed to submit inquiry. Please try again.");
    } finally {
      setContactSubmitting(false);
    }
  };

  const handleOldContactUs = () => {
    // Open email or contact form
    window.location.href = "mailto:sales@hivehq.com?subject=Elite Plan Inquiry";
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-purple-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900" data-testid="subscription-page">
      {/* Header */}
      <div className="text-center pt-16 pb-8 px-4">
        <Badge className="bg-purple-500 mb-4">Self-Funding Loop</Badge>
        <h1 className="text-4xl font-bold text-white mb-4">Choose Your Plan</h1>
        <p className="text-purple-200 max-w-2xl mx-auto">
          Unlock ARRIS AI insights, priority review, and advanced features to supercharge your creator journey.
        </p>
        
        {/* Billing Toggle */}
        <div className="flex items-center justify-center gap-4 mt-8">
          <button
            onClick={() => setBillingCycle("monthly")}
            className={`px-4 py-2 rounded-lg transition-all ${
              billingCycle === "monthly"
                ? "bg-white text-purple-900 font-medium"
                : "text-purple-200 hover:text-white"
            }`}
            data-testid="toggle-monthly"
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle("annual")}
            className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
              billingCycle === "annual"
                ? "bg-white text-purple-900 font-medium"
                : "text-purple-200 hover:text-white"
            }`}
            data-testid="toggle-annual"
          >
            Annual
            <Badge className="bg-green-500 text-xs">Save ~17%</Badge>
          </button>
        </div>
      </div>

      {/* Current Status Banner */}
      {currentStatus && (
        <div className="max-w-4xl mx-auto px-4 mb-8">
          <Card className="bg-white/10 border-white/20 text-white">
            <CardContent className="py-4 flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm">Current Plan</p>
                <p className="font-medium capitalize">{currentStatus.tier} {currentStatus.has_subscription && `• ${currentStatus.status}`}</p>
              </div>
              <div className="text-right">
                <p className="text-purple-200 text-sm">Proposals Used</p>
                <p className="font-medium">
                  {currentStatus.proposals_used} / {currentStatus.proposal_limit === -1 ? "∞" : currentStatus.proposal_limit}
                </p>
              </div>
              {currentStatus.current_period_end && (
                <div className="text-right">
                  <p className="text-purple-200 text-sm">Renews</p>
                  <p className="font-medium">{new Date(currentStatus.current_period_end).toLocaleDateString()}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Plans Grid */}
      <div className="max-w-6xl mx-auto px-4 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {getFilteredPlans().map((plan) => (
            <Card
              key={plan.plan_id}
              className={`relative overflow-hidden ${
                plan.is_popular ? "ring-2 ring-purple-500 scale-105 z-10" : ""
              } ${plan.is_custom ? "ring-2 ring-amber-400" : ""}
              ${currentStatus?.plan_id === plan.plan_id ? "ring-2 ring-green-500" : ""}`}
              data-testid={`plan-card-${plan.plan_id}`}
            >
              {plan.is_popular && (
                <div className="absolute top-0 right-0 bg-purple-500 text-white text-xs px-3 py-1 rounded-bl-lg">
                  Most Popular
                </div>
              )}
              {plan.is_custom && (
                <div className="absolute top-0 right-0 bg-amber-500 text-white text-xs px-3 py-1 rounded-bl-lg">
                  Custom
                </div>
              )}
              {currentStatus?.plan_id === plan.plan_id && (
                <div className="absolute top-0 left-0 bg-green-500 text-white text-xs px-3 py-1 rounded-br-lg">
                  Current
                </div>
              )}
              
              <CardHeader className="text-center pb-2">
                <Badge className={`${getTierColor(plan.tier)} w-fit mx-auto mb-2`}>
                  {plan.tier.toUpperCase()}
                </Badge>
                <CardTitle className="text-xl">{plan.name.replace(" Monthly", "").replace(" Annual", "")}</CardTitle>
                <div className="mt-4">
                  {plan.is_custom ? (
                    <span className="text-2xl font-bold">Custom</span>
                  ) : (
                    <>
                      <span className="text-3xl font-bold">${plan.price.toFixed(2)}</span>
                      {plan.price > 0 && (
                        <span className="text-slate-500 text-sm">/{billingCycle === "annual" ? "yr" : "mo"}</span>
                      )}
                    </>
                  )}
                </div>
                {plan.monthly_equivalent && (
                  <p className="text-xs text-green-600 mt-1">
                    ${plan.monthly_equivalent.toFixed(2)}/mo • Save ${plan.savings.toFixed(2)}
                  </p>
                )}
                <CardDescription className="mt-2 text-xs">{plan.description}</CardDescription>
              </CardHeader>
              
              <CardContent className="pt-2">
                <ul className="space-y-2 mb-4 text-xs">
                  {/* Proposals per month */}
                  <li className="flex items-center gap-2">
                    <span className="text-green-500">✓</span>
                    {plan.features.proposals_per_month === -1 ? "Unlimited" : plan.features.proposals_per_month} Proposals/mo
                  </li>
                  
                  {/* ARRIS Insights Level */}
                  <li className="flex items-center gap-2">
                    <span className={plan.features.arris_insights !== "none" ? "text-green-500" : "text-slate-300"}>
                      {plan.features.arris_insights !== "none" ? "✓" : "✗"}
                    </span>
                    {plan.features.arris_insights === "full" ? "Full ARRIS Insights" :
                     plan.features.arris_insights === "summary_strengths" ? "Summary + Strengths" :
                     plan.features.arris_insights === "summary_only" ? "Summary Only" : "No ARRIS"}
                  </li>
                  
                  {/* Priority Review */}
                  <li className="flex items-center gap-2">
                    <span className={plan.features.priority_review ? "text-green-500" : "text-slate-300"}>
                      {plan.features.priority_review ? "✓" : "✗"}
                    </span>
                    Priority Review
                  </li>
                  
                  {/* Dashboard Level */}
                  <li className="flex items-center gap-2">
                    <span className={plan.features.dashboard_level !== "basic" ? "text-green-500" : "text-slate-300"}>
                      {plan.features.dashboard_level !== "basic" ? "✓" : "✗"}
                    </span>
                    {plan.features.dashboard_level === "custom" ? "Custom Dashboard" :
                     plan.features.dashboard_level === "advanced" ? "Advanced Dashboard" : "Basic Dashboard"}
                  </li>
                  
                  {/* Advanced Analytics (Premium+) */}
                  {plan.features.advanced_analytics && (
                    <li className="flex items-center gap-2">
                      <span className="text-green-500">✓</span>
                      Advanced Analytics
                    </li>
                  )}
                  
                  {/* ARRIS Processing Speed */}
                  {plan.features.arris_processing_speed === "fast" && (
                    <li className="flex items-center gap-2">
                      <span className="text-amber-500">⚡</span>
                      <span className="font-medium text-amber-700">Fast ARRIS Processing</span>
                    </li>
                  )}
                  
                  {/* Support Level */}
                  <li className="flex items-center gap-2">
                    <span className="text-blue-500">📧</span>
                    {plan.features.support_level === "dedicated" ? "Dedicated Support" :
                     plan.features.support_level === "priority" ? "Priority Support" : 
                     plan.features.support_level === "email" ? "Email Support" : "Community"}
                  </li>
                  
                  {/* API Access */}
                  {plan.features.api_access && (
                    <li className="flex items-center gap-2">
                      <span className="text-green-500">✓</span>
                      API Access
                    </li>
                  )}
                  
                  {/* Brand Integrations (Elite) */}
                  {plan.features.brand_integrations && (
                    <li className="flex items-center gap-2">
                      <span className="text-green-500">✓</span>
                      Brand Integrations
                    </li>
                  )}
                  
                  {/* High Touch Onboarding (Elite) */}
                  {plan.features.high_touch_onboarding && (
                    <li className="flex items-center gap-2">
                      <span className="text-green-500">✓</span>
                      High-Touch Onboarding
                    </li>
                  )}
                </ul>
                
                {plan.is_custom ? (
                  <Button
                    className="w-full bg-amber-500 hover:bg-amber-600"
                    onClick={handleContactUs}
                    data-testid={`contact-btn-${plan.plan_id}`}
                  >
                    Contact Us
                  </Button>
                ) : (
                  <Button
                    className={`w-full ${
                      plan.plan_id === "free" 
                        ? "bg-slate-200 text-slate-700 hover:bg-slate-300" 
                        : plan.is_popular 
                          ? "bg-purple-600 hover:bg-purple-700" 
                          : "bg-slate-800 hover:bg-slate-700"
                    }`}
                    disabled={
                      currentStatus?.plan_id === plan.plan_id || 
                      plan.plan_id === "free" ||
                      checkoutLoading === plan.plan_id
                    }
                    onClick={() => handleSubscribe(plan.plan_id)}
                    data-testid={`subscribe-btn-${plan.plan_id}`}
                  >
                    {checkoutLoading === plan.plan_id ? (
                      "Processing..."
                    ) : currentStatus?.plan_id === plan.plan_id ? (
                      "Current"
                    ) : plan.plan_id === "free" ? (
                      "Free"
                    ) : (
                      `Get ${plan.name.replace(" Monthly", "").replace(" Annual", "")}`
                    )}
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Back to Dashboard */}
      {isAuthenticated && (
        <div className="text-center pb-16">
          <Button
            variant="outline"
            className="border-white/30 text-white hover:bg-white/10"
            onClick={() => navigate("/creator/dashboard")}
            data-testid="back-to-dashboard"
          >
            ← Back to Dashboard
          </Button>
        </div>
      )}
    </div>
  );
};

// ============== CHECKOUT SUCCESS PAGE ==============

export const SubscriptionSuccess = () => {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const [status, setStatus] = useState("checking");
  const [checkoutData, setCheckoutData] = useState(null);
  const [pollCount, setPollCount] = useState(0);
  const navigate = useNavigate();

  const getAuthHeaders = () => {
    const token = localStorage.getItem("creator_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  useEffect(() => {
    if (!sessionId) {
      setStatus("error");
      return;
    }

    const checkStatus = async () => {
      try {
        const headers = getAuthHeaders();
        const response = await axios.get(
          `${API}/subscriptions/checkout/status/${sessionId}`,
          { headers }
        );
        
        setCheckoutData(response.data);
        
        if (response.data.payment_status === "paid") {
          setStatus("success");
        } else if (response.data.status === "expired") {
          setStatus("expired");
        } else {
          // Continue polling
          if (pollCount < 5) {
            setPollCount(prev => prev + 1);
            setTimeout(checkStatus, 2000);
          } else {
            setStatus("pending");
          }
        }
      } catch (error) {
        console.error("Status check error:", error);
        setStatus("error");
      }
    };

    checkStatus();
  }, [sessionId, pollCount]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4" data-testid="subscription-success">
      <Card className="w-full max-w-md">
        <CardContent className="pt-8 text-center">
          {status === "checking" && (
            <>
              <div className="mx-auto w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center animate-pulse mb-4">
                <span className="text-3xl">💳</span>
              </div>
              <h2 className="text-xl font-bold mb-2">Processing Payment...</h2>
              <p className="text-slate-500 mb-4">Please wait while we confirm your subscription.</p>
              <Progress value={(pollCount / 5) * 100} className="w-48 mx-auto" />
            </>
          )}
          
          {status === "success" && (
            <>
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <span className="text-3xl">✅</span>
              </div>
              <h2 className="text-xl font-bold text-green-600 mb-2">Subscription Activated!</h2>
              <p className="text-slate-500 mb-4">
                Thank you! Your subscription is now active and you have access to all premium features.
              </p>
              {checkoutData && (
                <div className="bg-slate-50 p-4 rounded-lg mb-6 text-left">
                  <p className="text-sm text-slate-500">Amount Paid</p>
                  <p className="font-bold text-lg">${checkoutData.amount} {checkoutData.currency?.toUpperCase()}</p>
                </div>
              )}
              <Button
                className="w-full bg-purple-600 hover:bg-purple-700"
                onClick={() => navigate("/creator/dashboard")}
                data-testid="go-to-dashboard"
              >
                Go to Dashboard
              </Button>
            </>
          )}
          
          {status === "expired" && (
            <>
              <div className="mx-auto w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mb-4">
                <span className="text-3xl">⏰</span>
              </div>
              <h2 className="text-xl font-bold text-amber-600 mb-2">Session Expired</h2>
              <p className="text-slate-500 mb-4">
                Your checkout session has expired. Please try again.
              </p>
              <Button
                className="w-full"
                onClick={() => navigate("/creator/subscription")}
              >
                Try Again
              </Button>
            </>
          )}
          
          {status === "pending" && (
            <>
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <span className="text-3xl">⏳</span>
              </div>
              <h2 className="text-xl font-bold text-blue-600 mb-2">Payment Processing</h2>
              <p className="text-slate-500 mb-4">
                Your payment is being processed. This may take a few moments.
              </p>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => window.location.reload()}
              >
                Refresh Status
              </Button>
            </>
          )}
          
          {status === "error" && (
            <>
              <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <span className="text-3xl">❌</span>
              </div>
              <h2 className="text-xl font-bold text-red-600 mb-2">Something Went Wrong</h2>
              <p className="text-slate-500 mb-4">
                We couldn't verify your payment. Please contact support if you were charged.
              </p>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => navigate("/creator/subscription")}
              >
                Back to Plans
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// ============== CHECKOUT CANCEL PAGE ==============

export const SubscriptionCancel = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4" data-testid="subscription-cancel">
      <Card className="w-full max-w-md">
        <CardContent className="pt-8 text-center">
          <div className="mx-auto w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
            <span className="text-3xl">↩️</span>
          </div>
          <h2 className="text-xl font-bold mb-2">Checkout Cancelled</h2>
          <p className="text-slate-500 mb-6">
            No worries! You can subscribe anytime when you're ready.
          </p>
          <div className="space-y-3">
            <Button
              className="w-full bg-purple-600 hover:bg-purple-700"
              onClick={() => navigate("/creator/subscription")}
              data-testid="back-to-plans"
            >
              View Plans
            </Button>
            <Button
              variant="outline"
              className="w-full"
              onClick={() => navigate("/creator/dashboard")}
            >
              Back to Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SubscriptionPlans;
