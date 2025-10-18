# Cloudflare Spectrum Setup Guide
## TCP Proxy for Evennia MUD Telnet Traffic

**Date**: October 18, 2025  
**Purpose**: Configure Cloudflare Spectrum to proxy Telnet (port 23) traffic with IP obfuscation and DDoS protection

---

## Prerequisites

- Cloudflare account with domain (gel.monster)
- Upgrade to Pro plan ($20/month)
- Evennia running on Lightsail instance
- SSH access to server

---

## Cost Analysis

### Current Setup (Two Load Balancers)
- Evennia Load Balancer: $18/month
- Discourse Load Balancer: $18/month
- Evennia Instance: $10/month
- Discourse Instance: $10/month
- **Total: $56/month**

### With Cloudflare Spectrum + Tunnel
- Cloudflare Pro: $20/month (base)
- Spectrum data transfer: $1/GB (~$10-20/month estimated)
- Evennia Instance: $10/month
- Discourse Instance: $10/month
- **Total: $50-60/month**

**Break-even**: Similar cost with MUCH better security

### Monthly Data Transfer Estimates

| Concurrent Players | Hours/Day | MB/Day/Player | Total GB/Month | Spectrum Cost |
|-------------------|-----------|---------------|----------------|---------------|
| 10                | 4         | 15            | ~10 GB         | $10           |
| 25                | 4         | 15            | ~25 GB         | $25           |
| 50                | 4         | 15            | ~50 GB         | $50           |
| 100               | 4         | 15            | ~100 GB        | $100          |

---

## Phase 1: Cloudflare Account Setup

### 1. Upgrade to Pro Plan

```
1. Log into Cloudflare dashboard
2. Select gel.monster domain
3. Go to "Plans" section
4. Click "Upgrade Plan"
5. Select "Pro" ($20/month)
6. Confirm payment method
```

### 2. Enable Spectrum

```
1. In Cloudflare dashboard for gel.monster
2. Navigate to "Spectrum" in left sidebar
3. Click "Enable Spectrum"
4. Accept terms and pricing
```

---

## Phase 2: Configure Spectrum Application

### 1. Create Spectrum Application

```
Cloudflare Dashboard → Spectrum → Create Application

Configuration:
┌─────────────────────────────────────────────────┐
│ Application Name: Evennia MUD Telnet            │
│                                                  │
│ Domain: play.gel.monster                        │
│                                                  │
│ Edge Port Configuration:                        │
│   Protocol: TCP                                 │
│   Port: 23                                      │
│                                                  │
│ Origin Configuration:                           │
│   Origin Server: 35.165.102.12                  │
│   Origin Port: 23                               │
│   Protocol: TCP                                 │
│                                                  │
│ Proxy Status: ☑ Proxied (orange cloud)         │
│                                                  │
│ IP Firewall:                                    │
│   ☑ Enable Cloudflare IP Firewall              │
│                                                  │
│ TLS:                                            │
│   ☐ Don't use TLS (raw Telnet, plaintext)      │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 2. DNS Configuration

The Spectrum application will automatically update DNS:

```
Before:
play.gel.monster  A  35.165.102.12  (gray cloud - DNS only)

After:
play.gel.monster  A  <cloudflare-ip>  (orange cloud - proxied)
```

**Important**: The DNS record will show a Cloudflare Anycast IP, not your origin IP.

---

## Phase 3: Cloudflare Tunnel for Web Traffic

### 1. Install cloudflared on Evennia Instance

```bash
# SSH to Evennia server
ssh -i ~/Documents/LightsailDefaultKey-us-west-2.pem ubuntu@play.gel.monster

# Download cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared

# Make executable and move to system path
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Verify installation
cloudflared --version
```

### 2. Authenticate with Cloudflare

```bash
# Login to Cloudflare (opens browser)
cloudflared tunnel login

# This will download a cert.pem file to ~/.cloudflared/
```

### 3. Create Tunnel

```bash
# Create named tunnel
cloudflared tunnel create gelatinous-tunnel

# Note the Tunnel ID from output
# Creates credentials file: ~/.cloudflared/<TUNNEL_ID>.json
```

### 4. Configure Tunnel Routing

```bash
# Create tunnel configuration
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: <TUNNEL_ID>
credentials-file: /home/ubuntu/.cloudflared/<TUNNEL_ID>.json

ingress:
  # Main website
  - hostname: gel.monster
    service: http://localhost:80
  
  # WWW redirect
  - hostname: www.gel.monster
    service: http://localhost:80
  
  # Discourse forum (different instance)
  - hostname: forum.gel.monster
    service: http://<DISCOURSE_INSTANCE_IP>:80
  
  # Catch-all (required)
  - service: http_status:404
EOF
```

### 5. Configure DNS for Tunnel

```bash
# Route DNS through tunnel
cloudflared tunnel route dns gelatinous-tunnel gel.monster
cloudflared tunnel route dns gelatinous-tunnel www.gel.monster
cloudflared tunnel route dns gelatinous-tunnel forum.gel.monster
```

This automatically creates CNAME records:
```
gel.monster          CNAME  <TUNNEL_ID>.cfargotunnel.com  (orange cloud)
www.gel.monster      CNAME  <TUNNEL_ID>.cfargotunnel.com  (orange cloud)
forum.gel.monster    CNAME  <TUNNEL_ID>.cfargotunnel.com  (orange cloud)
```

### 6. Run Tunnel

```bash
# Test tunnel
cloudflared tunnel run gelatinous-tunnel

# If working, install as system service
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Check status
sudo systemctl status cloudflared
```

---

## Phase 4: Origin Server Security

### 1. Configure Firewall (Evennia Instance)

With Cloudflare proxying all traffic, lock down your origin server:

```bash
# SSH to Evennia instance
ssh -i ~/Documents/LightsailDefaultKey-us-west-2.pem ubuntu@play.gel.monster

# Install UFW if not present
sudo apt update
sudo apt install -y ufw

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (CRITICAL - don't lock yourself out!)
sudo ufw allow 22/tcp comment 'SSH'

# Allow Cloudflare IPs ONLY for Telnet (port 23)
# Get latest Cloudflare IP ranges from:
# https://www.cloudflare.com/ips-v4

# Cloudflare IPv4 ranges (as of 2025)
for ip in \
  173.245.48.0/20 \
  103.21.244.0/22 \
  103.22.200.0/22 \
  103.31.4.0/22 \
  141.101.64.0/18 \
  108.162.192.0/18 \
  190.93.240.0/20 \
  188.114.96.0/20 \
  197.234.240.0/22 \
  198.41.128.0/17 \
  162.158.0.0/15 \
  104.16.0.0/13 \
  104.24.0.0/14 \
  172.64.0.0/13 \
  131.0.72.0/22
do
  sudo ufw allow from $ip to any port 23 proto tcp comment 'Cloudflare Spectrum'
done

# Allow Cloudflare Tunnel (cloudflared connects outbound, no inbound needed)
# But allow port 80 from localhost for tunnel
sudo ufw allow from 127.0.0.1 to any port 80 proto tcp comment 'Local Tunnel'

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status numbered
```

### 2. Automated Cloudflare IP Updates

Cloudflare occasionally updates their IP ranges. Create a script to update UFW:

```bash
# Create update script
sudo nano /usr/local/bin/update-cloudflare-ips.sh
```

```bash
#!/bin/bash
# Update UFW with latest Cloudflare IP ranges

# Fetch latest IPs
CLOUDFLARE_IPS=$(curl -s https://www.cloudflare.com/ips-v4)

# Remove old Cloudflare rules (comment contains 'Cloudflare Spectrum')
sudo ufw status numbered | grep 'Cloudflare Spectrum' | awk -F'[][]' '{print $2}' | sort -rn | while read line; do
  sudo ufw --force delete $line
done

# Add new rules
for ip in $CLOUDFLARE_IPS; do
  sudo ufw allow from $ip to any port 23 proto tcp comment 'Cloudflare Spectrum'
done

# Reload UFW
sudo ufw reload

echo "Cloudflare IP ranges updated"
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/update-cloudflare-ips.sh

# Add to monthly cron
echo "0 3 1 * * /usr/local/bin/update-cloudflare-ips.sh" | sudo crontab -
```

---

## Phase 5: Remove Load Balancers

### 1. Verify Everything Works

**Test Checklist:**
- [ ] Telnet connection: `telnet play.gel.monster 23`
- [ ] Web client: https://gel.monster
- [ ] Forum access: https://forum.gel.monster
- [ ] Check your real IP is hidden (use whatismyip.com from server)
- [ ] Cloudflare analytics showing traffic

### 2. Delete Lightsail Load Balancers

```
AWS Lightsail Console:

1. Networking → Load Balancers
2. Select Evennia load balancer
3. Actions → Delete
4. Confirm deletion

5. Select Discourse load balancer
6. Actions → Delete
7. Confirm deletion

Billing Impact: -$36/month
```

---

## Phase 6: Monitor and Optimize

### 1. Cloudflare Analytics

```
Cloudflare Dashboard → Analytics → Traffic

Monitor:
- Total requests (HTTP + Spectrum)
- Data transfer (Spectrum billing)
- Threats blocked (DDoS attempts)
- Geographic distribution
```

### 2. Set Up Billing Alerts

```
Cloudflare Dashboard → Billing → Notifications

Configure alerts:
- Spectrum data transfer > 50GB
- Spectrum data transfer > 100GB
- Unusual traffic spike detected
```

### 3. Rate Limiting (Optional)

Protect against connection floods:

```
Cloudflare Dashboard → Security → Rate Limiting

Create rule:
- Name: Telnet Connection Limit
- URL: play.gel.monster
- Requests: 10 connections per 10 seconds per IP
- Action: Block for 1 hour
- Description: Prevent Telnet connection flooding
```

---

## Troubleshooting

### Telnet Connection Fails

**Check 1: Spectrum Application Status**
```
Cloudflare Dashboard → Spectrum
Verify: Status = "Healthy"
```

**Check 2: DNS Propagation**
```bash
dig play.gel.monster +short
# Should show Cloudflare IP, not your origin
```

**Check 3: Origin Firewall**
```bash
# Temporarily allow all to test
sudo ufw allow 23/tcp
# Try connection
# Re-enable restricted access after test
```

**Check 4: Cloudflare Logs**
```
Cloudflare Dashboard → Analytics → Logs
Filter: Application = "Evennia MUD Telnet"
```

### Web Traffic Issues

**Check 1: Tunnel Status**
```bash
sudo systemctl status cloudflared
# Should be "active (running)"
```

**Check 2: Tunnel Logs**
```bash
sudo journalctl -u cloudflared -f
```

**Check 3: Test Local Services**
```bash
# From Evennia server
curl http://localhost:80
# Should return Evennia web page
```

### High Data Transfer Costs

**Identify Cause:**
```
Cloudflare Dashboard → Analytics → Traffic

Check:
- Unusual traffic patterns
- Bot traffic (not filtered)
- Large file transfers
- DDoS attempts getting through
```

**Solutions:**
- Enable bot fight mode
- Add rate limiting
- Cache static assets
- Compress responses

---

## Rollback Plan

If you need to revert to load balancers:

### 1. Recreate Load Balancers

```
AWS Lightsail Console → Networking → Create Load Balancer

Configuration:
- Name: evennia-lb (or discourse-lb)
- Region: us-west-2
- Attach instances
- Configure health checks
- Create SSL certificate
```

### 2. Update DNS

```
Cloudflare Dashboard → DNS

Change records:
play.gel.monster   A      <load-balancer-ip>  (gray cloud)
gel.monster        A      <load-balancer-ip>  (gray cloud)
forum.gel.monster  A      <load-balancer-ip>  (gray cloud)
```

### 3. Disable Cloudflare Services

```
# Stop tunnel
sudo systemctl stop cloudflared
sudo systemctl disable cloudflared

# Disable Spectrum
Cloudflare Dashboard → Spectrum → Delete Application

# Downgrade to Free plan (optional)
Cloudflare Dashboard → Plans → Change Plan
```

---

## Benefits Summary

### Security
✅ Origin IP hidden from public  
✅ DDoS protection on all ports  
✅ TCP SYN flood protection  
✅ Cloudflare's WAF for web traffic  
✅ Rate limiting available  

### Performance
✅ Global Anycast network (low latency)  
✅ Optimized routing to origin  
✅ CDN for static assets  
✅ HTTP/2 and HTTP/3 support  

### Operations
✅ No load balancers to manage  
✅ Unified analytics dashboard  
✅ Automatic SSL certificates  
✅ Simple DNS management  
✅ Single billing portal  

### Cost
✅ Similar to two load balancers (~$50-60/month)  
✅ Scales with usage (pay for what you use)  
✅ Better value at higher traffic  
✅ No bandwidth caps or overage fees  

---

## Next Steps

1. **Review cost estimates** - Confirm $50-60/month fits budget
2. **Upgrade Cloudflare** - Enable Pro plan ($20/month)
3. **Configure Spectrum** - Set up Telnet proxy
4. **Deploy Tunnel** - Route web traffic through Cloudflare
5. **Test thoroughly** - Verify all services work
6. **Delete load balancers** - Save $36/month
7. **Monitor usage** - Watch Spectrum data transfer costs

---

## Additional Resources

- **Cloudflare Spectrum Docs**: https://developers.cloudflare.com/spectrum/
- **Cloudflare Tunnel Docs**: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- **Cloudflare IP Ranges**: https://www.cloudflare.com/ips-v4
- **Pricing Calculator**: https://www.cloudflare.com/plans/pro/

---

*This guide assumes Cloudflare Pro plan and provides complete migration path from Lightsail load balancers to Cloudflare Spectrum + Tunnel.*
