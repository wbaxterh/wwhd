'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/auth';
import { AuthModal } from '@/components/AuthModal';
import { ThemeToggle } from '@/components/ThemeToggle';
import ReactMarkdown from 'react-markdown';
import { User, Bot, ArrowLeft, Database } from 'lucide-react';

interface Citation {
  title: string;
  url: string;
  timestamp?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

// Custom markdown components for better styling
function MarkdownRenderer({ content }: { content: string }) {
  return (
    <ReactMarkdown
      components={{
        // Style blockquotes (direct quotes) with special background
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-primary/50 bg-primary/5 dark:bg-primary/10 pl-4 py-2 my-2 italic">
            {children}
          </blockquote>
        ),
        // Style code blocks
        code: ({ className, children, ...props }) => {
          const match = /language-(\w+)/.exec(className || '');
          return (
            <code
              className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono"
              {...props}
            >
              {children}
            </code>
          );
        },
        // Style inline code
        p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
        // Style headings
        h1: ({ children }) => <h1 className="text-xl font-bold mb-3">{children}</h1>,
        h2: ({ children }) => <h2 className="text-lg font-semibold mb-2">{children}</h2>,
        h3: ({ children }) => <h3 className="text-md font-medium mb-2">{children}</h3>,
        // Style lists
        ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
        // Style emphasis
        em: ({ children }) => <em className="italic text-primary">{children}</em>,
        strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function ChatInterface() {
  const { token, isAuthenticated } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setShowAuthModal(true);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const backendUrl = 'https://api.weshuber.com';
      const response = await fetch(`${backendUrl}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` }),
        },
        body: JSON.stringify({
          content: input
        }),
      });

      if (!response.ok) {
        if (response.status === 503) {
          const errorData = await response.json();
          throw new Error(errorData.message || 'Backend service is unavailable');
        }
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMessage = '';
      let citations: Citation[] = [];

      const assistantMessageObj: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '',
        citations: []
      };

      setMessages(prev => [...prev, assistantMessageObj]);
      setIsStreaming(true);

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '') continue;

              try {
                const parsed = JSON.parse(data);
                if (parsed.type === 'token' && parsed.content) {
                  assistantMessage += parsed.content;
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageObj.id
                      ? { ...msg, content: assistantMessage }
                      : msg
                  ));
                } else if (parsed.type === 'citation' && parsed.citations) {
                  citations = parsed.citations;
                  setMessages(prev => prev.map(msg =>
                    msg.id === assistantMessageObj.id
                      ? { ...msg, citations: citations }
                      : msg
                  ));
                } else if (parsed.type === 'done') {
                  break;
                }
              } catch (e) {
                // Skip invalid JSON
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    }

    setIsLoading(false);
    setIsStreaming(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground mt-20">
            <div className="max-w-md mx-auto">
              <Bot className="h-12 w-12 mx-auto mb-4 text-primary" />
              <h3 className="text-xl font-semibold mb-2">Welcome to W.W.H.D.</h3>
              <p className="text-sm">Ask Herman for wisdom and guidance. What's on your mind?</p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className="w-full">
            <div className={`flex gap-4 max-w-none sm:max-w-4xl mx-auto ${
              message.role === 'user' ? 'flex-row-reverse' : 'flex-row'
            }`}>
              {/* Avatar */}
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
              }`}>
                {message.role === 'user' ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </div>

              {/* Message Content */}
              <div className={`flex-1 min-w-0 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                <div className={`inline-block max-w-full rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted/50 text-foreground'
                }`}>
                  <div className="text-xs font-medium mb-2 opacity-70">
                    {message.role === 'user' ? 'You' : 'Herman'}
                  </div>

                  {message.role === 'assistant' ? (
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <MarkdownRenderer content={message.content} />
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                      {message.content}
                    </div>
                  )}

                  {/* Citations */}
                  {message.citations && message.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-border/20">
                      <div className="text-xs font-medium mb-2 text-muted-foreground">Sources:</div>
                      <div className="space-y-1">
                        {message.citations.map((citation, index) => (
                          <div key={index} className="text-xs">
                            <span className="font-medium">{index + 1}. </span>
                            {citation.url ? (
                              <a
                                href={citation.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline"
                              >
                                {citation.title}
                              </a>
                            ) : (
                              <span>{citation.title}</span>
                            )}
                            {citation.timestamp && (
                              <span className="text-muted-foreground"> (@{citation.timestamp})</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Loading Animation */}
        {isLoading && !isStreaming && (
          <div className="w-full">
            <div className="flex gap-4 max-w-none sm:max-w-4xl mx-auto">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <div className="inline-block bg-muted/50 rounded-lg px-4 py-3">
                  <div className="text-xs font-medium mb-2 opacity-70">Herman</div>
                  <div className="flex items-center space-x-1">
                    <div className="w-2 h-2 bg-current rounded-full animate-bounce opacity-60" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-current rounded-full animate-bounce opacity-60" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-current rounded-full animate-bounce opacity-60" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <div className="border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-3">
            <div className="flex-1 min-w-0">
              <textarea
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Ask Herman for wisdom..."
                className="w-full min-h-[48px] max-h-32 px-4 py-3 bg-background border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 text-foreground placeholder:text-muted-foreground resize-none"
                rows={1}
                style={{
                  height: 'auto',
                  minHeight: '48px'
                }}
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-xl hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
          <div className="text-xs text-muted-foreground mt-2 text-center">
            Press Enter to send, Shift + Enter for new line
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <div className="h-screen bg-background flex flex-col">
      <header className="border-b border-border bg-card/50 backdrop-blur supports-[backdrop-filter]:bg-card/50 flex-shrink-0">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Bot className="h-6 w-6 text-primary" />
              <h1 className="text-xl font-bold text-foreground">W.W.H.D.</h1>
              <span className="text-sm text-muted-foreground hidden sm:block">Chat with Herman</span>
            </div>
            <div className="flex items-center space-x-3">
              <a
                href="/knowledgebase"
                className="flex items-center gap-2 px-3 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              >
                <Database className="h-4 w-4" />
                <span className="hidden sm:inline">Knowledge Base</span>
              </a>
              <ThemeToggle />
              <a
                href="/"
                className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground border border-border rounded-lg hover:bg-muted transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                <span className="hidden sm:inline">Home</span>
              </a>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 flex">
        <ChatInterface />
      </main>
    </div>
  );
}