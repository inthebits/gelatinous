# AWS Global Accelerator vs Cloudflare Spectrum
## IP Obfuscation & DDoS Protection Comparison

**Date**: October 18, 2025  
**Purpose**: Compare solutions for hiding origin IP and protecting against DDoS attacks

---

## Quick Comparison

| Feature | AWS Global Accelerator | Cloudflare Spectrum |
|---------|----------------------|-------------------|
| **Base Cost** | $18/month | $20/month |
| **Data Transfer** | $0.015/GB | $1.00/GB |
| **Cost @ 3GB/month** | $18.05 | $23 |
| **Cost @ 10GB/month** | $18.15 | $30 |
| **Telnet Support** | ✅ Native | ✅ Native |
| **HTTP/HTTPS** | ✅ Native | ✅ Native |
| **DDoS Protection** | ✅ AWS Shield Standard | ✅✅ Cloudflare (stronger) |
| **Obfuscation** | ✅ Static Anycast IPs | ✅ Cloudflare Anycast IPs |
| **Global Network** | AWS Edge Locations | Cloudflare Edge (300+) |
| **Setup Complexity** | Medium (AWS-native) | Medium (multi-provider) |
| **SSL Management** | Manual (ACM) | Automatic |

---

## AWS Global Accelerator Details

### What It Does

Provides **two static Anycast IP addresses** that route traffic to your AWS resources through AWS's global network.

```
Player → Anycast IP (Global Accelerator) → AWS Edge Location → Your Lightsail Instance
         [Hides your origin IP]              [DDoS filtering]     [Protected]
```

### Architecture

```
┌────────────────────────────────────────────────────────┐
│         AWS Global Accelerator (2 Static IPs)          │
│                  $18/month base                         │
└─────────────────────┬──────────────────────────────────┘
                      │
          ┌───────────┴────────────┐
          │                        │
          ▼                        ▼
┌──────────────────┐    ┌──────────────────┐
│  Endpoint Group  │    │  Endpoint Group  │
│   us-west-2      │    │   us-west-2      │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│ Evennia Instance │    │Discourse Instance│
│  Port 23, 80     │    │    Port 80       │
└──────────────────┘    └──────────────────┘
```

### DNS Configuration

```
# Point all traffic to Global Accelerator IPs
play.gel.monster    A  <accelerator-ip-1>
gel.monster         A  <accelerator-ip-1>
forum.gel.monster   A  <accelerator-ip-2>  (or same IP with listener)
```

### Listeners Configuration

**Listener 1: Telnet (Port 23)**
```
Protocol: TCP
Port: 23
Endpoint: Evennia Lightsail instance (35.165.102.12:23)
Health check: TCP port 23
```

**Listener 2: HTTP (Port 80)**
```
Protocol: TCP
Port: 80
Endpoint Group:
  - Evennia instance (35.165.102.12:80) - weight 100
  - Discourse instance (<discourse-ip>:80) - weight 100
Health check: HTTP GET / (port 80)
```

**Listener 3: HTTPS (Port 443)**
```
Protocol: TCP
Port: 443
Endpoint Group:
  - Evennia instance (35.165.102.12:443) - weight 100
  - Discourse instance (<discourse-ip>:443) - weight 100
Health check: HTTPS GET / (port 443)
```

### SSL Certificate Setup

**You'll need SSL on the instances themselves:**

```bash
# Install certbot on each instance
sudo apt update
sudo apt install -y certbot

# Get certificates
sudo certbot certonly --standalone -d gel.monster -d play.gel.monster
sudo certbot certonly --standalone -d forum.gel.monster

# Configure Evennia to use certificates
# Configure Discourse to use certificates
```

### Cost Breakdown

**Monthly costs at different traffic levels:**

| Traffic/Month | Accelerator Base | Data Transfer | Total | vs Load Balancers |
|---------------|-----------------|---------------|-------|-------------------|
| 3 GB | $18.00 | $0.05 | **$18.05** | Save $37.95 |
| 10 GB | $18.00 | $0.15 | **$18.15** | Save $37.85 |
| 50 GB | $18.00 | $0.75 | **$18.75** | Save $37.25 |
| 100 GB | $18.00 | $1.50 | **$19.50** | Save $36.50 |

**Plus instances: $20/month (same regardless)**

---

## Cloudflare Spectrum Details

### What It Does

Proxies **any TCP/UDP traffic** through Cloudflare's global network with DDoS protection.

```
Player → Cloudflare Edge → Cloudflare Network → Origin Server (hidden)
         [300+ locations]   [DDoS scrubbing]     [Protected]
```

### Architecture

```
┌────────────────────────────────────────────────────────┐
│              Cloudflare Network                         │
│         Pro Plan: $20/month + $1/GB                    │
├────────────────────────────────────────────────────────┤
│                                                         │
│  Spectrum (TCP Proxy)      Tunnel (HTTP Proxy)        │
│     Port 23 (Telnet)       Port 80/443 (Web)          │
│                                                         │
└─────────────┬──────────────────────┬───────────────────┘
              │                      │
              ▼                      ▼
      ┌──────────────┐      ┌──────────────┐
      │   Evennia    │      │  Discourse   │
      │  Instance    │      │  Instance    │
      └──────────────┘      └──────────────┘
```

### Cost Breakdown

**Monthly costs at different traffic levels:**

| Traffic/Month | Pro Base | Spectrum Data | Total | vs Load Balancers |
|---------------|----------|---------------|-------|-------------------|
| 3 GB | $20 | $3 | **$23** | Save $33 |
| 10 GB | $20 | $10 | **$30** | Save $26 |
| 50 GB | $20 | $50 | **$70** | Cost +$14 |
| 100 GB | $20 | $100 | **$120** | Cost +$64 |

**Plus instances: $20/month (same regardless)**

---

## Head-to-Head Comparison

### Cost Winner: **AWS Global Accelerator**

At your current traffic (3 GB/month):
- **AWS Global Accelerator**: $18/month
- **Cloudflare Spectrum**: $23/month
- **Savings**: $5/month ($60/year)

Even at 100 GB/month (massive growth):
- **AWS Global Accelerator**: $19.50/month
- **Cloudflare Spectrum**: $120/month
- **Savings**: $100.50/month!

### Security Winner: **Cloudflare Spectrum**

**DDoS Protection Capacity:**
- AWS Shield Standard: ~10-20 Gbps typical
- Cloudflare: 100+ Tbps network capacity

**Attack Mitigation:**
- AWS: Automatic for common attacks, Shield Advanced ($3000/mo) for more
- Cloudflare: Enterprise-grade included in Pro plan

**WAF (Web Application Firewall):**
- AWS: Extra cost (AWS WAF)
- Cloudflare: Included in Pro

### Ease of Use Winner: **Cloudflare Spectrum**

**Setup:**
- AWS: Configure accelerator, endpoints, listeners, health checks, SSL on instances
- Cloudflare: Enable Spectrum app, configure tunnel, automatic SSL

**Management:**
- AWS: Multiple AWS services (Global Accelerator, ACM, Lightsail)
- Cloudflare: Single dashboard for everything

**SSL:**
- AWS: Manual certificate management per instance
- Cloudflare: Automatic SSL, auto-renewal

### Performance Winner: **Tie**

Both use Anycast and global edge networks. Differences minimal for your use case.

---

## Recommendations by Scenario

### Scenario 1: You Want Maximum Savings
**Choose: AWS Global Accelerator**
- $18/month vs $56/month current = **Save $38/month**
- Works great at low traffic
- Stays in AWS (simpler billing)

### Scenario 2: You Expect High Growth
**Choose: AWS Global Accelerator**
- Data transfer costs scale much better
- At 100GB/month: $19.50 vs $120 Cloudflare

### Scenario 3: You Value Simplicity
**Choose: Cloudflare Spectrum**
- Single dashboard for everything
- Automatic SSL management
- Easier initial setup
- Better documentation/support

### Scenario 4: You Need Strongest Security
**Choose: Cloudflare Spectrum**
- Better DDoS protection
- WAF included
- More mature security features
- Better for high-profile targets

### Scenario 5: You're Budget-Constrained
**Choose: AWS Global Accelerator**
- $5/month cheaper at low traffic
- Much cheaper if traffic grows
- No surprises in billing

---

## My Recommendation: **AWS Global Accelerator**

### Why?

1. **Cost**: $18/month vs $23+ Cloudflare (saves $60+/year)
2. **Scaling**: Data transfer costs 67x cheaper ($0.015/GB vs $1/GB)
3. **AWS Native**: Already using Lightsail, simpler integration
4. **Sufficient Security**: AWS Shield Standard handles most DDoS attacks
5. **Future-proof**: Even at 10x traffic growth, still cheaper

### When to Choose Cloudflare Instead?

- You're being actively targeted by attackers
- You need WAF features
- You want the easiest possible setup
- $5/month difference doesn't matter to you
- You value the Cloudflare brand/reputation

---

## Implementation Comparison

### AWS Global Accelerator Setup

**Time: ~2 hours**

1. Create Global Accelerator (15 min)
2. Add listeners for ports 23, 80, 443 (15 min)
3. Add endpoint groups (10 min)
4. Update DNS to accelerator IPs (5 min + propagation)
5. Install SSL certificates on instances (30 min)
6. Test all services (30 min)
7. Delete load balancers (5 min)

### Cloudflare Spectrum Setup

**Time: ~2-3 hours**

1. Upgrade to Pro plan (5 min)
2. Enable Spectrum (5 min)
3. Create Spectrum app for port 23 (10 min)
4. Install cloudflared on instances (30 min)
5. Configure tunnel for web traffic (30 min)
6. Update DNS (5 min + propagation)
7. Test all services (30 min)
8. Secure origin with firewall (30 min)
9. Delete load balancers (5 min)

**Similar complexity, slightly favor AWS for AWS-native users.**

---

## Hybrid Option: Best of Both Worlds?

**Not Really Practical:**

You could use AWS Global Accelerator for Telnet and Cloudflare Free for web, but:
- Saves only $3/month vs pure AWS
- More complex (two systems)
- Cloudflare Free doesn't support TCP proxy for Telnet
- Not worth the complexity

---

## Final Decision Matrix

| Priority | Choose AWS Global Accelerator | Choose Cloudflare Spectrum |
|----------|------------------------------|---------------------------|
| **Lowest Cost** | ✅ | ❌ |
| **Scalability** | ✅ | ❌ |
| **AWS Integration** | ✅ | ❌ |
| **Easiest Setup** | ❌ | ✅ |
| **Best DDoS Protection** | ❌ | ✅ |
| **Included WAF** | ❌ | ✅ |
| **Automatic SSL** | ❌ | ✅ |

---

## Bottom Line

**For Gelatinous Monster:**

Given your **low traffic** (3 GB/month), **AWS expertise**, and **budget consciousness**:

### **Use AWS Global Accelerator**

**Total monthly cost:**
- Global Accelerator: $18/month
- Evennia instance: $10/month
- Discourse instance: $10/month
- **Total: $38/month**

**vs Current: $56/month**
**Savings: $18/month ($216/year)**

With the added benefits of:
- ✅ IP obfuscation (origin IP hidden)
- ✅ DDoS protection (AWS Shield Standard)
- ✅ Static Anycast IPs
- ✅ Works with Telnet natively
- ✅ Scales incredibly cheaply

You can always upgrade to Cloudflare Spectrum later if you need stronger DDoS protection or face active attacks.

---

*This comparison assumes 3 GB/month baseline traffic with potential for growth.*
