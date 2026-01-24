import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from './ui/dialog';
import { toast } from 'sonner';
import { 
  Users, Mail, TrendingUp, Award, Search, Download,
  Send, Trash2, Eye, BarChart3, RefreshCw, CheckCircle,
  Clock, UserPlus, Share2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const statusColors = {
  pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  invited: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  converted: 'bg-green-500/20 text-green-400 border-green-500/30',
  unsubscribed: 'bg-gray-500/20 text-gray-400 border-gray-500/30'
};

const creatorTypeLabels = {
  youtuber: '🎬 YouTuber',
  instagrammer: '📸 Instagram',
  tiktoker: '🎵 TikTok',
  podcaster: '🎙️ Podcaster',
  blogger: '✍️ Blogger',
  streamer: '🎮 Streamer',
  musician: '🎸 Musician',
  artist: '🎨 Artist',
  educator: '📚 Educator',
  business: '💼 Business',
  other: '✨ Other'
};

export default function AdminWaitlistDashboard({ token }) {
  const [stats, setStats] = useState(null);
  const [signups, setSignups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSignups, setSelectedSignups] = useState([]);
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [selectedSignup, setSelectedSignup] = useState(null);
  
  // Filters
  const [filters, setFilters] = useState({
    status: '',
    creatorType: '',
    search: '',
    sortBy: 'created_at',
    sortOrder: -1
  });
  
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 20,
    total: 0
  });

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/waitlist/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, [token]);

  const fetchSignups = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        skip: pagination.skip,
        limit: pagination.limit,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder
      });
      
      if (filters.status) params.append('status', filters.status);
      if (filters.creatorType) params.append('creator_type', filters.creatorType);
      if (filters.search) params.append('search', filters.search);
      
      const response = await fetch(`${API_URL}/api/admin/waitlist/signups?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSignups(data.signups || []);
        setPagination(prev => ({ ...prev, total: data.total }));
      }
    } catch (error) {
      console.error('Failed to fetch signups:', error);
      toast.error('Failed to load waitlist');
    }
    setLoading(false);
  }, [token, pagination.skip, pagination.limit, filters, refreshTrigger]);

  useEffect(() => {
    fetchStats();
    fetchSignups();
  }, [fetchStats, fetchSignups]);

  const refreshData = () => {
    setRefreshTrigger(prev => prev + 1);
    fetchStats();
  };

  const inviteSelected = async () => {
    if (selectedSignups.length === 0) {
      toast.error('Select signups to invite');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/admin/waitlist/invite`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ signup_ids: selectedSignups })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Invited ${data.invited} users`);
        setSelectedSignups([]);
        setShowInviteDialog(false);
        refreshData();
      } else {
        toast.error('Failed to send invitations');
      }
    } catch (error) {
      toast.error('Failed to send invitations');
    }
  };

  const deleteSignup = async (signupId) => {
    if (!window.confirm('Are you sure you want to delete this signup?')) return;

    try {
      const response = await fetch(`${API_URL}/api/admin/waitlist/${signupId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Signup deleted');
        refreshData();
      } else {
        toast.error('Failed to delete signup');
      }
    } catch (error) {
      toast.error('Failed to delete signup');
    }
  };

  const exportWaitlist = async () => {
    try {
      const params = filters.status ? `?status=${filters.status}` : '';
      const response = await fetch(`${API_URL}/api/admin/waitlist/export${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `waitlist-export-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        toast.success('Waitlist exported');
      }
    } catch (error) {
      toast.error('Failed to export');
    }
  };

  const toggleSelectAll = () => {
    if (selectedSignups.length === signups.length) {
      setSelectedSignups([]);
    } else {
      setSelectedSignups(signups.map(s => s.id));
    }
  };

  const toggleSelect = (signupId) => {
    setSelectedSignups(prev => 
      prev.includes(signupId) 
        ? prev.filter(id => id !== signupId)
        : [...prev, signupId]
    );
  };

  return (
    <div className="space-y-6" data-testid="admin-waitlist-dashboard">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Users className="h-6 w-6 text-purple-400" />
            Waitlist Management
          </h2>
          <p className="text-gray-400 mt-1">
            Manage signups, send invitations, and track referrals
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button variant="outline" onClick={refreshData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={exportWaitlist}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          {selectedSignups.length > 0 && (
            <Button 
              onClick={() => setShowInviteDialog(true)}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Send className="h-4 w-4 mr-2" />
              Invite ({selectedSignups.length})
            </Button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Signups</p>
                  <p className="text-2xl font-bold text-white">{stats.total?.toLocaleString()}</p>
                </div>
                <Users className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Pending</p>
                  <p className="text-2xl font-bold text-yellow-400">{stats.pending?.toLocaleString()}</p>
                </div>
                <Clock className="h-8 w-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Invited</p>
                  <p className="text-2xl font-bold text-blue-400">{stats.invited?.toLocaleString()}</p>
                </div>
                <Mail className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Converted</p>
                  <p className="text-2xl font-bold text-green-400">{stats.converted?.toLocaleString()}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Conversion Rate</p>
                  <p className="text-2xl font-bold text-white">{stats.conversion_rate}%</p>
                </div>
                <TrendingUp className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="signups" className="space-y-4">
        <TabsList className="bg-gray-800/50">
          <TabsTrigger value="signups">All Signups</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="leaderboard">Top Referrers</TabsTrigger>
        </TabsList>

        {/* Signups Tab */}
        <TabsContent value="signups" className="space-y-4">
          {/* Filters */}
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex flex-wrap gap-4">
                <div className="flex-1 min-w-[200px]">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search by name or email..."
                      value={filters.search}
                      onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                      className="pl-10 bg-gray-800 border-gray-700"
                    />
                  </div>
                </div>
                
                <Select
                  value={filters.status}
                  onValueChange={(value) => setFilters(prev => ({ ...prev, status: value === 'all' ? '' : value }))}
                >
                  <SelectTrigger className="w-[150px] bg-gray-800 border-gray-700">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="invited">Invited</SelectItem>
                    <SelectItem value="converted">Converted</SelectItem>
                  </SelectContent>
                </Select>
                
                <Select
                  value={filters.creatorType}
                  onValueChange={(value) => setFilters(prev => ({ ...prev, creatorType: value === 'all' ? '' : value }))}
                >
                  <SelectTrigger className="w-[150px] bg-gray-800 border-gray-700">
                    <SelectValue placeholder="Creator Type" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    <SelectItem value="all">All Types</SelectItem>
                    {Object.entries(creatorTypeLabels).map(([key, label]) => (
                      <SelectItem key={key} value={key}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                <Select
                  value={filters.sortBy}
                  onValueChange={(value) => setFilters(prev => ({ ...prev, sortBy: value }))}
                >
                  <SelectTrigger className="w-[150px] bg-gray-800 border-gray-700">
                    <SelectValue placeholder="Sort By" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    <SelectItem value="created_at">Date Joined</SelectItem>
                    <SelectItem value="priority_score">Priority Score</SelectItem>
                    <SelectItem value="referral_count">Referrals</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* Signups Table */}
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-800/50">
                    <tr>
                      <th className="p-4 text-left">
                        <input 
                          type="checkbox"
                          checked={selectedSignups.length === signups.length && signups.length > 0}
                          onChange={toggleSelectAll}
                          className="rounded border-gray-600"
                        />
                      </th>
                      <th className="p-4 text-left text-sm font-medium text-gray-400">Name</th>
                      <th className="p-4 text-left text-sm font-medium text-gray-400">Email</th>
                      <th className="p-4 text-left text-sm font-medium text-gray-400">Type</th>
                      <th className="p-4 text-left text-sm font-medium text-gray-400">Status</th>
                      <th className="p-4 text-left text-sm font-medium text-gray-400">Priority</th>
                      <th className="p-4 text-left text-sm font-medium text-gray-400">Referrals</th>
                      <th className="p-4 text-left text-sm font-medium text-gray-400">Joined</th>
                      <th className="p-4 text-left text-sm font-medium text-gray-400">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {loading ? (
                      <tr>
                        <td colSpan={9} className="p-8 text-center text-gray-400">
                          Loading...
                        </td>
                      </tr>
                    ) : signups.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="p-8 text-center text-gray-400">
                          No signups found
                        </td>
                      </tr>
                    ) : (
                      signups.map((signup) => (
                        <tr key={signup.id} className="hover:bg-gray-800/30">
                          <td className="p-4">
                            <input 
                              type="checkbox"
                              checked={selectedSignups.includes(signup.id)}
                              onChange={() => toggleSelect(signup.id)}
                              className="rounded border-gray-600"
                            />
                          </td>
                          <td className="p-4">
                            <span className="font-medium text-white">{signup.name}</span>
                          </td>
                          <td className="p-4 text-gray-400">{signup.email}</td>
                          <td className="p-4">
                            <span className="text-sm">{creatorTypeLabels[signup.creator_type] || signup.creator_type}</span>
                          </td>
                          <td className="p-4">
                            <Badge className={statusColors[signup.status]}>
                              {signup.status}
                            </Badge>
                          </td>
                          <td className="p-4">
                            <span className="font-medium text-purple-400">{signup.priority_score}</span>
                          </td>
                          <td className="p-4">
                            <span className="text-white">{signup.referral_count}</span>
                          </td>
                          <td className="p-4 text-sm text-gray-400">
                            {new Date(signup.created_at).toLocaleDateString()}
                          </td>
                          <td className="p-4">
                            <div className="flex items-center gap-2">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => {
                                  setSelectedSignup(signup);
                                  setShowDetailDialog(true);
                                }}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-red-400 hover:text-red-300"
                                onClick={() => deleteSignup(signup.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination */}
              <div className="p-4 border-t border-gray-800 flex items-center justify-between">
                <span className="text-sm text-gray-400">
                  Showing {pagination.skip + 1} - {Math.min(pagination.skip + pagination.limit, pagination.total)} of {pagination.total}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pagination.skip === 0}
                    onClick={() => setPagination(prev => ({ ...prev, skip: prev.skip - prev.limit }))}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pagination.skip + pagination.limit >= pagination.total}
                    onClick={() => setPagination(prev => ({ ...prev, skip: prev.skip + prev.limit }))}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            {/* By Creator Type */}
            <Card className="bg-gray-900/50 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Signups by Creator Type</CardTitle>
              </CardHeader>
              <CardContent>
                {stats?.by_creator_type?.length > 0 ? (
                  <div className="space-y-3">
                    {stats.by_creator_type.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between">
                        <span className="text-gray-300">{creatorTypeLabels[item.type] || item.type}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-purple-500 rounded-full"
                              style={{ width: `${(item.count / stats.total) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm text-white w-12 text-right">{item.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400 text-center py-4">No data available</p>
                )}
              </CardContent>
            </Card>

            {/* By Source */}
            <Card className="bg-gray-900/50 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Signups by Source</CardTitle>
              </CardHeader>
              <CardContent>
                {stats?.by_source?.length > 0 ? (
                  <div className="space-y-3">
                    {stats.by_source.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between">
                        <span className="text-gray-300 capitalize">{item.source?.replace('_', ' ') || 'Unknown'}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-blue-500 rounded-full"
                              style={{ width: `${(item.count / stats.total) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm text-white w-12 text-right">{item.count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400 text-center py-4">No data available</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Daily Signups Chart */}
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Daily Signups (Last 30 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              {stats?.daily_signups?.length > 0 ? (
                <div className="flex items-end gap-1 h-40">
                  {stats.daily_signups.map((day, idx) => {
                    const maxCount = Math.max(...stats.daily_signups.map(d => d.count));
                    const height = (day.count / maxCount) * 100;
                    return (
                      <div 
                        key={idx}
                        className="flex-1 bg-purple-500/20 hover:bg-purple-500/40 transition-colors rounded-t group relative"
                        style={{ height: `${Math.max(height, 5)}%` }}
                        title={`${day.date}: ${day.count} signups`}
                      >
                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 px-2 py-1 rounded text-xs text-white opacity-0 group-hover:opacity-100 transition whitespace-nowrap">
                          {day.count} signups
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-4">No data available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Leaderboard Tab */}
        <TabsContent value="leaderboard" className="space-y-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Award className="h-5 w-5 text-yellow-400" />
                Top Referrers
              </CardTitle>
              <CardDescription>Users with the most successful referrals</CardDescription>
            </CardHeader>
            <CardContent>
              {stats?.top_referrers?.length > 0 ? (
                <div className="space-y-4">
                  {stats.top_referrers.map((referrer, idx) => (
                    <div 
                      key={idx}
                      className={`flex items-center gap-4 p-4 rounded-lg ${
                        idx === 0 ? 'bg-yellow-500/10 border border-yellow-500/20' :
                        idx === 1 ? 'bg-gray-400/10 border border-gray-400/20' :
                        idx === 2 ? 'bg-orange-500/10 border border-orange-500/20' :
                        'bg-gray-800/50'
                      }`}
                    >
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-xl font-bold ${
                        idx === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                        idx === 1 ? 'bg-gray-400/20 text-gray-400' :
                        idx === 2 ? 'bg-orange-500/20 text-orange-400' :
                        'bg-gray-700 text-gray-400'
                      }`}>
                        {idx + 1}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-white">{referrer.name}</p>
                        <p className="text-sm text-gray-400">{referrer.email}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-white">{referrer.referral_count}</p>
                        <p className="text-xs text-gray-400">referrals</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-purple-400">{referrer.priority_score}</p>
                        <p className="text-xs text-gray-400">points</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Share2 className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">No referrers yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Invite Confirmation Dialog */}
      <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
        <DialogContent className="bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">Send Invitations</DialogTitle>
            <DialogDescription>
              Send invitation emails to {selectedSignups.length} selected users?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowInviteDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={inviteSelected}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Send className="h-4 w-4 mr-2" />
              Send Invitations
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Signup Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="bg-gray-900 border-gray-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">Signup Details</DialogTitle>
          </DialogHeader>
          
          {selectedSignup && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-400">Name</p>
                  <p className="text-white font-medium">{selectedSignup.name}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Email</p>
                  <p className="text-white">{selectedSignup.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Creator Type</p>
                  <p className="text-white">{creatorTypeLabels[selectedSignup.creator_type]}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Niche</p>
                  <p className="text-white">{selectedSignup.niche || 'Not specified'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Status</p>
                  <Badge className={statusColors[selectedSignup.status]}>{selectedSignup.status}</Badge>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Position</p>
                  <p className="text-white">#{selectedSignup.position}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Priority Score</p>
                  <p className="text-purple-400 font-bold">{selectedSignup.priority_score}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-400">Referrals</p>
                  <p className="text-white">{selectedSignup.referral_count}</p>
                </div>
              </div>
              
              <div className="pt-4 border-t border-gray-700">
                <p className="text-sm text-gray-400 mb-2">Referral Code</p>
                <code className="bg-gray-800 px-4 py-2 rounded block text-purple-400">
                  {selectedSignup.referral_code}
                </code>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-400">Joined</p>
                  <p className="text-white">{new Date(selectedSignup.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-400">Source</p>
                  <p className="text-white capitalize">{selectedSignup.source}</p>
                </div>
                {selectedSignup.invited_at && (
                  <div>
                    <p className="text-gray-400">Invited</p>
                    <p className="text-white">{new Date(selectedSignup.invited_at).toLocaleString()}</p>
                  </div>
                )}
                {selectedSignup.converted_at && (
                  <div>
                    <p className="text-gray-400">Converted</p>
                    <p className="text-white">{new Date(selectedSignup.converted_at).toLocaleString()}</p>
                  </div>
                )}
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowDetailDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
