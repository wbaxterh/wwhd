'use client';

import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-background to-secondary">
        <div className="container mx-auto px-4 py-20">
          <div className="text-center">
            <h1 className="hero-title text-foreground mb-4">
              W.W.H.D.
            </h1>
            <p className="text-xl text-muted-foreground mb-4">
              What Would Herman Do?
            </p>
            <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
              AI-powered wisdom companion combining ancient Shaolin philosophy with modern technology
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/chat"
                className="inline-flex items-center justify-center px-8 py-3 text-base font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-colors"
              >
                Start Chatting
              </Link>
              <a
                href="http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center px-8 py-3 text-base font-medium text-primary bg-transparent border border-primary rounded-md hover:bg-primary hover:text-primary-foreground transition-colors"
              >
                API Documentation
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-background">
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-foreground mb-4">
              What You Get
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="p-6 bg-card border border-border rounded-lg">
              <div className="text-2xl mb-4">🔐</div>
              <h3 className="text-xl font-semibold text-foreground mb-2">JWT Authentication</h3>
              <p className="text-muted-foreground">Secure user management and API access</p>
            </div>
            <div className="p-6 bg-card border border-border rounded-lg">
              <div className="text-2xl mb-4">💬</div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Intelligent Chat</h3>
              <p className="text-muted-foreground">AI-powered responses with Herman's personality</p>
            </div>
            <div className="p-6 bg-card border border-border rounded-lg">
              <div className="text-2xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Agent Routing</h3>
              <p className="text-muted-foreground">Specialized handlers for different topics</p>
            </div>
            <div className="p-6 bg-card border border-border rounded-lg">
              <div className="text-2xl mb-4">📚</div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Knowledge Base</h3>
              <p className="text-muted-foreground">RAG-powered responses from curated content</p>
            </div>
            <div className="p-6 bg-card border border-border rounded-lg">
              <div className="text-2xl mb-4">⚡</div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Real-time API</h3>
              <p className="text-muted-foreground">Fast, reliable streaming responses</p>
            </div>
            <div className="p-6 bg-card border border-border rounded-lg">
              <div className="text-2xl mb-4">📖</div>
              <h3 className="text-xl font-semibold text-foreground mb-2">Full Documentation</h3>
              <p className="text-muted-foreground">Complete guides and examples</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}