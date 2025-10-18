# Forum Integration Specification
## Message Board for Gelatinous Monster Community

**Date**: October 18, 2025  
**Status**: Analysis & Specification  
**Objective**: Integrate a modern message board with seamless SSO from Evennia/Django

---

## Executive Summary

Gelatinous Monster needs a community forum for:
- Player discussions and community building
- Game announcements and updates
- Bug reports and feature requests
- Character development and roleplay coordination
- Out-of-character (OOC) communication

**Recommended Solution**: **Discourse** with Django SSO integration

---

## Requirements Analysis

### Functional Requirements

1. **Single Sign-On (SSO)**
   - Users authenticate via Evennia/Django (gel.monster)
   - Automatic account creation on first forum visit
   - Username/email synchronized between systems
   - No separate forum registration process

2. **User Experience**
   - Seamless login from game website
   - Modern, mobile-responsive interface
   - Email notifications for forum activity
   - Rich text editing with Markdown support

3. **Content Organization**
   - Categories for different discussion types
   - Thread tagging and search functionality
   - Pinned announcements
   - Private messaging between users

4. **Moderation & Administration**
   - Admin panel accessible to staff
   - User trust levels and permissions
   - Spam protection and rate limiting
   - Content moderation tools

5. **Integration Features**
   - Link to forum from game website
   - Display recent forum posts on website (optional)
   - In-game notifications for forum activity (future)
   - Character name display with account (future)

### Non-Functional Requirements

1. **Performance**: Fast page loads, scalable to 1000+ users
2. **Security**: Protected from spam, DDoS, SQL injection
3. **Cost**: Minimize hosting costs, leverage existing infrastructure
4. **Maintenance**: Low maintenance overhead, automatic updates
5. **Mobile**: Full mobile support without separate app

---

## Platform Comparison

### Option 1: Discourse (Recommended)

**Pros**:
- ✅ Industry-leading modern forum software
- ✅ Built-in SSO support (DiscourseConnect, formerly SSO)
- ✅ Excellent mobile experience
- ✅ Active development and community
- ✅ Email notifications and digests
- ✅ Markdown support, emoji, reactions
- ✅ Trust levels and gamification
- ✅ Search engine friendly
- ✅ API for future integrations
- ✅ Free and open source

**Cons**:
- ⚠️ Resource intensive (2GB RAM minimum)
- ⚠️ Ruby/Rails stack (different from Django)
- ⚠️ Requires separate Docker container
- ⚠️ Self-hosted complexity OR $100/month hosted

**Technical Stack**:
- Ruby on Rails
- PostgreSQL (separate from Evennia DB)
- Redis (for caching and background jobs)
- Docker (recommended deployment)

**SSO Integration**: DiscourseConnect (official SSO protocol)
- Django acts as SSO provider
- Discourse consumes SSO tokens
- Well-documented, battle-tested

### Option 2: Flarum

**Pros**:
- ✅ Modern, lightweight interface
- ✅ PHP-based (easier hosting)
- ✅ SSO support via extensions
- ✅ Less resource intensive
- ✅ Beautiful mobile UI

**Cons**:
- ⚠️ Smaller community than Discourse
- ⚠️ SSO extension may be less mature
- ⚠️ Fewer features overall
- ⚠️ PHP stack (still separate from Django)

### Option 3: NodeBB

**Pros**:
- ✅ Node.js based
- ✅ Real-time features (websockets)
- ✅ Modern interface
- ✅ SSO plugins available

**Cons**:
- ⚠️ Smaller community than Discourse
- ⚠️ Less documentation
- ⚠️ SSO integration less mature
- ⚠️ Another stack to maintain

### Option 4: Custom Django Forum

**Pros**:
- ✅ Same stack as Evennia
- ✅ Perfect SSO (built-in Django auth)
- ✅ Direct database integration
- ✅ Full control

**Cons**:
- ❌ Significant development time
- ❌ Need to build all features from scratch
- ❌ Maintenance burden
- ❌ Mobile experience requires work
- ❌ Spam protection from scratch
- ❌ Search functionality to build

**Verdict**: Not recommended unless you want a multi-month project

### Option 5: Hosted Solutions (Reddit, Discord, etc.)

**Pros**:
- ✅ Zero maintenance
- ✅ Free
- ✅ Established communities

**Cons**:
- ❌ No SSO with your site
- ❌ Less control
- ❌ External branding
- ❌ Can't customize
- ❌ Risk of platform changes

---

## Recommendation: Discourse with DiscourseConnect SSO

### Why Discourse?

1. **Best-in-class forum software** used by major communities
2. **Official SSO protocol** (DiscourseConnect) designed for this exact use case
3. **Battle-tested** by thousands of communities
4. **Excellent documentation** for Django SSO integration
5. **Professional appearance** that matches gel.monster's quality
6. **Future-proof** with active development and API

### DiscourseConnect SSO Overview

**How It Works**:
```
1. User clicks "Forum" on gel.monster
2. Redirected to forum.gel.monster
3. Discourse checks if user is logged in
4. If not, Discourse redirects to gel.monster/sso/discourse
5. Django verifies user authentication
6. Django generates signed SSO payload
7. User redirected back to Discourse with payload
8. Discourse validates signature
9. Discourse creates/updates user account
10. User is logged into forum
```

**Security**: HMAC-SHA256 signed payloads prevent tampering

---

## Architecture Design

### Hosting Options

#### Option A: Self-Hosted on AWS Lightsail (Recommended)

**Setup**:
- New Lightsail instance: $10/month (2GB RAM, 1 vCPU)
- Domain: forum.gel.monster
- Docker-based Discourse installation
- Separate from Evennia server

**Pros**:
- Full control
- $10/month fixed cost
- Can scale up if needed
- Same AWS account/region as Evennia

**Cons**:
- Requires setup and maintenance
- Separate server to manage

#### Option B: Discourse Hosted

**Setup**:
- Official Discourse hosting
- $100/month for basic plan
- Fully managed

**Pros**:
- Zero maintenance
- Automatic updates
- Expert support

**Cons**:
- $100/month (vs $10 self-hosted)
- Less control

**Recommendation**: Self-hosted for cost efficiency

### Domain Structure

```
Primary Site:    https://gel.monster          (Evennia website)
Game Server:     play.gel.monster:23          (Telnet)
Forum:           https://forum.gel.monster    (Discourse)
SSO Endpoint:    https://gel.monster/sso/discourse
```

### Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Lightsail                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────┐          ┌────────────────────┐     │
│  │  Load Balancer 1   │          │  Load Balancer 2   │     │
│  │  (gel.monster)     │          │ (forum.gel.monster)│     │
│  │  $18/month         │          │  $18/month         │     │
│  └─────────┬──────────┘          └─────────┬──────────┘     │
│            │                               │                 │
│            ▼                               ▼                 │
│  ┌─────────────────────────┐    ┌──────────────────────┐   │
│  │  Evennia Server          │    │  Discourse Server    │   │
│  │  (35.165.102.12)        │    │  (New Instance)      │   │
│  │  $10/month              │    │  $10/month           │   │
│  │                          │    │                       │   │
│  │  - Django Website        │◄──►│  - Ruby on Rails     │   │
│  │  - Evennia Game         │    │  - PostgreSQL        │   │
│  │  - SSO Provider         │    │  - Redis             │   │
│  └─────────────────────────┘    └──────────────────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
             ▲                              ▲
             │         Internet             │
             │                              │
        ┌────┴──────────────────────────────┴─────┐
        │           User Browser                   │
        │  1. Login at gel.monster                │
        │  2. Click "Forum"                       │
        │  3. SSO handshake                       │
        │  4. Access forum.gel.monster            │
        └──────────────────────────────────────────┘

Total Infrastructure Cost: $56/month
Future Optimization: Migrate to Cloudflare Tunnel ($0/month for SSL + routing)
```

---

## DiscourseConnect SSO Implementation

### Django Side (SSO Provider)

#### 1. Create SSO Endpoint

**File**: `web/website/views/discourse_sso.py`

```python
import hmac
import hashlib
import base64
import urllib.parse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_GET

@require_GET
@login_required
def discourse_sso(request):
    """
    Handle DiscourseConnect SSO authentication.
    
    Discourse sends: sso (base64 payload) + sig (HMAC signature)
    Django returns: sso (base64 response) + sig (HMAC signature)
    """
    # Get payload and signature from Discourse
    payload = request.GET.get('sso', '')
    signature = request.GET.get('sig', '')
    
    # Verify the signature
    secret = settings.DISCOURSE_SSO_SECRET.encode('utf-8')
    expected_sig = hmac.new(
        secret,
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    if signature != expected_sig:
        return HttpResponse('Invalid signature', status=403)
    
    # Decode the payload
    decoded = base64.b64decode(payload).decode('utf-8')
    params = urllib.parse.parse_qs(decoded)
    nonce = params['nonce'][0]
    
    # Build response payload
    user = request.user
    response_params = {
        'nonce': nonce,
        'email': user.email,
        'external_id': str(user.id),
        'username': user.username,
        'name': user.username,  # or user.get_full_name() if available
        'require_activation': 'false',  # User already verified in Django
    }
    
    # Optional: Add admin/moderator status
    if user.is_superuser:
        response_params['admin'] = 'true'
    if user.is_staff:
        response_params['moderator'] = 'true'
    
    # Encode response
    response_payload = urllib.parse.urlencode(response_params)
    response_encoded = base64.b64encode(response_payload.encode('utf-8')).decode('utf-8')
    
    # Sign response
    response_sig = hmac.new(
        secret,
        response_encoded.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Redirect back to Discourse
    discourse_url = settings.DISCOURSE_URL
    redirect_url = f"{discourse_url}/session/sso_login?sso={response_encoded}&sig={response_sig}"
    
    return HttpResponseRedirect(redirect_url)
```

#### 2. Add URL Route

**File**: `web/urls.py`

```python
from web.website.views.discourse_sso import discourse_sso

urlpatterns = [
    # ... existing patterns ...
    path('sso/discourse/', discourse_sso, name='discourse_sso'),
]
```

#### 3. Configure Settings

**File**: `server/conf/secret_settings.py` (production)

```python
# Discourse SSO Configuration
DISCOURSE_URL = 'https://forum.gel.monster'
DISCOURSE_SSO_SECRET = 'generate-a-random-secret-here'  # Must match Discourse
```

**File**: `server/conf/settings.py` (defaults)

```python
# Discourse integration (optional, defaults if not in secret_settings)
DISCOURSE_URL = None
DISCOURSE_SSO_SECRET = None
```

### Discourse Side (SSO Consumer)

#### 1. Enable DiscourseConnect

**Admin Panel** → Settings → Login:
- Enable: `enable_discourse_connect`
- Set: `discourse_connect_url = https://gel.monster/sso/discourse`
- Set: `discourse_connect_secret = <same-secret-as-django>`

#### 2. Disable Local Logins (Optional)

- Disable: `enable_local_logins` (users MUST use SSO)
- Disable: `enable_google_oauth2_logins` (if you don't want Google)

#### 3. Configure User Fields

Map Django fields to Discourse:
- `external_id` → Django user.id
- `email` → Django user.email
- `username` → Django user.username
- `name` → Django user display name

---

## User Experience Flow

### First-Time Forum Visit

1. **User is logged into gel.monster**
2. **Clicks "Forum" link** in navigation
3. **Redirected to forum.gel.monster**
4. **Discourse sees no session**, redirects to SSO endpoint
5. **Django verifies authentication** (already logged in)
6. **Django sends user data** to Discourse via signed payload
7. **Discourse creates forum account** (automatic)
8. **User lands on forum**, fully logged in

**Time**: < 3 seconds, seamless

### Returning Visit

1. **User clicks "Forum" link**
2. **Discourse checks session** (still valid)
3. **User lands on forum**, immediately logged in

**Time**: < 1 second

### Logout Behavior

**Option A: Separate Logout** (Recommended)
- Logging out of forum doesn't log out of gel.monster
- Logging out of gel.monster doesn't log out of forum
- Users can stay logged into one or both

**Option B: Synchronized Logout**
- Logging out of either logs out of both
- Requires additional implementation
- More complex, potentially confusing

**Recommendation**: Option A (separate logout) for flexibility

---

## Deployment Plan

### Phase 1: Infrastructure Setup

**1. Create Lightsail Instance**
```bash
# AWS Lightsail Console
Name: discourse-gelatinous
Plan: $10/month (2GB RAM, 1 vCPU, 60GB SSD)
Region: us-west-2 (same as Evennia)
OS: Ubuntu 22.04 LTS
```

**2. Create Lightsail Load Balancer**
```bash
# AWS Lightsail Console
Name: discourse-lb
Region: us-west-2
Port: 443 (HTTPS)
Health check: HTTP on port 80, path: /
Attach instance: discourse-gelatinous
```

**3. Configure SSL Certificate**
```bash
# In load balancer settings
Certificate domain: forum.gel.monster
Validation: DNS (CNAME records will be provided)
Wait for certificate validation to complete
```

**4. Configure DNS**
```
Type: A
Host: forum.gel.monster
Value: <load-balancer-ip>  (NOT instance IP)
TTL: 300

Plus: CNAME records for SSL certificate validation
```

**3. Install Docker**
```bash
ssh ubuntu@forum.gel.monster
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker
sudo systemctl start docker
```

### Phase 2: Discourse Installation

**1. Clone Discourse Docker**
```bash
sudo -s
mkdir /var/discourse
cd /var/discourse
git clone https://github.com/discourse/discourse_docker.git
cd discourse_docker
```

**2. Run Setup Script**
```bash
./discourse-setup
```

**Prompts**:
- Hostname: `forum.gel.monster`
- Email: `admin@gel.monster` (your verified SES email)
- SMTP server: `email-smtp.us-east-1.amazonaws.com`
- SMTP port: `587`
- SMTP username: `<your-ses-smtp-username>`
- SMTP password: `<your-ses-smtp-password>`
- Let's Encrypt email: `admin@gel.monster`

**3. Build and Start**
```bash
./launcher bootstrap app
./launcher start app
```

**Time**: 10-15 minutes

### Phase 3: Django SSO Implementation

**1. Create SSO View** (as shown above)
**2. Add URL Route**
**3. Configure Settings**
**4. Test SSO Flow**

### Phase 4: Discourse Configuration

**1. Create Admin Account**
- Visit `https://forum.gel.monster`
- Register first account (becomes admin)

**2. Enable DiscourseConnect**
- Admin → Settings → Login
- Configure SSO settings
- Test with secondary account

**3. Configure Categories**
```
Suggested Categories:
- 📢 Announcements (staff only posting)
- 💬 General Discussion
- 🎭 Roleplay & Character Development
- 🐛 Bug Reports
- 💡 Feature Requests
- 📚 Game Lore & World
- 🆘 Help & Support
- 🗑️ Off-Topic
```

**4. Set Trust Levels**
- TL0: New users (can read, limited posting)
- TL1: Basic users (full posting rights)
- TL2: Members (can edit wiki posts)
- TL3: Regular (additional privileges)
- TL4: Leaders (near-moderator powers)

### Phase 5: Integration

**1. Add Forum Link to Website**
```html
<!-- In navigation template -->
<a href="https://forum.gel.monster">Forum</a>
```

**2. Styling**
- Match Discourse theme to gel.monster colors
- Use Daring Fireball-inspired dark theme
- Custom CSS via Admin → Customize → Themes

**3. Testing**
- Test SSO flow with multiple accounts
- Test logout behavior
- Test admin/moderator sync
- Test email notifications

---

## Security Considerations

### 1. SSO Secret Management

**Critical**: The `DISCOURSE_SSO_SECRET` must be:
- Strong (32+ random characters)
- Stored in `secret_settings.py` (not in git)
- Identical on both Django and Discourse sides
- Never exposed in logs or error messages

**Generate Secure Secret**:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### 2. HTTPS Enforcement

- Force HTTPS on both domains
- Let's Encrypt certificates (automatic via Discourse Docker)
- HSTS headers enabled

### 3. Rate Limiting

Discourse has built-in rate limiting:
- Account creation
- Post frequency
- Login attempts
- Search queries

### 4. Spam Protection

Discourse includes:
- Akismet spam detection (optional, paid)
- Trust level system
- Flagging and moderation tools
- New user restrictions

### 5. User Data Sync

**Data Synchronized**:
- ✅ Username
- ✅ Email address
- ✅ Admin status
- ✅ Moderator status

**Data NOT Synchronized**:
- ❌ Password (Discourse never sees it)
- ❌ Profile data (managed separately)
- ❌ Preferences (forum-specific)

**Privacy Consideration**: Email addresses are visible to Discourse admins

---

## Cost Analysis

### Self-Hosted Option (Recommended)

**Infrastructure**:
- Lightsail instance: $10/month (2GB RAM)
- Lightsail load balancer: $18/month (dedicated for Discourse)
- Domain (forum.gel.monster): $0 (subdomain)
- SSL certificates: $0 (via load balancer)
- **Total: $28/month**

**Annual Cost**: $336/year

**Note**: Using separate load balancer for clean SSL management. Future migration to Cloudflare Tunnel can eliminate load balancer costs entirely.

### Hosted Discourse Option

**Service**:
- Basic plan: $100/month
- Standard plan: $300/month
- **Total: $100-$300/month**

**Annual Cost**: $1,200-$3,600/year

### Cost Savings

**Self-hosting saves**: $1,080-$3,480/year

**Tradeoff**: ~2 hours/month maintenance vs zero maintenance

**Recommendation**: Self-host given your AWS expertise

---

## Maintenance Requirements

### Regular Tasks

**Weekly**:
- Check for spam posts
- Review flagged content
- Monitor server resources

**Monthly**:
- Update Discourse (`./launcher rebuild app`)
- Review user trust levels
- Check backup integrity

**Quarterly**:
- Review category structure
- Update pinned announcements
- Audit admin/moderator access

**Annual**:
- Review hosting costs
- Evaluate feature usage
- Community survey

### Backup Strategy

**Discourse Built-in Backups**:
- Daily automatic backups
- Stored locally and optionally S3
- One-click restore

**Configuration**:
- Admin → Backups
- Enable automatic daily backups
- Upload to S3 (optional, recommended)

---

## Alternative: Lightweight Options

If Discourse seems too resource-intensive:

### Option: Flarum + SSO

**Resources**: 1GB RAM minimum
**Cost**: $6/month Lightsail instance
**Tradeoff**: Fewer features, less polished

**SSO**: Available via `flarum/auth-sso` extension

### Option: Simple Django Forum

Use `django-machina` or `pybbm`:
- Integrated with Django
- Built-in SSO (Django auth)
- Lightweight

**Cons**:
- Less modern UX
- More development work
- Less feature-rich

---

## Future Enhancements

### Phase 2 Features

1. **In-Game Forum Notifications**
   - Notify players of new posts via in-game message
   - Use Discourse webhooks + Evennia script

2. **Character Association**
   - Display character names with forum posts
   - "Posting as: CharacterName (PlayerName)"

3. **Roleplaying Section**
   - Forum category for IC (in-character) posts
   - Integration with character sheets

4. **Recent Posts Widget**
   - Display recent forum activity on gel.monster homepage
   - Use Discourse API

5. **Unified Search**
   - Search both game wiki and forum from one interface

### API Integration

Discourse has a comprehensive REST API:
```
GET /posts.json                  # Latest posts
GET /t/{topic_id}.json          # Topic details
POST /posts                      # Create post
PUT /t/{topic_id}               # Update topic
```

**Use Cases**:
- Display forum activity on website
- Cross-post announcements
- Automated moderation
- Statistics and analytics

---

## Implementation Timeline

### Week 1: Infrastructure
- [ ] Create Lightsail instance
- [ ] Configure DNS for forum.gel.monster
- [ ] Install Docker and Discourse
- [ ] Configure SSL certificates
- [ ] Test basic Discourse functionality

### Week 2: SSO Development
- [ ] Implement Django SSO endpoint
- [ ] Configure DiscourseConnect in Discourse
- [ ] Test SSO flow with test accounts
- [ ] Verify admin/moderator sync
- [ ] Document SSO process

### Week 3: Configuration
- [ ] Set up forum categories
- [ ] Configure trust levels
- [ ] Customize theme to match gel.monster
- [ ] Configure email notifications
- [ ] Set up automatic backups

### Week 4: Integration & Testing
- [ ] Add forum link to website navigation
- [ ] Test complete user journey
- [ ] Create staff documentation
- [ ] Invite beta testers
- [ ] Monitor performance and adjust

### Week 5: Launch
- [ ] Announce forum to community
- [ ] Create welcome post
- [ ] Monitor initial activity
- [ ] Address any issues
- [ ] Gather feedback

**Total Time**: 4-5 weeks part-time

---

## Testing Checklist

### SSO Testing

- [ ] Login to gel.monster, click forum link → auto-login works
- [ ] Not logged into gel.monster, click forum → redirect to login
- [ ] Create new account on gel.monster → can access forum
- [ ] Change username on gel.monster → syncs to forum
- [ ] Promote user to staff → becomes moderator on forum
- [ ] Promote user to admin → becomes admin on forum
- [ ] Log out of gel.monster → still logged into forum (separate sessions)

### Forum Functionality

- [ ] Create new topic
- [ ] Reply to topic
- [ ] Edit post
- [ ] Upload image
- [ ] Use Markdown formatting
- [ ] Receive email notification
- [ ] Search for posts
- [ ] Flag inappropriate content
- [ ] Private message another user
- [ ] Change theme (light/dark)

### Performance

- [ ] Page load time < 2 seconds
- [ ] Mobile experience smooth
- [ ] Email delivery < 1 minute
- [ ] Search results relevant
- [ ] Handles 10 concurrent users
- [ ] Backup completes successfully

### Security

- [ ] HTTPS enforced
- [ ] SSO signature validation works
- [ ] Invalid signature rejected
- [ ] Rate limiting prevents spam
- [ ] Admin panel requires authentication
- [ ] Backups are encrypted

---

## Documentation Requirements

### For Developers

- SSO implementation guide
- Discourse admin access credentials
- Backup and restore procedures
- Troubleshooting common issues

### For Players

- How to access the forum
- Forum rules and guidelines
- How to report issues
- Privacy policy update (forum data)

### For Moderators

- Moderation guidelines
- Trust level management
- Handling flagged content
- Banning/suspending users

---

## Risks & Mitigation

### Risk 1: Resource Constraints

**Problem**: Discourse requires 2GB RAM, may strain small instance

**Mitigation**:
- Monitor resource usage closely
- Use swap space if needed
- Upgrade to $20/month instance (4GB RAM) if necessary
- Consider Flarum as lightweight alternative

### Risk 2: SSO Implementation Complexity

**Problem**: Custom SSO code may have bugs

**Mitigation**:
- Use official DiscourseConnect documentation
- Test extensively with multiple accounts
- Use existing Django SSO libraries if available
- Have fallback plan (temporary email/password login)

### Risk 3: Community Adoption

**Problem**: Players may not use forum

**Mitigation**:
- Promote forum actively in-game
- Post exclusive content on forum
- Staff participation to seed discussions
- Integrate forum with game announcements

### Risk 4: Moderation Burden

**Problem**: Forum requires active moderation

**Mitigation**:
- Recruit volunteer moderators from community
- Use Discourse's trust level system
- Enable automatic spam detection
- Set clear community guidelines

### Risk 5: Maintenance Overhead

**Problem**: Self-hosted requires regular updates

**Mitigation**:
- Schedule monthly maintenance windows
- Document update procedures
- Set up monitoring/alerts
- Consider hosted option if time-constrained

---

## Success Metrics

### Technical Metrics

- SSO success rate: >99%
- Forum uptime: >99.5%
- Page load time: <2 seconds
- Email delivery rate: >95%

### Community Metrics

- Active users per month: Target 50% of game population
- Posts per day: Target 10+ after first month
- Response time: <24 hours for questions
- User satisfaction: >80% positive feedback

---

## Conclusion

**Recommendation**: Implement Discourse with DiscourseConnect SSO

**Rationale**:
1. **Best-in-class** forum software with excellent UX
2. **Official SSO protocol** designed for this exact use case
3. **Cost-effective** at $10/month self-hosted
4. **Battle-tested** by thousands of communities
5. **Future-proof** with rich API and active development

**Next Steps**:
1. Review and approve this specification
2. Create AWS Lightsail instance for Discourse
3. Implement Django SSO endpoint
4. Configure and test SSO integration
5. Launch forum to community

**Timeline**: 4-5 weeks part-time  
**Cost**: $10/month infrastructure  
**Maintenance**: ~2 hours/month  

---

## Appendix: DiscourseConnect Protocol Details

### Request from Discourse

```http
GET /sso/discourse?sso=<base64_payload>&sig=<hmac_signature>
```

**Payload** (decoded):
```
nonce=cb68251eefb5211e58c00ff1395f0c0b
return_sso_url=https://forum.gel.monster/session/sso_login
```

### Response from Django

```http
HTTP/1.1 302 Found
Location: https://forum.gel.monster/session/sso_login?sso=<base64_response>&sig=<hmac_signature>
```

**Response Payload** (decoded):
```
nonce=cb68251eefb5211e58c00ff1395f0c0b
email=user@example.com
external_id=123
username=playerone
name=Player One
require_activation=false
admin=false
moderator=false
```

### Signature Calculation

```python
signature = hmac.new(
    secret.encode('utf-8'),
    payload.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

**Security**: HMAC-SHA256 ensures payload cannot be tampered with

---

## References

- [Discourse Official Documentation](https://docs.discourse.org/)
- [DiscourseConnect SSO Guide](https://meta.discourse.org/t/discourseconnect-official-single-sign-on-for-discourse-sso/13045)
- [Discourse Docker Installation](https://github.com/discourse/discourse_docker)
- [Django HMAC Documentation](https://docs.python.org/3/library/hmac.html)

---

*This specification provides a comprehensive analysis and implementation plan for integrating Discourse forum with Gelatinous Monster's Evennia/Django platform.*
