import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Progress } from './ui/progress';
import { toast } from 'sonner';
import { Copy, Users, DollarSign, Trophy, Gift, TrendingUp, Share2, CheckCircle, Clock, Award } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const tierColors = {
  bronze: 'bg-amber-600',
  silver: 'bg-gray-400',
  gold: 'bg-yellow-500',
  platinum: 'bg-purple-500',
};

const tierBgColors = {
  bronze: 'bg-amber-600/10 border-amber-600/30',
  silver: 'bg-gray-400/10 border-gray-400/30',
  gold: 'bg-yellow-500/10 border-yellow-500/30',
  platinum: 'bg-purple-500/10 border-purple-500/30',
};

const statusBadges = {
  pending: { color: 'bg-yellow-500/20 text-yellow-300', label: 'Pending' },
  qualified: { color: 'bg-blue-500/20 text-blue-300', label: 'Qualified' },
  converted: { color: 'bg-green-500/20 text-green-300', label: 'Converted' },
  expired: { color: 'bg-gray-500/20 text-gray-400', label: 'Expired' },
};

export default function ReferralDashboard({ token }) {
  const [stats, setStats] = useState(null);
  const [tierInfo, setTierInfo] = useState(null);
  const [referrals, setReferrals] = useState([]);
  const [commissions, setCommissions] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generatingCode, setGeneratingCode] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    if (!token) return;
    
    let cancelled = false;
    
    const fetchData = async () => {
      setLoading(true);
      try {
        const headers = { 'Authorization': `Bearer ${token}` };
        
        const [statsRes, tierRes, referralsRes, commissionsRes, leaderboardRes] = await Promise.all([
          fetch(`${API_URL}/api/referral/my-stats`, { headers }),
          fetch(`${API_URL}/api/referral/tier-info`, { headers }),
          fetch(`${API_URL}/api/referral/my-referrals`, { headers }),
          fetch(`${API_URL}/api/referral/my-commissions`, { headers }),
          fetch(`${API_URL}/api/referral/leaderboard`, { headers }),
        ]);

        if (cancelled) return;

        if (statsRes.ok) {
          const data = await statsRes.json();
          setStats(data);
        }
        if (tierRes.ok) {
          const data = await tierRes.json();
          setTierInfo(data);
        }
        if (referralsRes.ok) {
          const data = await referralsRes.json();
          setReferrals(data.referrals || []);
        }
        if (commissionsRes.ok) {
          const data = await commissionsRes.json();
          setCommissions(data);
        }
        if (leaderboardRes.ok) {
          const data = await leaderboardRes.json();
          setLeaderboard(data.leaderboard || []);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load referral data:', error);
          toast.error('Failed to load referral data');
        }
      }
      if (!cancelled) {
        setLoading(false);
      }
    };
    
    fetchData();
    
    return () => { cancelled = true; };
  }, [token, refreshTrigger]);

  const loadData = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const generateCode = async () => {
    setGeneratingCode(true);
    try {
      const response = await fetch(`${API_URL}/api/referral/generate-code`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setStats(prev => ({ ...prev, referral_code: data.code, referral_url: data.referral_url }));
        toast.success('Referral code generated!');
        loadData();
      }
    } catch (error) {
      toast.error('Failed to generate code');
    }
    setGeneratingCode(false);
  };

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied to clipboard!`);
  };

  const getFullReferralUrl = () => {
    if (!stats?.referral_url) return '';
    return `${window.location.origin}${stats.referral_url}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Referral Code */}
      <Card className="bg-gradient-to-r from-purple-900/50 to-indigo-900/50 border-purple-700/30">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <Share2 className="h-6 w-6 text-purple-400" />
                Referral Program
              </h2>
              <p className="text-gray-400 mt-1">
                Earn commissions by referring new creators to Hive HQ
              </p>
            </div>
            
            {stats?.referral_code ? (
              <div className="flex flex-col sm:flex-row gap-2">
                <div className="bg-gray-900/60 rounded-lg px-4 py-2 flex items-center gap-2">
                  <span className="text-gray-400 text-sm">Your Code:</span>
                  <span className="font-mono text-lg font-bold text-purple-300">{stats.referral_code}</span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => copyToClipboard(stats.referral_code, 'Code')}
                    data-testid="copy-code-btn"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
                <Button
                  onClick={() => copyToClipboard(getFullReferralUrl(), 'Referral URL')}
                  className="bg-purple-600 hover:bg-purple-700"
                  data-testid="copy-url-btn"
                >
                  <Share2 className="h-4 w-4 mr-2" />
                  Share Link
                </Button>
              </div>
            ) : (
              <Button
                onClick={generateCode}
                disabled={generatingCode}
                className="bg-purple-600 hover:bg-purple-700"
                data-testid="generate-code-btn"
              >
                {generatingCode ? 'Generating...' : 'Generate Referral Code'}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Referrals</p>
                <p className="text-2xl font-bold text-white">{stats?.stats?.total_referrals || 0}</p>
              </div>
              <Users className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Converted</p>
                <p className="text-2xl font-bold text-green-400">{stats?.stats?.converted || 0}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Earnings</p>
                <p className="text-2xl font-bold text-emerald-400">${stats?.earnings?.total?.toFixed(2) || '0.00'}</p>
              </div>
              <DollarSign className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gray-900/50 border-gray-800">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Pending Payout</p>
                <p className="text-2xl font-bold text-yellow-400">${stats?.earnings?.pending?.toFixed(2) || '0.00'}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tier Progress */}
      {stats && (
        <Card className={`border ${tierBgColors[stats.tier] || tierBgColors.bronze}`}>
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-full ${tierColors[stats.tier]} flex items-center justify-center`}>
                  <Trophy className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white capitalize">{stats.tier} Tier</h3>
                  <p className="text-gray-400">
                    {(stats.commission_rate * 100).toFixed(0)}% commission rate
                  </p>
                </div>
              </div>
              
              {stats.next_tier?.tier && (
                <div className="flex-1 max-w-md">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Progress to {stats.next_tier.tier}</span>
                    <span className="text-purple-400">
                      {stats.stats?.converted || 0} / {stats.next_tier.referrals_needed + (stats.stats?.converted || 0)} referrals
                    </span>
                  </div>
                  <Progress 
                    value={stats.next_tier.progress_percent || 0} 
                    className="h-2 bg-gray-800"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    {stats.next_tier.referrals_needed} more to unlock {(stats.next_tier.commission_rate * 100).toFixed(0)}% commission
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="referrals" className="w-full">
        <TabsList className="bg-gray-900/50 border border-gray-800">
          <TabsTrigger value="referrals" data-testid="referrals-tab">
            My Referrals
          </TabsTrigger>
          <TabsTrigger value="commissions" data-testid="commissions-tab">
            Commissions
          </TabsTrigger>
          <TabsTrigger value="milestones" data-testid="milestones-tab">
            Milestones
          </TabsTrigger>
          <TabsTrigger value="leaderboard" data-testid="leaderboard-tab">
            Leaderboard
          </TabsTrigger>
        </TabsList>

        {/* Referrals Tab */}
        <TabsContent value="referrals" className="mt-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Your Referrals</CardTitle>
              <CardDescription>People who signed up using your referral code</CardDescription>
            </CardHeader>
            <CardContent>
              {referrals.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No referrals yet. Share your code to get started!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {referrals.map((ref, index) => (
                    <div 
                      key={ref.id || index}
                      className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg"
                      data-testid={`referral-item-${index}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-purple-600/20 flex items-center justify-center">
                          <Users className="h-5 w-5 text-purple-400" />
                        </div>
                        <div>
                          <p className="font-medium text-white">{ref.referred_name || 'Creator'}</p>
                          <p className="text-sm text-gray-400">
                            {new Date(ref.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        {ref.commission_earned > 0 && (
                          <span className="text-green-400 font-medium">
                            +${ref.commission_earned.toFixed(2)}
                          </span>
                        )}
                        <Badge className={statusBadges[ref.status]?.color || statusBadges.pending.color}>
                          {statusBadges[ref.status]?.label || ref.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Commissions Tab */}
        <TabsContent value="commissions" className="mt-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Commission History</CardTitle>
              <CardDescription>Your earned commissions and payout status</CardDescription>
            </CardHeader>
            <CardContent>
              {(!commissions?.commissions || commissions.commissions.length === 0) ? (
                <div className="text-center py-8 text-gray-400">
                  <DollarSign className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No commissions earned yet. Conversions generate commissions!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {commissions.commissions.map((comm, index) => (
                    <div 
                      key={comm.id || index}
                      className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg"
                      data-testid={`commission-item-${index}`}
                    >
                      <div>
                        <p className="font-medium text-white">
                          ${comm.amount.toFixed(2)} Commission
                        </p>
                        <p className="text-sm text-gray-400">
                          {(comm.commission_rate * 100).toFixed(0)}% of ${comm.conversion_value.toFixed(2)}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(comm.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <Badge className={
                        comm.status === 'paid' ? 'bg-green-500/20 text-green-300' :
                        comm.status === 'approved' ? 'bg-blue-500/20 text-blue-300' :
                        'bg-yellow-500/20 text-yellow-300'
                      }>
                        {comm.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
              
              {commissions?.summary && (
                <div className="mt-6 pt-4 border-t border-gray-800 grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <p className="text-sm text-gray-400">Total Earned</p>
                    <p className="text-lg font-bold text-white">${commissions.summary.total_earned.toFixed(2)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-400">Pending</p>
                    <p className="text-lg font-bold text-yellow-400">${commissions.summary.total_pending.toFixed(2)}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-gray-400">Paid Out</p>
                    <p className="text-lg font-bold text-green-400">${commissions.summary.total_paid.toFixed(2)}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Milestones Tab */}
        <TabsContent value="milestones" className="mt-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Gift className="h-5 w-5 text-purple-400" />
                Milestone Bonuses
              </CardTitle>
              <CardDescription>Earn bonus rewards as you reach referral milestones</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {tierInfo?.milestones?.map((milestone, index) => {
                  const achieved = (stats?.stats?.converted || 0) >= milestone.threshold;
                  const alreadyEarned = stats?.milestones?.achieved?.includes(`MILESTONE_${milestone.threshold}`);
                  
                  return (
                    <div 
                      key={index}
                      className={`p-4 rounded-lg border ${
                        alreadyEarned ? 'bg-green-900/20 border-green-700/30' :
                        achieved ? 'bg-purple-900/20 border-purple-700/30' :
                        'bg-gray-800/30 border-gray-700/30'
                      }`}
                      data-testid={`milestone-${milestone.threshold}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                            alreadyEarned ? 'bg-green-600' : achieved ? 'bg-purple-600' : 'bg-gray-700'
                          }`}>
                            {alreadyEarned ? (
                              <CheckCircle className="h-6 w-6 text-white" />
                            ) : (
                              <Award className="h-6 w-6 text-white" />
                            )}
                          </div>
                          <div>
                            <h4 className="font-semibold text-white">{milestone.title}</h4>
                            <p className="text-sm text-gray-400">{milestone.description}</p>
                            <p className="text-xs text-gray-500 mt-1">
                              {milestone.threshold} successful referrals required
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-xl font-bold ${
                            alreadyEarned ? 'text-green-400' : 'text-purple-400'
                          }`}>
                            ${milestone.bonus.toFixed(2)}
                          </p>
                          <p className="text-xs text-gray-500">bonus</p>
                        </div>
                      </div>
                      
                      {!alreadyEarned && (
                        <div className="mt-3">
                          <Progress 
                            value={Math.min(100, ((stats?.stats?.converted || 0) / milestone.threshold) * 100)}
                            className="h-1 bg-gray-700"
                          />
                          <p className="text-xs text-gray-500 mt-1 text-right">
                            {stats?.stats?.converted || 0} / {milestone.threshold}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Leaderboard Tab */}
        <TabsContent value="leaderboard" className="mt-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-purple-400" />
                Top Referrers
              </CardTitle>
              <CardDescription>See how you rank among other creators</CardDescription>
            </CardHeader>
            <CardContent>
              {leaderboard.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Trophy className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Be the first to make the leaderboard!</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {leaderboard.map((entry, index) => (
                    <div 
                      key={entry.creator_id}
                      className={`flex items-center justify-between p-3 rounded-lg ${
                        index < 3 ? 'bg-gradient-to-r from-purple-900/30 to-transparent' : 'bg-gray-800/30'
                      }`}
                      data-testid={`leaderboard-entry-${index}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                          index === 0 ? 'bg-yellow-500 text-black' :
                          index === 1 ? 'bg-gray-300 text-black' :
                          index === 2 ? 'bg-amber-600 text-white' :
                          'bg-gray-700 text-gray-300'
                        }`}>
                          {entry.rank}
                        </div>
                        <div>
                          <p className="font-medium text-white">{entry.name}</p>
                          <Badge className={`text-xs ${tierColors[entry.tier]} text-white`}>
                            {entry.tier}
                          </Badge>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-white">{entry.total_referrals} referrals</p>
                        <p className="text-sm text-green-400">${entry.total_earnings.toFixed(2)} earned</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Tier Information */}
      <Card className="bg-gray-900/50 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Commission Tiers</CardTitle>
          <CardDescription>Increase your referrals to unlock higher commission rates</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {tierInfo?.tiers?.map((tier) => (
              <div 
                key={tier.tier}
                className={`p-4 rounded-lg border text-center ${
                  stats?.tier === tier.tier ? 
                    `${tierBgColors[tier.tier]} ring-2 ring-purple-500` : 
                    'bg-gray-800/30 border-gray-700/30'
                }`}
              >
                <div className={`w-10 h-10 rounded-full ${tierColors[tier.tier]} mx-auto mb-2 flex items-center justify-center`}>
                  <Trophy className="h-5 w-5 text-white" />
                </div>
                <h4 className="font-semibold text-white capitalize">{tier.tier}</h4>
                <p className="text-2xl font-bold text-purple-400">{(tier.commission_rate * 100).toFixed(0)}%</p>
                <p className="text-xs text-gray-500">{tier.min_referrals}+ referrals</p>
                {stats?.tier === tier.tier && (
                  <Badge className="mt-2 bg-purple-600">Current</Badge>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
