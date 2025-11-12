import type {ReactNode} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import HomepageFeatures from '@site/src/components/HomepageFeatures';
import Heading from '@theme/Heading';

import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          W.W.H.D.
        </Heading>
        <p className="hero__subtitle">What Would Herman Do?</p>
        <p className="hero__subtitle" style={{fontSize: '1rem', marginBottom: '2rem'}}>
          AI-powered wisdom companion combining ancient Shaolin philosophy with modern technology
        </p>
        <div className={styles.buttons}>
          <Link
            className="button button--primary button--lg"
            to="/docs/intro">
            Get Started
          </Link>
          <Link
            className="button button--secondary button--lg"
            to="/docs/api-reference"
            style={{marginLeft: '1rem'}}>
            API Documentation
          </Link>
        </div>
        <div className={styles.quickStats}>
          <div className={styles.stat}>
            <strong>Live API</strong>
            <br />
            <small>Production Ready</small>
          </div>
          <div className={styles.stat}>
            <strong>Multi-Agent</strong>
            <br />
            <small>Intelligent Routing</small>
          </div>
          <div className={styles.stat}>
            <strong>OpenAI Powered</strong>
            <br />
            <small>GPT-4 Integration</small>
          </div>
        </div>
      </div>
    </header>
  );
}

function QuickStart() {
  const postmanUrl = useBaseUrl('/WWHD.postman_collection.json');
  return (
    <section className={styles.quickStart}>
      <div className="container">
        <div className="row">
          <div className="col col--6">
            <Heading as="h2">Quick Start</Heading>
            <p>Get up and running with the W.W.H.D. API in minutes:</p>
            <pre className={styles.codeBlock}>
              <code>{`# 1. Register a user
curl -X POST \\
  http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"username": "seeker", "email": "seeker@example.com",
       "password": "WisdomPath123", "name": "Wisdom Seeker"}'

# 2. Get authentication token
curl -X POST \\
  http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/auth/token \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "username=seeker&password=WisdomPath123"

# 3. Chat with Herman
curl -X POST \\
  http://wwhd-alb-1530831557.us-west-2.elb.amazonaws.com/api/v1/chat/chat \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"content": "Hello Herman!", "chat_id": null}'`}</code>
            </pre>
          </div>
          <div className="col col--6">
            <Heading as="h2">What You Get</Heading>
            <ul className={styles.featureList}>
              <li><strong>🔐 JWT Authentication</strong> - Secure user management</li>
              <li><strong>💬 Intelligent Chat</strong> - AI-powered responses with Herman's personality</li>
              <li><strong>🎯 Agent Routing</strong> - Specialized handlers for different topics</li>
              <li><strong>📚 Knowledge Base</strong> - RAG-powered responses from curated content</li>
              <li><strong>⚡ Real-time API</strong> - Fast, reliable responses</li>
              <li><strong>📖 Full Documentation</strong> - Complete guides and examples</li>
            </ul>
            <div className={styles.downloadSection}>
              <Heading as="h3">Download Resources</Heading>
              <a
                className="button button--outline button--primary"
                href={postmanUrl}
                download>
                📥 Postman Collection
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="AI Wisdom Companion"
      description="What Would Herman Do? - AI-powered wisdom companion combining ancient Shaolin philosophy with modern technology. Production-ready API with intelligent agent routing.">
      <HomepageHeader />
      <main>
        <HomepageFeatures />
        <QuickStart />
      </main>
    </Layout>
  );
}