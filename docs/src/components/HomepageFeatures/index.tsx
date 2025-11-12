import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  icon: string;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'AI-Powered Wisdom',
    icon: '🧘',
    description: (
      <>
        Tap into centuries of Shaolin and Traditional Chinese Medicine wisdom
        through modern AI technology. Get personalized guidance for life's challenges.
      </>
    ),
  },
  {
    title: 'Multi-Agent System',
    icon: '🔄',
    description: (
      <>
        Intelligent routing system directs your questions to specialized agents
        for meditation, relationships, health, and general life guidance.
      </>
    ),
  },
  {
    title: 'REST API Ready',
    icon: '⚡',
    description: (
      <>
        Production-ready API with JWT authentication, comprehensive documentation,
        and Postman collection for easy integration into your applications.
      </>
    ),
  },
];

function Feature({title, icon, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center feature-card">
        <div className={styles.featureIcon}>{icon}</div>
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}