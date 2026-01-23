import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogDescription } from './ui/dialog';
import { toast } from 'sonner';
import { 
  Briefcase, Smile, LineChart, Lightbulb, Trophy, Star, Rocket, Heart, Brain, 
  User, Plus, Edit2, Trash2, Check, Sparkles, MessageSquare, Settings2, TestTube
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const iconMap = {
  briefcase: Briefcase,
  smile: Smile,
  'chart-line': LineChart,
  lightbulb: Lightbulb,
  trophy: Trophy,
  star: Star,
  rocket: Rocket,
  heart: Heart,
  brain: Brain,
  user: User,
};

const toneDescriptions = {
  professional: 'Formal, business-oriented, and polished',
  friendly: 'Warm, conversational, and approachable',
  analytical: 'Precise, data-focused, and methodical',
  creative: 'Imaginative, innovative, and unconventional',
  motivational: 'Encouraging, energizing, and inspiring',
  direct: 'Concise, straightforward, and to the point',
  empathetic: 'Understanding, supportive, and compassionate',
};

const styleDescriptions = {
  detailed: 'Comprehensive, in-depth responses',
  concise: 'Brief and focused, uses bullet points',
  conversational: 'Natural dialogue flow with questions',
  structured: 'Organized with headers and lists',
  storytelling: 'Narratives and analogies',
  socratic: 'Guides through questioning',
};

export default function ArrisPersonaManager({ token, onPersonaChange }) {
  const [personas, setPersonas] = useState({ default_personas: [], custom_personas: [] });
  const [options, setOptions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activePersona, setActivePersona] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [testPersonaId, setTestPersonaId] = useState(null);
  const [testMessage, setTestMessage] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [editingPersona, setEditingPersona] = useState(null);
  
  const [newPersona, setNewPersona] = useState({
    name: '',
    description: '',
    tone: 'friendly',
    communication_style: 'conversational',
    response_length: 'medium',
    primary_focus_areas: ['content'],
    emoji_usage: 'moderate',
    custom_greeting: '',
    signature_phrase: '',
    personality_traits: [],
    custom_instructions: '',
    icon: 'user',
  });

  const fetchData = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [personasRes, optionsRes, activeRes] = await Promise.all([
        fetch(`${API_URL}/api/elite/personas`, { headers }),
        fetch(`${API_URL}/api/elite/personas/options`, { headers }),
        fetch(`${API_URL}/api/elite/personas/active`, { headers }),
      ]);

      if (personasRes.ok) {
        const data = await personasRes.json();
        setPersonas(data);
      }
      if (optionsRes.ok) {
        const data = await optionsRes.json();
        setOptions(data);
      }
      if (activeRes.ok) {
        const data = await activeRes.json();
        setActivePersona(data);
      }
    } catch (error) {
      console.error('Failed to load personas:', error);
      toast.error('Failed to load ARRIS personas');
    }
    setLoading(false);
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const activatePersona = async (personaId) => {
    try {
      const response = await fetch(`${API_URL}/api/elite/personas/${personaId}/activate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        const result = await response.json();
        setActivePersona(result.active_persona);
        toast.success(`Switched to ${result.active_persona.name}`);
        fetchData();
        if (onPersonaChange) onPersonaChange(result.active_persona);
      } else {
        toast.error('Failed to activate persona');
      }
    } catch (error) {
      toast.error('Failed to activate persona');
    }
  };

  const createPersona = async () => {
    if (!newPersona.name.trim()) {
      toast.error('Please enter a persona name');
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/api/elite/personas`, {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newPersona),
      });
      
      if (response.ok) {
        toast.success('Custom persona created!');
        setShowCreateDialog(false);
        resetNewPersona();
        fetchData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create persona');
      }
    } catch (error) {
      toast.error('Failed to create persona');
    }
  };

  const updatePersona = async (personaId, updates) => {
    try {
      const response = await fetch(`${API_URL}/api/elite/personas/${personaId}`, {
        method: 'PATCH',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates),
      });
      
      if (response.ok) {
        toast.success('Persona updated!');
        setEditingPersona(null);
        fetchData();
      } else {
        toast.error('Failed to update persona');
      }
    } catch (error) {
      toast.error('Failed to update persona');
    }
  };

  const deletePersona = async (personaId) => {
    if (!window.confirm('Are you sure you want to delete this persona?')) return;
    
    try {
      const response = await fetch(`${API_URL}/api/elite/personas/${personaId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      
      if (response.ok) {
        toast.success('Persona deleted');
        fetchData();
      } else {
        toast.error('Failed to delete persona');
      }
    } catch (error) {
      toast.error('Failed to delete persona');
    }
  };

  const testPersona = async () => {
    if (!testMessage.trim()) {
      toast.error('Please enter a test message');
      return;
    }
    
    try {
      const response = await fetch(
        `${API_URL}/api/elite/personas/${testPersonaId}/test?test_message=${encodeURIComponent(testMessage)}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        setTestResult(result);
      } else {
        toast.error('Failed to test persona');
      }
    } catch (error) {
      toast.error('Failed to test persona');
    }
  };

  const resetNewPersona = () => {
    setNewPersona({
      name: '',
      description: '',
      tone: 'friendly',
      communication_style: 'conversational',
      response_length: 'medium',
      primary_focus_areas: ['content'],
      emoji_usage: 'moderate',
      custom_greeting: '',
      signature_phrase: '',
      personality_traits: [],
      custom_instructions: '',
      icon: 'user',
    });
  };

  const renderPersonaIcon = (iconName, size = 'h-6 w-6') => {
    const IconComponent = iconMap[iconName] || User;
    return <IconComponent className={size} />;
  };

  const PersonaCard = ({ persona, isDefault = false }) => {
    const isActive = activePersona?.id === persona.id;
    
    return (
      <Card 
        className={`relative transition-all cursor-pointer hover:border-purple-500/50 ${
          isActive ? 'border-purple-500 bg-purple-500/10' : 'bg-gray-900/50 border-gray-800'
        }`}
        onClick={() => !isActive && activatePersona(persona.id)}
        data-testid={`persona-card-${persona.id}`}
      >
        {isActive && (
          <div className="absolute top-2 right-2">
            <Badge className="bg-purple-600 text-white">
              <Check className="h-3 w-3 mr-1" /> Active
            </Badge>
          </div>
        )}
        
        <CardHeader className="pb-2">
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
              isActive ? 'bg-purple-600' : 'bg-gray-800'
            }`}>
              {renderPersonaIcon(persona.icon)}
            </div>
            <div>
              <CardTitle className="text-white text-lg">{persona.name}</CardTitle>
              <div className="flex gap-2 mt-1">
                <Badge variant="outline" className="text-xs capitalize">
                  {persona.tone}
                </Badge>
                {isDefault && (
                  <Badge className="bg-gray-700 text-gray-300 text-xs">Default</Badge>
                )}
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <p className="text-sm text-gray-400 line-clamp-2">{persona.description}</p>
          
          <div className="mt-3 flex flex-wrap gap-1">
            {persona.primary_focus_areas?.slice(0, 3).map((area, i) => (
              <Badge key={i} variant="secondary" className="text-xs bg-gray-800 text-gray-300">
                {area.replace('_', ' ')}
              </Badge>
            ))}
          </div>
          
          {!isDefault && (
            <div className="mt-4 flex gap-2" onClick={(e) => e.stopPropagation()}>
              <Button 
                size="sm" 
                variant="outline"
                onClick={() => setEditingPersona(persona)}
                data-testid={`edit-persona-${persona.id}`}
              >
                <Edit2 className="h-3 w-3 mr-1" /> Edit
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setTestPersonaId(persona.id);
                  setShowTestDialog(true);
                }}
                data-testid={`test-persona-${persona.id}`}
              >
                <TestTube className="h-3 w-3 mr-1" /> Test
              </Button>
              <Button
                size="sm"
                variant="destructive"
                onClick={() => deletePersona(persona.id)}
                data-testid={`delete-persona-${persona.id}`}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          )}
          
          {isDefault && (
            <div className="mt-4 flex gap-2" onClick={(e) => e.stopPropagation()}>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setTestPersonaId(persona.id);
                  setShowTestDialog(true);
                }}
              >
                <TestTube className="h-3 w-3 mr-1" /> Test
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="arris-persona-manager">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-purple-400" />
            ARRIS Personas
          </h2>
          <p className="text-gray-400 mt-1">
            Customize how ARRIS communicates with you
          </p>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-purple-600 hover:bg-purple-700" data-testid="create-persona-btn">
              <Plus className="h-4 w-4 mr-2" /> Create Custom Persona
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-gray-900 border-gray-800 max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-white">Create Custom ARRIS Persona</DialogTitle>
              <DialogDescription>
                Design your perfect AI assistant personality
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Persona Name *</Label>
                  <Input
                    value={newPersona.name}
                    onChange={(e) => setNewPersona({...newPersona, name: e.target.value})}
                    placeholder="e.g., Strategy Expert"
                    className="bg-gray-800 border-gray-700"
                    data-testid="persona-name-input"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label>Icon</Label>
                  <Select
                    value={newPersona.icon}
                    onValueChange={(value) => setNewPersona({...newPersona, icon: value})}
                  >
                    <SelectTrigger className="bg-gray-800 border-gray-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {options?.icon_options?.map((icon) => (
                        <SelectItem key={icon} value={icon}>
                          <div className="flex items-center gap-2">
                            {renderPersonaIcon(icon, 'h-4 w-4')}
                            <span className="capitalize">{icon}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea
                  value={newPersona.description}
                  onChange={(e) => setNewPersona({...newPersona, description: e.target.value})}
                  placeholder="Describe what this persona is best for..."
                  className="bg-gray-800 border-gray-700"
                  rows={2}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Tone</Label>
                  <Select
                    value={newPersona.tone}
                    onValueChange={(value) => setNewPersona({...newPersona, tone: value})}
                  >
                    <SelectTrigger className="bg-gray-800 border-gray-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {options?.tones?.map((tone) => (
                        <SelectItem key={tone} value={tone}>
                          <span className="capitalize">{tone}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500">{toneDescriptions[newPersona.tone]}</p>
                </div>
                
                <div className="space-y-2">
                  <Label>Communication Style</Label>
                  <Select
                    value={newPersona.communication_style}
                    onValueChange={(value) => setNewPersona({...newPersona, communication_style: value})}
                  >
                    <SelectTrigger className="bg-gray-800 border-gray-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {options?.communication_styles?.map((style) => (
                        <SelectItem key={style} value={style}>
                          <span className="capitalize">{style}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-gray-500">{styleDescriptions[newPersona.communication_style]}</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Response Length</Label>
                  <Select
                    value={newPersona.response_length}
                    onValueChange={(value) => setNewPersona({...newPersona, response_length: value})}
                  >
                    <SelectTrigger className="bg-gray-800 border-gray-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {options?.response_lengths?.map((len) => (
                        <SelectItem key={len} value={len}>
                          <span className="capitalize">{len}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label>Emoji Usage</Label>
                  <Select
                    value={newPersona.emoji_usage}
                    onValueChange={(value) => setNewPersona({...newPersona, emoji_usage: value})}
                  >
                    <SelectTrigger className="bg-gray-800 border-gray-700">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {options?.emoji_options?.map((opt) => (
                        <SelectItem key={opt} value={opt}>
                          <span className="capitalize">{opt}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Focus Areas (select multiple)</Label>
                <div className="flex flex-wrap gap-2">
                  {options?.focus_areas?.map((area) => (
                    <Badge
                      key={area}
                      className={`cursor-pointer ${
                        newPersona.primary_focus_areas.includes(area)
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                      onClick={() => {
                        const areas = newPersona.primary_focus_areas.includes(area)
                          ? newPersona.primary_focus_areas.filter(a => a !== area)
                          : [...newPersona.primary_focus_areas, area];
                        setNewPersona({...newPersona, primary_focus_areas: areas});
                      }}
                    >
                      {area.replace('_', ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>Custom Greeting</Label>
                <Input
                  value={newPersona.custom_greeting}
                  onChange={(e) => setNewPersona({...newPersona, custom_greeting: e.target.value})}
                  placeholder="How should ARRIS greet you?"
                  className="bg-gray-800 border-gray-700"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Signature Phrase</Label>
                <Input
                  value={newPersona.signature_phrase}
                  onChange={(e) => setNewPersona({...newPersona, signature_phrase: e.target.value})}
                  placeholder="A phrase ARRIS might occasionally use"
                  className="bg-gray-800 border-gray-700"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Custom Instructions (Advanced)</Label>
                <Textarea
                  value={newPersona.custom_instructions}
                  onChange={(e) => setNewPersona({...newPersona, custom_instructions: e.target.value})}
                  placeholder="Any additional instructions for how ARRIS should behave..."
                  className="bg-gray-800 border-gray-700"
                  rows={3}
                />
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancel
              </Button>
              <Button onClick={createPersona} className="bg-purple-600 hover:bg-purple-700" data-testid="save-persona-btn">
                Create Persona
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Active Persona Banner */}
      {activePersona && (
        <Card className="bg-gradient-to-r from-purple-900/50 to-indigo-900/50 border-purple-700/30">
          <CardContent className="py-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-purple-600 flex items-center justify-center">
                {renderPersonaIcon(activePersona.icon, 'h-7 w-7')}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-semibold text-white">{activePersona.name}</h3>
                  <Badge className="bg-green-600">Active</Badge>
                </div>
                <p className="text-sm text-purple-200">{activePersona.description}</p>
                {activePersona.custom_greeting && (
                  <p className="text-sm text-gray-400 mt-1 italic">
                    <MessageSquare className="h-3 w-3 inline mr-1" />
                    {activePersona.custom_greeting}
                  </p>
                )}
              </div>
              <Button
                variant="outline"
                onClick={() => {
                  setTestPersonaId(activePersona.id);
                  setShowTestDialog(true);
                }}
              >
                <Settings2 className="h-4 w-4 mr-2" /> Configure
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Persona Tabs */}
      <Tabs defaultValue="default" className="w-full">
        <TabsList className="bg-gray-900/50 border border-gray-800">
          <TabsTrigger value="default" data-testid="default-personas-tab">
            Default Personas ({personas.default_personas?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="custom" data-testid="custom-personas-tab">
            My Personas ({personas.custom_personas?.length || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="default" className="mt-4">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {personas.default_personas?.map((persona) => (
              <PersonaCard key={persona.id} persona={persona} isDefault />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="custom" className="mt-4">
          {personas.custom_personas?.length === 0 ? (
            <Card className="bg-gray-900/50 border-gray-800">
              <CardContent className="py-12 text-center">
                <Sparkles className="h-12 w-12 mx-auto mb-4 text-purple-400 opacity-50" />
                <h3 className="text-lg font-medium text-white mb-2">No Custom Personas Yet</h3>
                <p className="text-gray-400 mb-4">
                  Create your first custom ARRIS persona to personalize your AI assistant experience.
                </p>
                <Button
                  onClick={() => setShowCreateDialog(true)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Plus className="h-4 w-4 mr-2" /> Create Your First Persona
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {personas.custom_personas?.map((persona) => (
                <PersonaCard key={persona.id} persona={persona} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Test Dialog */}
      <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
        <DialogContent className="bg-gray-900 border-gray-800 max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white">Test Persona</DialogTitle>
            <DialogDescription>
              See how ARRIS would respond with this persona
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Test Message</Label>
              <Textarea
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                placeholder="Enter a message to see how ARRIS would respond..."
                className="bg-gray-800 border-gray-700"
                rows={3}
                data-testid="test-message-input"
              />
            </div>
            
            <Button onClick={testPersona} className="w-full" data-testid="run-test-btn">
              <TestTube className="h-4 w-4 mr-2" /> Run Test
            </Button>
            
            {testResult && (
              <div className="mt-4 space-y-4">
                <div>
                  <Label className="text-purple-400">Active Persona</Label>
                  <p className="text-white">{testResult.persona?.name}</p>
                </div>
                <div>
                  <Label className="text-purple-400">System Prompt Preview</Label>
                  <pre className="mt-2 p-3 bg-gray-800 rounded-lg text-xs text-gray-300 whitespace-pre-wrap max-h-48 overflow-y-auto">
                    {testResult.system_prompt_preview}
                  </pre>
                </div>
                <p className="text-xs text-gray-500">
                  Note: This shows the configuration. Full AI responses will use this prompt.
                </p>
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowTestDialog(false);
              setTestResult(null);
              setTestMessage('');
            }}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
