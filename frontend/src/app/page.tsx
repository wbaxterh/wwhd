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
                className="inline-flex items-center justify-center px-8 py-3 text-base font-medium text-slate-900 bg-white rounded-md hover:bg-slate-100 transition-colors shadow-lg"
              >
                Start Chatting
              </Link>
              <Link
                href="/knowledgebase"
                className="inline-flex items-center justify-center px-8 py-3 text-base font-medium text-white bg-transparent border-2 border-white rounded-md hover:bg-white hover:text-slate-900 transition-colors"
              >
                Knowledge Base
              </Link>
            </div>
          </div>
        </div>
      </section>

    </div>
  )
}