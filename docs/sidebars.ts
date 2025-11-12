import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    // Overview
    {
      type: 'category',
      label: 'Overview',
      collapsed: false,
      items: [
        'overview/index',
        'intro',
      ],
    },

    // Architecture
    {
      type: 'category',
      label: 'Architecture',
      items: [
        'architecture/system-design',
        'architecture/agents',
      ],
    },

    // API Documentation
    {
      type: 'category',
      label: 'API Documentation',
      items: [
        'api-reference',
        'authentication',
        'chat-api',
        'examples',
      ],
    },

    // Development
    {
      type: 'category',
      label: 'Development',
      items: [
        'development/local-setup',
        'setup',
      ],
    },

    // Deployment
    {
      type: 'category',
      label: 'Deployment',
      items: [
        'deployment/aws-infrastructure',
        'deployment/security',
      ],
    },

    // Operations
    {
      type: 'category',
      label: 'Operations',
      items: [
        'operations/monitoring',
        'troubleshooting',
        'working-sessions',
      ],
    },
  ],
};

export default sidebars;