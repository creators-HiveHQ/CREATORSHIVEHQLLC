import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from './ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Switch } from './ui/switch';
import { toast } from 'sonner';
import { 
  Building2, Plus, Edit2, Trash2, Check, ArrowRight,
  Palette, Target, Users, BarChart3, Sparkles, Settings,
  Globe, Image, Megaphone, Package, Briefcase, User
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const categoryIcons = {
  personal: User,
  business: Building2,
  influencer: Sparkles,
  product: Package,
  service: Briefcase,
  agency: Users
};

const statusColors = {
  active: 'bg-green-500/20 text-green-400 border-green-500/30',
  paused: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  archived: 'bg-gray-500/20 text-gray-400 border-gray-500/30'
};

export default function MultiBrandManager({ token, onBrandSwitch }) {
  const [brands, setBrands] = useState([]);
  const [activeBrand, setActiveBrand] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [brandLimit, setBrandLimit] = useState(5);
  const [loading, setLoading] = useState(true);
  
  // Dialog states
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [selectedBrand, setSelectedBrand] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: 'personal',
    template_id: null,
    colors: { primary: '#7C3AED', secondary: '#A78BFA', accent: '#DDD6FE' },
    logo_url: '',
    tagline: '',
    voice_tone: 'professional',
    platforms: []
  });

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    if (!token) return;
    
    let cancelled = false;
    
    const fetchData = async () => {
      setLoading(true);
      try {
        const headers = { 'Authorization': `Bearer ${token}` };
        
        const [brandsRes, activeRes, templatesRes, analyticsRes] = await Promise.all([
          fetch(`${API_URL}/api/elite/brands`, { headers }),
          fetch(`${API_URL}/api/elite/brands/active`, { headers }),
          fetch(`${API_URL}/api/elite/brands/templates`, { headers }),
          fetch(`${API_URL}/api/elite/brands/analytics`, { headers })
        ]);

        if (cancelled) return;

        if (brandsRes.ok) {
          const data = await brandsRes.json();
          setBrands(data.brands || []);
          setBrandLimit(data.limit || 5);
        }
        
        if (activeRes.ok) {
          const data = await activeRes.json();
          setActiveBrand(data.brand || null);
        }
        
        if (templatesRes.ok) {
          const data = await templatesRes.json();
          setTemplates(data.templates || []);
        }
        
        if (analyticsRes.ok) {
          const data = await analyticsRes.json();
          setAnalytics(data);
        }
      } catch (error) {
        if (!cancelled) {
          console.error('Failed to load brand data:', error);
          toast.error('Failed to load brand settings');
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

  const createBrand = async () => {
    if (!formData.name.trim()) {
      toast.error('Please enter a brand name');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/elite/brands`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Brand "${data.brand?.name}" created!`);
        setShowCreateDialog(false);
        resetForm();
        refreshData();
      } else {
        const error = await response.json();
        toast.error(error.detail?.error || error.detail || 'Failed to create brand');
      }
    } catch (error) {
      toast.error('Failed to create brand');
    }
  };

  const updateBrand = async () => {
    if (!selectedBrand) return;

    try {
      const response = await fetch(`${API_URL}/api/elite/brands/${selectedBrand.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        toast.success('Brand updated successfully');
        setShowEditDialog(false);
        refreshData();
      } else {
        const error = await response.json();
        toast.error(error.detail?.error || 'Failed to update brand');
      }
    } catch (error) {
      toast.error('Failed to update brand');
    }
  };

  const deleteBrand = async () => {
    if (!selectedBrand) return;

    try {
      const response = await fetch(`${API_URL}/api/elite/brands/${selectedBrand.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Brand archived');
        setShowDeleteDialog(false);
        setSelectedBrand(null);
        refreshData();
      } else {
        const error = await response.json();
        toast.error(error.detail?.error || 'Failed to archive brand');
      }
    } catch (error) {
      toast.error('Failed to archive brand');
    }
  };

  const switchBrand = async (brandId) => {
    try {
      const response = await fetch(`${API_URL}/api/elite/brands/${brandId}/switch`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setActiveBrand(data.brand);
        toast.success(`Switched to "${data.brand?.name}"`);
        if (onBrandSwitch) {
          onBrandSwitch(data.brand);
        }
        refreshData();
      } else {
        toast.error('Failed to switch brand');
      }
    } catch (error) {
      toast.error('Failed to switch brand');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      category: 'personal',
      template_id: null,
      colors: { primary: '#7C3AED', secondary: '#A78BFA', accent: '#DDD6FE' },
      logo_url: '',
      tagline: '',
      voice_tone: 'professional',
      platforms: []
    });
  };

  const openEditDialog = (brand) => {
    setSelectedBrand(brand);
    setFormData({
      name: brand.name,
      description: brand.description || '',
      category: brand.category || 'personal',
      template_id: brand.template_id,
      colors: brand.colors || { primary: '#7C3AED', secondary: '#A78BFA', accent: '#DDD6FE' },
      logo_url: brand.logo_url || '',
      tagline: brand.tagline || '',
      voice_tone: brand.voice_tone || 'professional',
      platforms: brand.platforms || []
    });
    setShowEditDialog(true);
  };

  const selectTemplate = (template) => {
    setFormData(prev => ({
      ...prev,
      template_id: template.id,
      category: template.category,
      colors: template.default_colors,
      platforms: template.suggested_platforms
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  const activeBrandCount = brands.filter(b => b.status !== 'archived').length;

  return (
    <div className="space-y-6" data-testid="multi-brand-manager">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Building2 className="h-6 w-6 text-purple-400" />
            Multi-Brand Management
          </h2>
          <p className="text-gray-400 mt-1">
            Manage multiple brand identities under one account
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-400">
            {activeBrandCount} / {brandLimit} brands
          </div>
          <Button
            onClick={() => {
              resetForm();
              setShowCreateDialog(true);
            }}
            disabled={activeBrandCount >= brandLimit}
            className="bg-purple-600 hover:bg-purple-700"
            data-testid="create-brand-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Brand
          </Button>
        </div>
      </div>

      {/* Active Brand Banner */}
      {activeBrand && (
        <Card className="bg-gradient-to-r from-purple-900/30 to-indigo-900/30 border-purple-500/30">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div 
                  className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                  style={{ backgroundColor: activeBrand.colors?.primary || '#7C3AED' }}
                >
                  {activeBrand.logo_url ? (
                    <img src={activeBrand.logo_url} alt="" className="w-8 h-8 object-contain" />
                  ) : (
                    activeBrand.name.charAt(0).toUpperCase()
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white">{activeBrand.name}</span>
                    <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                      Active
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-400">{activeBrand.description || activeBrand.tagline || 'Your active brand'}</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => openEditDialog(activeBrand)}
              >
                <Edit2 className="h-4 w-4 mr-2" />
                Edit
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analytics Overview */}
      {analytics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Brands</p>
                  <p className="text-2xl font-bold text-white">{analytics.total_brands || 0}</p>
                </div>
                <Building2 className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Proposals</p>
                  <p className="text-2xl font-bold text-white">{analytics.aggregated_metrics?.total_proposals || 0}</p>
                </div>
                <Target className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Projects</p>
                  <p className="text-2xl font-bold text-white">{analytics.aggregated_metrics?.total_projects || 0}</p>
                </div>
                <Briefcase className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gray-900/50 border-gray-800">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Revenue</p>
                  <p className="text-2xl font-bold text-white">${(analytics.aggregated_metrics?.total_revenue || 0).toLocaleString()}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-yellow-400" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs defaultValue="brands" className="space-y-4">
        <TabsList className="bg-gray-800/50">
          <TabsTrigger value="brands" data-testid="tab-brands">My Brands</TabsTrigger>
          <TabsTrigger value="templates" data-testid="tab-templates">Templates</TabsTrigger>
          <TabsTrigger value="analytics" data-testid="tab-analytics">Analytics</TabsTrigger>
        </TabsList>

        {/* Brands Tab */}
        <TabsContent value="brands" className="space-y-4">
          {brands.length === 0 ? (
            <Card className="bg-gray-900/50 border-gray-800">
              <CardContent className="py-12 text-center">
                <Building2 className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-white mb-2">No brands yet</h3>
                <p className="text-gray-400 mb-4">Create your first brand to get started</p>
                <Button
                  onClick={() => setShowCreateDialog(true)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Brand
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {brands.map((brand) => {
                const IconComponent = categoryIcons[brand.category] || Building2;
                const isActive = activeBrand?.id === brand.id;
                
                return (
                  <Card 
                    key={brand.id}
                    className={`bg-gray-900/50 border-gray-800 hover:border-purple-500/50 transition-colors ${
                      isActive ? 'ring-2 ring-purple-500' : ''
                    }`}
                    data-testid={`brand-card-${brand.id}`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div 
                            className="w-10 h-10 rounded-lg flex items-center justify-center"
                            style={{ backgroundColor: brand.colors?.primary || '#7C3AED' }}
                          >
                            {brand.logo_url ? (
                              <img src={brand.logo_url} alt="" className="w-6 h-6 object-contain" />
                            ) : (
                              <IconComponent className="h-5 w-5 text-white" />
                            )}
                          </div>
                          <div>
                            <h4 className="font-medium text-white">{brand.name}</h4>
                            <Badge variant="outline" className="text-xs">
                              {brand.category}
                            </Badge>
                          </div>
                        </div>
                        <Badge className={statusColors[brand.status]}>
                          {brand.status}
                        </Badge>
                      </div>
                      
                      {brand.description && (
                        <p className="text-sm text-gray-400 mb-3 line-clamp-2">{brand.description}</p>
                      )}
                      
                      {brand.platforms?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-3">
                          {brand.platforms.slice(0, 4).map((platform) => (
                            <Badge key={platform} variant="secondary" className="text-xs">
                              {platform}
                            </Badge>
                          ))}
                          {brand.platforms.length > 4 && (
                            <Badge variant="secondary" className="text-xs">
                              +{brand.platforms.length - 4}
                            </Badge>
                          )}
                        </div>
                      )}
                      
                      <div className="flex items-center gap-2 pt-3 border-t border-gray-700">
                        {!isActive && brand.status === 'active' && (
                          <Button
                            size="sm"
                            onClick={() => switchBrand(brand.id)}
                            className="flex-1 bg-purple-600 hover:bg-purple-700"
                            data-testid={`switch-brand-${brand.id}`}
                          >
                            <ArrowRight className="h-4 w-4 mr-1" />
                            Switch
                          </Button>
                        )}
                        {isActive && (
                          <div className="flex-1 flex items-center justify-center text-sm text-green-400">
                            <Check className="h-4 w-4 mr-1" />
                            Current
                          </div>
                        )}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => openEditDialog(brand)}
                          data-testid={`edit-brand-${brand.id}`}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setSelectedBrand(brand);
                            setShowDeleteDialog(true);
                          }}
                          className="text-red-400 hover:text-red-300"
                          data-testid={`delete-brand-${brand.id}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Brand Templates</CardTitle>
              <CardDescription>Quick-start templates for different brand types</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((template) => {
                  const IconComponent = categoryIcons[template.category] || Building2;
                  
                  return (
                    <div
                      key={template.id}
                      className="p-4 rounded-lg bg-gray-800/50 border border-gray-700 hover:border-purple-500/50 transition-colors cursor-pointer"
                      onClick={() => {
                        selectTemplate(template);
                        setShowCreateDialog(true);
                      }}
                      data-testid={`template-${template.id}`}
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div 
                          className="w-10 h-10 rounded-lg flex items-center justify-center"
                          style={{ backgroundColor: template.default_colors?.primary }}
                        >
                          <span className="text-xl">{template.icon}</span>
                        </div>
                        <div>
                          <h4 className="font-medium text-white">{template.name}</h4>
                          <Badge variant="outline" className="text-xs">{template.category}</Badge>
                        </div>
                      </div>
                      <p className="text-sm text-gray-400 mb-3">{template.description}</p>
                      <div className="flex gap-1">
                        {template.suggested_platforms?.slice(0, 3).map((p) => (
                          <Badge key={p} variant="secondary" className="text-xs">{p}</Badge>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <Card className="bg-gray-900/50 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">Brand Performance</CardTitle>
              <CardDescription>Compare metrics across your brands</CardDescription>
            </CardHeader>
            <CardContent>
              {analytics?.brands?.length > 0 ? (
                <div className="space-y-4">
                  {analytics.brands.map((brand) => (
                    <div key={brand.brand_id} className="p-4 bg-gray-800/50 rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-white">{brand.brand_name}</span>
                          <Badge className={statusColors[brand.status]}>{brand.status}</Badge>
                        </div>
                      </div>
                      <div className="grid grid-cols-4 gap-4">
                        <div>
                          <p className="text-xs text-gray-400">Proposals</p>
                          <p className="text-lg font-semibold text-white">{brand.metrics?.total_proposals || 0}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400">Projects</p>
                          <p className="text-lg font-semibold text-white">{brand.metrics?.total_projects || 0}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400">Revenue</p>
                          <p className="text-lg font-semibold text-white">${(brand.metrics?.total_revenue || 0).toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-400">ARRIS Chats</p>
                          <p className="text-lg font-semibold text-white">{brand.metrics?.total_arris_interactions || 0}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <BarChart3 className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                  <p className="text-gray-400">No analytics data available yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Brand Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="bg-gray-900 border-gray-800 max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">Create New Brand</DialogTitle>
            <DialogDescription>
              Set up a new brand identity for your content
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-white">Brand Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Tech Reviews Pro"
                className="bg-gray-800 border-gray-700"
                data-testid="brand-name-input"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-white">Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="What is this brand about?"
                className="bg-gray-800 border-gray-700"
                rows={2}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-white">Category</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
                >
                  <SelectTrigger className="bg-gray-800 border-gray-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    <SelectItem value="personal">Personal</SelectItem>
                    <SelectItem value="business">Business</SelectItem>
                    <SelectItem value="influencer">Influencer</SelectItem>
                    <SelectItem value="product">Product</SelectItem>
                    <SelectItem value="service">Service</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label className="text-white">Voice Tone</Label>
                <Select
                  value={formData.voice_tone}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, voice_tone: value }))}
                >
                  <SelectTrigger className="bg-gray-800 border-gray-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                    <SelectItem value="friendly">Friendly</SelectItem>
                    <SelectItem value="authoritative">Authoritative</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-white">Brand Colors</Label>
              <div className="flex gap-4">
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formData.colors.primary}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      colors: { ...prev.colors, primary: e.target.value }
                    }))}
                    className="w-10 h-10 rounded cursor-pointer"
                  />
                  <span className="text-sm text-gray-400">Primary</span>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formData.colors.secondary}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      colors: { ...prev.colors, secondary: e.target.value }
                    }))}
                    className="w-10 h-10 rounded cursor-pointer"
                  />
                  <span className="text-sm text-gray-400">Secondary</span>
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-white">Logo URL</Label>
              <Input
                value={formData.logo_url}
                onChange={(e) => setFormData(prev => ({ ...prev, logo_url: e.target.value }))}
                placeholder="https://..."
                className="bg-gray-800 border-gray-700"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-white">Tagline</Label>
              <Input
                value={formData.tagline}
                onChange={(e) => setFormData(prev => ({ ...prev, tagline: e.target.value }))}
                placeholder="Your brands tagline"
                className="bg-gray-800 border-gray-700"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={createBrand}
              className="bg-purple-600 hover:bg-purple-700"
              data-testid="confirm-create-brand"
            >
              Create Brand
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Brand Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="bg-gray-900 border-gray-800 max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">Edit Brand</DialogTitle>
            <DialogDescription>
              Update your brand settings
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-white">Brand Name</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="bg-gray-800 border-gray-700"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-white">Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="bg-gray-800 border-gray-700"
                rows={2}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-white">Category</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
                >
                  <SelectTrigger className="bg-gray-800 border-gray-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    <SelectItem value="personal">Personal</SelectItem>
                    <SelectItem value="business">Business</SelectItem>
                    <SelectItem value="influencer">Influencer</SelectItem>
                    <SelectItem value="product">Product</SelectItem>
                    <SelectItem value="service">Service</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label className="text-white">Voice Tone</Label>
                <Select
                  value={formData.voice_tone}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, voice_tone: value }))}
                >
                  <SelectTrigger className="bg-gray-800 border-gray-700">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    <SelectItem value="professional">Professional</SelectItem>
                    <SelectItem value="casual">Casual</SelectItem>
                    <SelectItem value="friendly">Friendly</SelectItem>
                    <SelectItem value="authoritative">Authoritative</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-white">Brand Colors</Label>
              <div className="flex gap-4">
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formData.colors.primary}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      colors: { ...prev.colors, primary: e.target.value }
                    }))}
                    className="w-10 h-10 rounded cursor-pointer"
                  />
                  <span className="text-sm text-gray-400">Primary</span>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="color"
                    value={formData.colors.secondary}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      colors: { ...prev.colors, secondary: e.target.value }
                    }))}
                    className="w-10 h-10 rounded cursor-pointer"
                  />
                  <span className="text-sm text-gray-400">Secondary</span>
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label className="text-white">Logo URL</Label>
              <Input
                value={formData.logo_url}
                onChange={(e) => setFormData(prev => ({ ...prev, logo_url: e.target.value }))}
                className="bg-gray-800 border-gray-700"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-white">Tagline</Label>
              <Input
                value={formData.tagline}
                onChange={(e) => setFormData(prev => ({ ...prev, tagline: e.target.value }))}
                className="bg-gray-800 border-gray-700"
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowEditDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={updateBrand}
              className="bg-purple-600 hover:bg-purple-700"
            >
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="bg-gray-900 border-gray-800">
          <DialogHeader>
            <DialogTitle className="text-white">Archive Brand</DialogTitle>
            <DialogDescription>
              Are you sure you want to archive &quot;{selectedBrand?.name}&quot;? 
              This will hide the brand but preserve all associated data.
            </DialogDescription>
          </DialogHeader>
          
          <DialogFooter>
            <Button variant="ghost" onClick={() => setShowDeleteDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={deleteBrand}
              className="bg-red-600 hover:bg-red-700"
            >
              Archive Brand
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
