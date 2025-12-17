# AWS Infrastructure Costs & Pricing Strategy

## Executive Summary

**Current WWHD Infrastructure Cost: $40/month**
- ECS Fargate + Qdrant: $20/month
- Application Load Balancer: $20/month
- Storage & Monitoring: <$1/month

**Key Insight**: With infrastructure costs this low, the application is profitable from day 1 with just 5 paid users at $9.99/month.

## WWHD Application Infrastructure

### Current Infrastructure Components

Based on AWS CLI analysis, the WWHD application uses:

| Component | Service | Details |
|-----------|---------|---------|
| **Backend API** | ECS Fargate | 1 task (1024 CPU, 2048 MB memory) |
| **Vector Database** | Qdrant on ECS | Sidecar container (256 CPU, 512 MB) |
| **Load Balancer** | ALB | wwhd-alb-1530831557.us-west-2.elb.amazonaws.com |
| **Container Registry** | ECR | wwhd-dev-backend repository |
| **Persistent Storage** | EFS | 2 file systems (wwhd-data: 64MB, wwhd-database: 6KB) |
| **Frontend** | Amplify | wwhd-frontend app |
| **API Domain** | Route 53 | api.weshuber.com |

## Actual WWHD Monthly Costs

### Estimated Monthly Cost: ~$35-40 USD

#### Detailed Cost Breakdown

| Service | Monthly Cost | Calculation | Purpose |
|---------|-------------|-------------|----------|
| **ECS Fargate** | | | |
| vCPU hours | $12.24 | 1.0 vCPU × 730 hrs × $0.04048 | Backend compute |
| Memory GB hours | $7.30 | 2 GB × 730 hrs × $0.004445 | Backend memory |
| **Application Load Balancer** | | | |
| ALB hours | $18.25 | 730 hrs × $0.025 | Load balancing |
| LCU hours | $1.46 | 730 hrs × $0.008 × 0.25 LCU | Minimal traffic |
| **EFS Storage** | | | |
| Storage (Standard) | $0.02 | 0.064 GB × $0.30/GB | SQLite + Qdrant data |
| **ECR** | | | |
| Storage | $0.05 | ~0.5 GB × $0.10/GB | Docker images |
| **Amplify** | | | |
| Build minutes | $0.00 | Free tier (1000 min/month) | Frontend builds |
| Hosting | $0.01 | ~1 GB served × $0.01/GB | Static hosting |
| **CloudWatch** | | | |
| Logs | $0.50 | ~1 GB ingestion × $0.50 | Application logs |
| **Data Transfer** | | | |
| ALB to Internet | $0.00 | First 1 GB free | Minimal traffic |

### **Total: ~$35/month**

### Cost Analysis

#### Fixed Costs (Always incurred)
- ECS Fargate (minimum 1 task): ~$20/month
- ALB (always running): ~$18/month
- **Total Fixed: ~$38/month**

#### Variable Costs (Scale with usage)
- EFS storage: ~$0.02/month (grows with data)
- ECR storage: ~$0.05/month (grows with images)
- CloudWatch logs: ~$0.50/month (grows with traffic)
- Data transfer: ~$0/month (currently minimal)
- **Total Variable: ~$0.60/month**

### Projected Costs at Scale

| Users | Monthly AWS Cost | Cost per User | Notes |
|-------|------------------|---------------|-------|
| 10 | $40 | $4.00 | Current infrastructure |
| 50 | $45 | $0.90 | +CloudWatch logs, data transfer |
| 100 | $55 | $0.55 | +1 ECS task for scaling |
| 500 | $150 | $0.30 | +2 ECS tasks, larger EFS |
| 1000 | $300 | $0.30 | +4 ECS tasks, RDS/managed Qdrant |

*Note: Major cost jumps occur when adding ECS tasks for scaling*

## Pricing Strategy

### Target Break-Even Analysis

To break even at current costs ($40/month):
- **5 users**: Need $8/user
- **10 users**: Need $4/user
- **20 users**: Need $2/user

### Recommended Pricing Tiers

#### 1. **Free Tier** (User Acquisition)
- **Price**: $0/month
- **Limits**:
  - 10 questions per day
  - Access to shared knowledge base (read-only)
  - 7-day chat history
  - Basic response speed
- **Purpose**: User acquisition and trial

#### 2. **Personal Plan** (Individual Users)
- **Price**: $9.99/month
- **Features**:
  - Unlimited questions
  - Full chat history
  - Priority response speed
  - Export chat history
  - Email support
- **Target**: Individual professionals

#### 3. **Professional Plan** (Power Users)
- **Price**: $19.99/month
- **Features**:
  - Everything in Personal
  - Custom knowledge base namespace
  - Upload up to 50 documents/month
  - API access (1000 calls/month)
  - Advanced analytics
  - Priority support
- **Target**: Consultants, researchers

#### 4. **Team Plan** (Small Teams)
- **Price**: $49.99/month (up to 5 users)
- **Features**:
  - Everything in Professional
  - 5 user accounts
  - Shared team knowledge base
  - Unlimited document uploads
  - Admin controls
  - Team analytics
  - Slack integration
- **Target**: Small businesses, teams

#### 5. **Enterprise Plan** (Large Organizations)
- **Price**: Custom (starting at $299/month)
- **Features**:
  - Unlimited users
  - Dedicated namespace
  - Custom integrations
  - SLA guarantees
  - Dedicated support
  - On-premise option
- **Target**: Enterprises

### Revenue Projections

| Scenario | Free | Personal | Professional | Team | Enterprise | Monthly Revenue | AWS Cost | Profit |
|----------|------|----------|--------------|------|------------|-----------------|----------|--------|
| **Conservative** | 50 | 5 | 2 | 1 | 0 | $140 | $40 | $100 |
| **Realistic** | 100 | 15 | 5 | 2 | 0 | $350 | $45 | $305 |
| **Optimistic** | 200 | 50 | 15 | 5 | 1 | $1,350 | $55 | $1,295 |

### Break-Even Points

- **Conservative**: Profitable from day 1 with just 5 paid users
- **Realistic**: Strong profit margin of 87% ($305 profit on $350 revenue)
- **Optimistic**: Excellent profit margin of 96% ($1,295 profit on $1,350 revenue)

## Stripe Implementation Plan

### Phase 1: Foundation (Week 1-2)

#### Backend Setup
1. **Install Stripe SDK**
   ```bash
   pip install stripe
   ```

2. **Database Schema Updates**
   ```sql
   -- Add to users table
   ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(50) DEFAULT 'free';
   ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(255);
   ALTER TABLE users ADD COLUMN subscription_status VARCHAR(50) DEFAULT 'inactive';
   ALTER TABLE users ADD COLUMN subscription_end_date TIMESTAMP;

   -- Create subscriptions table
   CREATE TABLE subscriptions (
     id INTEGER PRIMARY KEY,
     user_id INTEGER REFERENCES users(id),
     stripe_subscription_id VARCHAR(255),
     tier VARCHAR(50),
     status VARCHAR(50),
     current_period_start TIMESTAMP,
     current_period_end TIMESTAMP,
     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   -- Create usage_tracking table
   CREATE TABLE usage_tracking (
     id INTEGER PRIMARY KEY,
     user_id INTEGER REFERENCES users(id),
     date DATE,
     questions_asked INTEGER DEFAULT 0,
     documents_uploaded INTEGER DEFAULT 0,
     api_calls INTEGER DEFAULT 0
   );
   ```

3. **Environment Variables**
   ```bash
   STRIPE_SECRET_KEY=sk_live_xxx
   STRIPE_PUBLISHABLE_KEY=pk_live_xxx
   STRIPE_WEBHOOK_SECRET=whsec_xxx
   ```

### Phase 2: API Endpoints (Week 2-3)

#### New Endpoints to Implement

```python
# api/billing.py

@router.post("/create-checkout-session")
async def create_checkout_session(
    tier: str,
    current_user: User = Depends(get_current_user)
):
    """Create Stripe checkout session"""

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""

@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user)
):
    """Get user's current subscription"""

@router.post("/cancel-subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_user)
):
    """Cancel user's subscription"""

@router.get("/usage")
async def get_usage(
    current_user: User = Depends(get_current_user)
):
    """Get user's current usage stats"""
```

### Phase 3: Usage Limits & Enforcement (Week 3-4)

#### Middleware for Rate Limiting

```python
# middleware/subscription_limits.py

class SubscriptionLimiter:
    def __init__(self):
        self.limits = {
            'free': {
                'daily_questions': 10,
                'chat_history_days': 7,
                'monthly_uploads': 0,
                'api_calls': 0
            },
            'personal': {
                'daily_questions': None,  # Unlimited
                'chat_history_days': None,
                'monthly_uploads': 0,
                'api_calls': 0
            },
            'professional': {
                'daily_questions': None,
                'chat_history_days': None,
                'monthly_uploads': 50,
                'api_calls': 1000
            }
        }

    async def check_limit(self, user, action):
        """Check if user can perform action"""
        pass
```

### Phase 4: Frontend Integration (Week 4-5)

#### Components to Build

1. **Pricing Page** (`/pricing`)
   - Display pricing tiers
   - Feature comparison table
   - CTA buttons to upgrade

2. **Billing Dashboard** (`/account/billing`)
   - Current plan display
   - Usage statistics
   - Upgrade/downgrade options
   - Payment method management
   - Invoice history

3. **Upgrade Modal**
   - Triggered when hitting limits
   - Show benefits of upgrading
   - Direct checkout integration

### Phase 5: Testing & Launch (Week 5-6)

#### Testing Checklist

- [ ] Test all Stripe webhooks
- [ ] Test subscription creation flow
- [ ] Test upgrade/downgrade scenarios
- [ ] Test cancellation flow
- [ ] Test usage limit enforcement
- [ ] Test payment failure handling
- [ ] Test free tier limitations
- [ ] Test invoice generation

#### Launch Steps

1. **Soft Launch**
   - Enable for 10% of users
   - Monitor for issues
   - Gather feedback

2. **Full Launch**
   - Enable for all users
   - Announce pricing changes
   - Offer early-bird discounts

### Implementation Timeline

| Week | Phase | Tasks |
|------|-------|-------|
| 1-2 | Foundation | Database schema, Stripe setup, environment config |
| 2-3 | API | Build billing endpoints, webhook handlers |
| 3-4 | Limits | Implement usage tracking and enforcement |
| 4-5 | Frontend | Build pricing page, billing dashboard |
| 5-6 | Testing | Full testing suite, bug fixes |
| 6-7 | Launch | Soft launch, monitoring, full rollout |

### Cost-Benefit Analysis

#### Stripe Fees
- **Transaction fee**: 2.9% + $0.30 per transaction
- **Monthly revenue needed to cover AWS**: $40
- **After Stripe fees**: Need ~$45 in gross revenue (just 5 Personal users!)

#### Profitability Timeline
- **Day 1**: Profitable with just 5 paid users
- **Month 1**: Target $100+ profit (10 paid users)
- **Month 3**: Target $300+ profit (30 paid users)
- **Month 12**: Target $1000+ monthly profit (100 paid users)

### Marketing Budget Recommendation

Since infrastructure costs are so low, invest in growth:
- **Months 1-3**: $100/month (Content marketing, SEO)
- **Months 4-6**: $200/month (Google Ads, targeted campaigns)
- **Months 7-12**: $300/month (Scale successful channels)

### Success Metrics

Track these KPIs:
1. **Conversion rate**: Free → Paid (target: 5%)
2. **Churn rate**: Monthly cancellations (target: <10%)
3. **Average Revenue Per User (ARPU)**: Target $15
4. **Customer Acquisition Cost (CAC)**: Target <$30
5. **Lifetime Value (LTV)**: Target >$180

---

**Next Steps**:
1. Set up Stripe account
2. Implement database schema changes
3. Build MVP of billing system
4. Test with small group
5. Launch to all users