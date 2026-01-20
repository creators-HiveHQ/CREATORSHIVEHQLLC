/**
 * ARRIS Voice Interaction Component
 * Premium feature for voice conversations with ARRIS AI
 */

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Mic, MicOff, Volume2, VolumeX, Loader2, Play, Square, Sparkles } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export function ArrisVoiceInteraction({ token, creatorTier, onUpgrade }) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState(null);
  const [selectedVoice, setSelectedVoice] = useState("nova");
  const [conversation, setConversation] = useState([]);
  const [error, setError] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioRef = useRef(null);
  const streamRef = useRef(null);

  // Check if user has Premium access
  const hasPremiumAccess = ["premium", "elite"].includes(creatorTier?.toLowerCase());

  // Fetch voice service status on mount
  useEffect(() => {
    if (hasPremiumAccess && token) {
      fetchVoiceStatus();
    }
  }, [hasPremiumAccess, token]);

  const fetchVoiceStatus = async () => {
    try {
      const response = await fetch(`${API}/arris/voice/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setVoiceStatus(data);
      if (data.default_voice) {
        setSelectedVoice(data.default_voice);
      }
    } catch (err) {
      console.error("Failed to fetch voice status:", err);
    }
  };

  const startRecording = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        await sendVoiceQuery(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      setError("Microphone access denied. Please allow microphone permissions.");
      console.error("Recording error:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop all tracks
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    }
  };

  const sendVoiceQuery = async (audioBlob) => {
    setIsProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      const response = await fetch(
        `${API}/arris/voice/query?respond_with_voice=true&voice=${selectedVoice}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formData
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || 'Voice query failed');
      }

      const result = await response.json();
      
      // Add to conversation
      const newMessage = {
        id: Date.now(),
        userQuery: result.transcription?.text || "...",
        arrisResponse: result.arris_response?.text || "I couldn't process that. Please try again.",
        audioBase64: result.audio_response?.audio_base64,
        audioFormat: result.audio_response?.audio_format || "mp3",
        timestamp: new Date().toISOString(),
        processingTime: result.total_processing_time
      };
      
      setConversation(prev => [...prev, newMessage]);

      // Auto-play response
      if (newMessage.audioBase64) {
        playAudio(newMessage.audioBase64, newMessage.audioFormat);
      }

    } catch (err) {
      setError(err.message || "Failed to process voice query");
      console.error("Voice query error:", err);
    } finally {
      setIsProcessing(false);
    }
  };

  const playAudio = (base64Audio, format = "mp3") => {
    try {
      const audioData = `data:audio/${format};base64,${base64Audio}`;
      
      if (audioRef.current) {
        audioRef.current.pause();
      }
      
      const audio = new Audio(audioData);
      audioRef.current = audio;
      
      audio.onplay = () => setIsPlaying(true);
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => {
        setIsPlaying(false);
        setError("Failed to play audio response");
      };
      
      audio.play();
    } catch (err) {
      console.error("Audio playback error:", err);
      setError("Failed to play audio response");
    }
  };

  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setIsPlaying(false);
    }
  };

  const clearConversation = () => {
    setConversation([]);
    setError(null);
  };

  // Non-Premium upgrade prompt
  if (!hasPremiumAccess) {
    return (
      <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200" data-testid="voice-upgrade-prompt">
        <CardContent className="py-12 text-center">
          <div className="mx-auto w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mb-6">
            <Mic className="w-10 h-10 text-purple-600" />
          </div>
          <h2 className="text-2xl font-bold text-purple-800 mb-3">Voice Interaction with ARRIS</h2>
          <p className="text-purple-600 max-w-md mx-auto mb-6">
            Have natural voice conversations with ARRIS AI! Ask questions, get insights, 
            and receive spoken responses - all hands-free.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto mb-8">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <Mic className="w-6 h-6 mx-auto text-purple-500" />
              <p className="text-xs text-slate-600 mt-2">Voice Input</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <Volume2 className="w-6 h-6 mx-auto text-purple-500" />
              <p className="text-xs text-slate-600 mt-2">Audio Response</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <Sparkles className="w-6 h-6 mx-auto text-purple-500" />
              <p className="text-xs text-slate-600 mt-2">AI Insights</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <span className="text-2xl">🎯</span>
              <p className="text-xs text-slate-600 mt-2">Hands-Free</p>
            </div>
          </div>
          <Badge className="bg-amber-100 text-amber-800 mb-4">Premium Feature</Badge>
          <br />
          <Button 
            onClick={onUpgrade}
            className="bg-purple-600 hover:bg-purple-700 mt-4"
            data-testid="upgrade-to-premium-btn"
          >
            ⚡ Upgrade to Premium
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4" data-testid="arris-voice-interaction">
      {/* Voice Control Panel */}
      <Card className="bg-gradient-to-br from-purple-50 to-indigo-50 border-purple-200">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <CardTitle className="text-lg text-purple-800">Talk to ARRIS</CardTitle>
              <Badge className="bg-purple-100 text-purple-700">Premium</Badge>
            </div>
            {conversation.length > 0 && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={clearConversation}
                className="text-purple-600 hover:text-purple-800"
              >
                Clear Chat
              </Button>
            )}
          </div>
          <CardDescription>
            Press and hold the microphone to ask ARRIS anything about your projects or business
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Voice Selection */}
          <div className="flex items-center gap-4 mb-6">
            <Label className="text-sm text-slate-600">ARRIS Voice:</Label>
            <Select value={selectedVoice} onValueChange={setSelectedVoice}>
              <SelectTrigger className="w-40" data-testid="voice-selector">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {voiceStatus?.voices?.map((voice) => (
                  <SelectItem key={voice.id} value={voice.id}>
                    {voice.name}
                  </SelectItem>
                )) || (
                  <>
                    <SelectItem value="nova">Nova (Energetic)</SelectItem>
                    <SelectItem value="alloy">Alloy (Neutral)</SelectItem>
                    <SelectItem value="echo">Echo (Calm)</SelectItem>
                    <SelectItem value="fable">Fable (Expressive)</SelectItem>
                    <SelectItem value="shimmer">Shimmer (Bright)</SelectItem>
                  </>
                )}
              </SelectContent>
            </Select>
          </div>

          {/* Record Button */}
          <div className="flex flex-col items-center gap-4">
            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onMouseLeave={() => isRecording && stopRecording()}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              disabled={isProcessing}
              className={`
                w-24 h-24 rounded-full flex items-center justify-center transition-all duration-200
                ${isRecording 
                  ? 'bg-red-500 scale-110 shadow-lg shadow-red-300 animate-pulse' 
                  : isProcessing 
                    ? 'bg-purple-300 cursor-wait'
                    : 'bg-purple-600 hover:bg-purple-700 hover:scale-105 shadow-md'
                }
              `}
              data-testid="record-button"
            >
              {isProcessing ? (
                <Loader2 className="w-10 h-10 text-white animate-spin" />
              ) : isRecording ? (
                <MicOff className="w-10 h-10 text-white" />
              ) : (
                <Mic className="w-10 h-10 text-white" />
              )}
            </button>
            <p className="text-sm text-slate-500">
              {isProcessing 
                ? "Processing your question..." 
                : isRecording 
                  ? "🔴 Recording... Release to send" 
                  : "Hold to speak"
              }
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" data-testid="voice-error">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Conversation History */}
      {conversation.length > 0 && (
        <Card data-testid="conversation-history">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Conversation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 max-h-96 overflow-y-auto">
            {conversation.map((msg) => (
              <div key={msg.id} className="space-y-3">
                {/* User Message */}
                <div className="flex justify-end">
                  <div className="bg-purple-100 rounded-lg px-4 py-2 max-w-[80%]">
                    <p className="text-sm text-purple-900">{msg.userQuery}</p>
                  </div>
                </div>
                
                {/* ARRIS Response */}
                <div className="flex justify-start gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                  <div className="bg-slate-100 rounded-lg px-4 py-2 max-w-[80%]">
                    <p className="text-sm text-slate-800">{msg.arrisResponse}</p>
                    <div className="flex items-center gap-2 mt-2">
                      {msg.audioBase64 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => isPlaying ? stopAudio() : playAudio(msg.audioBase64, msg.audioFormat)}
                          className="h-7 px-2"
                          data-testid="play-audio-btn"
                        >
                          {isPlaying ? (
                            <><Square className="w-3 h-3 mr-1" /> Stop</>
                          ) : (
                            <><Play className="w-3 h-3 mr-1" /> Play</>
                          )}
                        </Button>
                      )}
                      {msg.processingTime && (
                        <span className="text-xs text-slate-400">{msg.processingTime}s</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Tips Card */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="py-4">
          <p className="text-sm font-medium text-slate-700 mb-2">💡 Tips for best results:</p>
          <ul className="text-xs text-slate-600 space-y-1">
            <li>• Speak clearly and at a natural pace</li>
            <li>• Ask specific questions about your projects or strategy</li>
            <li>• Background noise may affect transcription quality</li>
            <li>• Try different voices to find your preferred ARRIS personality</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

export default ArrisVoiceInteraction;
