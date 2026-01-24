import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from './ui/dialog';
import { toast } from 'sonner';
import { 
  Key, Copy, RefreshCw, Trash2, Plus, Eye, EyeOff, 
  Code, BarChart3, Clock, Shield, Zap, BookOpen,
  CheckCircle, XCircle, AlertTriangle, ExternalLink
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const capabilityIcons = {
  text_analysis: Code,
  proposal_insights: Zap,
  content_suggestions: BookOpen,
  batch_analysis: BarChart3,
  persona_chat: Shield,
};

export default function ArrisApiManager({ token }) {
  const [keys, setKeys] = useState([]);
  const [usage, setUsage] = useState(null);
  const [capabilities, setCapabilities] = useState(null);
  const [docs, setDocs] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showKeyDialog, setShowKeyDialog] = useState(false);
  const [showDocsDialog, setShowDocsDialog] = useState(false);
  const [newKey, setNewKey] = useState(null);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyType, setNewKeyType] = useState('live');
  const [selectedEndpoint, setSelectedEndpoint] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    if (!token) return;
    
    let cancelled = false;
    
    const fetchData = async () => {
      setLoading(true);
      try {
        const headers = { 'Authorization': `Bearer ${token}` };
        
        const [keysRes, usageRes, capsRes] = await Promise.all([
          fetch(`${API_URL}/api/elite/arris-api/keys`, { headers }),
          fetch(`${API_URL}/api/elite/arris-api/usage`, { headers }),
          fetch(`${API_URL}/api/elite/arris-api/capabilities`, { headers }),
        ]);

        if (cancelled) return;

        if (keysRes.ok) {
          const data = await keysRes.json();
          setKeys(data.keys || []);
        }
        if (usageRes.ok) {
          const data = await usageRes.json();
          setUsage(data);
        }
        if (capsRes.ok) {
          const data = await capsRes.json();
          setCapabilities(data);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load API data:', error);
          toast.error('Failed to load API settings');
        }
      }
      if (!cancelled) {
        setLoading(false);
      }
    };
    
    fetchData();
    
    return () => { cancelled = true; };
  }, [token, refreshTrigger]);

  const refreshData = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  const createApiKey = async () => {
    if (!newKeyName.trim()) {
      toast.error('Please enter a key name');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/elite/arris-api/keys`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: newKeyName,
          key_type: newKeyType
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setNewKey(data);
        setShowCreateDialog(false);
        setShowKeyDialog(true);
        setNewKeyName('');
        refreshData();
        toast.success('API key created successfully');
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create API key');
      }
    } catch (error) {
      toast.error('Failed to create API key');
    }
  };

  const revokeKey = async (keyId) => {
    if (!window.confirm('Are you sure you want to revoke this API key? This cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/elite/arris-api/keys/${keyId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        toast.success('API key revoked');
        refreshData();
      } else {
        toast.error('Failed to revoke API key');
      }
    } catch (error) {
      toast.error('Failed to revoke API key');
    }
  };

  const regenerateKey = async (keyId) => {
    if (!window.confirm('Regenerate this API key? The old key will stop working immediately.')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/elite/arris-api/keys/${keyId}/regenerate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        setNewKey(data);
        setShowKeyDialog(true);
        refreshData();
        toast.success('API key regenerated');
      } else {
        toast.error('Failed to regenerate API key');
      }
    } catch (error) {
      toast.error('Failed to regenerate API key');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const loadDocs = async () => {
    try {
      const response = await fetch(`${API_URL}/api/elite/arris-api/docs`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        setDocs(data);
        setShowDocsDialog(true);
      }
    } catch (error) {
      toast.error('Failed to load documentation');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="arris-api-manager">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Key className="h-6 w-6 text-purple-400" />
            ARRIS API Access
          </h2>
          <p className="text-gray-400 mt-1">
            Direct programmatic access to ARRIS AI capabilities
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            onClick={loadDocs}
            variant="outline"
            data-testid="view-docs-btn"
          >
            <BookOpen className="h-4 w-4 mr-2" />
            API Docs
          </Button>
          <Button
            onClick={() => setShowCreateDialog(true)}
            className="bg-purple-600 hover:bg-purple-700"
            data-testid="create-key-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create API Key
          </Button>
        </div>
      </div>

      {/* Usage Stats */}
      {usage && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Requests</p>
                  <p className="text-2xl font-bold text-white">{usage.total_requests?.toLocaleString() || 0}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Active Keys</p>
                  <p className="text-2xl font-bold text-white">{usage.active_keys || 0}</p>
                </div>
                <Key className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Hourly Limit</p>
                  <p className="text-2xl font-bold text-white">{usage.rate_limits?.requests_per_hour || 100}</p>
                </div>
                <Clock className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Daily Limit</p>
                  <p className="text-2xl font-bold text-white">{usage.rate_limits?.requests_per_day?.toLocaleString() || '1,000'}</p>
                </div>
                <Zap className="h-8 w-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="keys" className="space-y-4">
        <TabsList className="bg-gray-800/50">
          <TabsTrigger value="keys" data-testid="tab-keys">API Keys</TabsTrigger>
          <TabsTrigger value="capabilities" data-testid="tab-capabilities">Capabilities</TabsTrigger>
          <TabsTrigger value="usage" data-testid="tab-usage">Usage History</TabsTrigger>
        </TabsList>

        {/* API Keys Tab */}
        <TabsContent value="keys" className="space-y-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Your API Keys</CardTitle>
              <CardDescription>Manage your ARRIS API keys</CardDescription>
            </CardHeader>
            <CardContent>
              {keys.length === 0 ? (
                <div className="text-center py-8">
                  <Key className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400 mb-4">No API keys yet</p>
                  <Button
                    onClick={() => setShowCreateDialog(true)}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Create Your First Key
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {keys.map((key) => (
                    <div
                      key={key.id}
                      className={`p-4 rounded-lg border ${
                        key.status === 'active' 
                          ? 'bg-gray-800/50 border-gray-700' 
                          : 'bg-gray-800/30 border-gray-800 opacity-60'
                      }`}
                      data-testid={`api-key-${key.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${
                            key.status === 'active' ? 'bg-green-500/20' : 'bg-red-500/20'
                          }`}>
                            <Key className={`h-5 w-5 ${
                              key.status === 'active' ? 'text-green-400' : 'text-red-400'
                            }`} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-white">{key.name}</span>
                              <Badge variant={key.key_type === 'live' ? 'default' : 'secondary'}>
                                {key.key_type}
                              </Badge>
                              <Badge variant={key.status === 'active' ? 'outline' : 'destructive'}>
                                {key.status}
                              </Badge>
                            </div>
                            <div className="text-sm text-gray-400 mt-1">
                              <code className="bg-gray-800 px-2 py-0.5 rounded">{key.key_prefix}...</code>
                              <span className="mx-2">•</span>
                              Created {new Date(key.created_at).toLocaleDateString()}
                              {key.last_used_at && (
                                <>
                                  <span className="mx-2">•</span>
                                  Last used {new Date(key.last_used_at).toLocaleDateString()}
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        {key.status === 'active' && (
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => regenerateKey(key.id)}
                              data-testid={`regenerate-key-${key.id}`}
                            >
                              <RefreshCw className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => revokeKey(key.id)}
                              className="text-red-400 hover:text-red-300"
                              data-testid={`revoke-key-${key.id}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
                      </div>
                      
                      {key.status === 'active' && (
                        <div className="mt-3 pt-3 border-t border-gray-700 flex items-center gap-4 text-sm">
                          <span className="text-gray-400">
                            Usage: <span className="text-white">{key.usage_count?.toLocaleString() || 0}</span> requests
                          </span>
                          <span className="text-gray-400">
                            Expires: <span className="text-white">{new Date(key.expires_at).toLocaleDateString()}</span>
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Capabilities Tab */}
        <TabsContent value="capabilities" className="space-y-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Available Capabilities</CardTitle>
              <CardDescription>What you can do with the ARRIS API</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                {capabilities?.capabilities?.map((cap) => {
                  const IconComponent = capabilityIcons[cap.id] || Code;
                  return (
                    <div
                      key={cap.id}
                      className="p-4 rounded-lg bg-gray-800/50 border border-gray-700 hover:border-purple-500/50 transition-colors cursor-pointer"
                      onClick={() => {
                        setSelectedEndpoint(cap);
                        loadDocs();
                      }}
                      data-testid={`capability-${cap.id}`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-purple-500/20">
                          <IconComponent className="h-5 w-5 text-purple-400" />
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-white">{cap.name}</h4>
                          <p className="text-sm text-gray-400 mt-1">{cap.description}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge variant="outline" className="text-xs">
                              {cap.method}
                            </Badge>
                            <code className="text-xs text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded">
                              {cap.endpoint}
                            </code>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Quick Start */}
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Quick Start</CardTitle>
              <CardDescription>Get started with the ARRIS API in minutes</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-white">1. Get your API key</h4>
                <p className="text-sm text-gray-400">
                  Create an API key above. Keep it secure - it grants full access to ARRIS.
                </p>
              </div>
              
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-white">2. Make your first request</h4>
                <div className="bg-gray-800 rounded-lg p-4 overflow-x-auto">
                  <pre className="text-sm text-gray-300">
{`curl -X POST "${API_URL}/api/elite/arris-api/analyze" \\
  -H "X-ARRIS-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "I want to grow my YouTube channel", "analysis_type": "strategy"}'`}
                  </pre>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(`curl -X POST "${API_URL}/api/elite/arris-api/analyze" -H "X-ARRIS-API-Key: YOUR_API_KEY" -H "Content-Type: application/json" -d '{"text": "I want to grow my YouTube channel", "analysis_type": "strategy"}'`)}
                >
                  <Copy className="h-4 w-4 mr-2" />
                  Copy
                </Button>
              </div>
              
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-white">3. Explore the response</h4>
                <p className="text-sm text-gray-400">
                  ARRIS will return structured insights including summary, key points, and actionable recommendations.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Usage History Tab */}
        <TabsContent value="usage" className="space-y-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Usage by Endpoint</CardTitle>
              <CardDescription>Last 30 days of API usage</CardDescription>
            </CardHeader>
            <CardContent>
              {usage?.by_endpoint?.length > 0 ? (
                <div className="space-y-3">
                  {usage.by_endpoint.map((ep) => (
                    <div key={ep.endpoint} className="flex items-center justify-between p-3 bg-gray-800/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Code className="h-5 w-5 text-purple-400" />
                        <div>
                          <span className="font-medium text-white">{ep.endpoint}</span>
                          <div className="text-sm text-gray-400">
                            Avg response: {ep.avg_time_ms}ms
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-medium text-white">{ep.total_requests?.toLocaleString()}</div>
                        <div className="text-sm text-gray-400">{ep.success_rate}% success</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <BarChart3 className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">No usage data yet</p>
                  <p className="text-sm text-gray-500 mt-1">Start making API requests to see usage statistics</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Daily Breakdown */}
          {usage?.daily_breakdown?.length > 0 && (
            <Card className="bg-gray-900/50 border-gray-800">
              <CardHeader>
                <CardTitle className="text-white">Daily Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {usage.daily_breakdown.slice(0, 14).map((day, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2 hover:bg-gray-800/50 rounded">
                      <span className="text-gray-400">{day.date}</span>
                      <div className="flex items-center gap-4">
                        <Badge variant="outline">{day.endpoint}</Badge>
                        <span className="text-white">{day.requests} requests</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Create Key Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">Create API Key</DialogTitle>
            <DialogDescription>
              Create a new API key to access ARRIS programmatically
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="keyName" className="text-white">Key Name</Label>
              <Input
                id="keyName"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production Server"
                className="bg-gray-800 border-gray-700"
                data-testid="key-name-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-white">Key Type</Label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    value="live"
                    checked={newKeyType === 'live'}
                    onChange={(e) => setNewKeyType(e.target.value)}
                    className="text-purple-500"
                  />
                  <span className="text-white">Live</span>
                  <span className="text-xs text-gray-400">(Production use)</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    value="test"
                    checked={newKeyType === 'test'}
                    onChange={(e) => setNewKeyType(e.target.value)}
                    className="text-purple-500"
                  />
                  <span className="text-white">Test</span>
                  <span className="text-xs text-gray-400">(Development use)</span>
                </label>
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button 
              onClick={createApiKey}
              className="bg-purple-600 hover:bg-purple-700"
              data-testid="confirm-create-key"
            >
              Create Key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* New Key Display Dialog */}
      <Dialog open={showKeyDialog} onOpenChange={setShowKeyDialog}>
        <DialogContent className="bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-400" />
              API Key Created
            </DialogTitle>
            <DialogDescription>
              Save this key now - it won't be shown again!
            </DialogDescription>
          </DialogHeader>
          
          {newKey && (
            <div className="space-y-4 py-4">
              <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-yellow-200">
                    This is the only time your API key will be displayed. Copy it now and store it securely.
                  </p>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label className="text-white">Your API Key</Label>
                <div className="flex gap-2">
                  <Input
                    value={newKey.api_key}
                    readOnly
                    className="bg-gray-800 border-gray-700 font-mono text-sm"
                    data-testid="new-api-key-value"
                  />
                  <Button
                    variant="outline"
                    onClick={() => copyToClipboard(newKey.api_key)}
                    data-testid="copy-api-key"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Key ID:</span>
                  <span className="text-white ml-2">{newKey.key_id}</span>
                </div>
                <div>
                  <span className="text-gray-400">Type:</span>
                  <Badge className="ml-2">{newKey.key_type}</Badge>
                </div>
                <div className="col-span-2">
                  <span className="text-gray-400">Expires:</span>
                  <span className="text-white ml-2">{new Date(newKey.expires_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button 
              onClick={() => setShowKeyDialog(false)}
              className="bg-purple-600 hover:bg-purple-700"
            >
              I've Saved My Key
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* API Documentation Dialog */}
      <Dialog open={showDocsDialog} onOpenChange={setShowDocsDialog}>
        <DialogContent className="bg-gray-900 border-gray-800 max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <BookOpen className="h-5 w-5 text-purple-400" />
              API Documentation
            </DialogTitle>
            <DialogDescription>
              Complete reference for the ARRIS API
            </DialogDescription>
          </DialogHeader>
          
          {docs && (
            <div className="space-y-6 py-4">
              {/* Authentication */}
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-white">Authentication</h3>
                <p className="text-gray-400 text-sm">{docs.authentication?.description}</p>
                <div className="bg-gray-800 rounded-lg p-3">
                  <code className="text-sm text-purple-400">{docs.authentication?.example}</code>
                </div>
              </div>
              
              {/* Rate Limits */}
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-white">Rate Limits</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 bg-gray-800/50 rounded-lg">
                    <p className="text-sm text-gray-400">Per Hour</p>
                    <p className="text-xl font-bold text-white">{docs.rate_limits?.requests_per_hour}</p>
                  </div>
                  <div className="p-3 bg-gray-800/50 rounded-lg">
                    <p className="text-sm text-gray-400">Per Day</p>
                    <p className="text-xl font-bold text-white">{docs.rate_limits?.requests_per_day?.toLocaleString()}</p>
                  </div>
                  <div className="p-3 bg-gray-800/50 rounded-lg">
                    <p className="text-sm text-gray-400">Batch Size</p>
                    <p className="text-xl font-bold text-white">{docs.rate_limits?.max_batch_size}</p>
                  </div>
                  <div className="p-3 bg-gray-800/50 rounded-lg">
                    <p className="text-sm text-gray-400">Max Text</p>
                    <p className="text-xl font-bold text-white">{(docs.rate_limits?.max_text_length / 1000).toFixed(0)}K</p>
                  </div>
                </div>
              </div>
              
              {/* Endpoints */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white">Endpoints</h3>
                {docs.endpoints?.map((endpoint, idx) => (
                  <div key={idx} className="p-4 bg-gray-800/50 rounded-lg border border-gray-700">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge>{endpoint.method}</Badge>
                      <code className="text-purple-400">{endpoint.path}</code>
                    </div>
                    <p className="text-gray-400 text-sm mb-3">{endpoint.description}</p>
                    
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <h5 className="text-sm font-medium text-white mb-2">Request Body</h5>
                        <div className="bg-gray-900 rounded p-2 text-xs">
                          {Object.entries(endpoint.request_body || {}).map(([key, val]) => (
                            <div key={key} className="py-1">
                              <code className="text-green-400">{key}</code>
                              <span className="text-gray-500">: {val}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                      <div>
                        <h5 className="text-sm font-medium text-white mb-2">Response</h5>
                        <div className="bg-gray-900 rounded p-2 text-xs">
                          {Object.entries(endpoint.response || {}).map(([key, val]) => (
                            <div key={key} className="py-1">
                              <code className="text-blue-400">{key}</code>
                              <span className="text-gray-500">: {val}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Error Codes */}
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-white">Error Codes</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {Object.entries(docs.error_codes || {}).map(([code, desc]) => (
                    <div key={code} className="p-2 bg-gray-800/50 rounded">
                      <Badge variant={code.startsWith('4') ? 'destructive' : 'secondary'}>{code}</Badge>
                      <p className="text-xs text-gray-400 mt-1">{desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowDocsDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
