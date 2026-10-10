"""Generate sample_tickets.csv and kb_articles.csv for the hackathon demo."""
import csv, os

TICKETS = [
    ("T-001","Payment failed after checkout, money deducted but order not placed","payment","high","negative"),
    ("T-002","I was charged twice for the same order last week","payment","high","negative"),
    ("T-003","My credit card was declined even though it has sufficient balance","payment","medium","negative"),
    ("T-004","Refund not received after 10 days of cancellation","refund","high","negative"),
    ("T-005","I requested a refund 2 weeks ago but still no credit in my account","refund","high","negative"),
    ("T-006","Partial refund received, missing ₹500 from the total","refund","medium","negative"),
    ("T-007","Unable to login, password reset email not arriving","login","high","negative"),
    ("T-008","Account locked after 3 failed login attempts","login","high","negative"),
    ("T-009","Two-factor authentication code not working","login","medium","negative"),
    ("T-010","Cannot reset password, reset link expired immediately","login","medium","negative"),
    ("T-011","Order delayed by 2 weeks, no tracking update","delivery","high","negative"),
    ("T-012","Package shows delivered but I never received it","delivery","high","negative"),
    ("T-013","Wrong item delivered, need exchange or refund","delivery","medium","negative"),
    ("T-014","Delivery agent did not attempt delivery, marked as failed","delivery","medium","negative"),
    ("T-015","API returning 500 errors on all endpoints since morning","technical","critical","negative"),
    ("T-016","Webhook integration stopped working after last update","technical","high","negative"),
    ("T-017","App crashes on iOS 17 when opening settings","technical","high","negative"),
    ("T-018","Dashboard not loading, stuck on spinner","technical","medium","negative"),
    ("T-019","Payment gateway timeout during peak hours","payment","critical","negative"),
    ("T-020","UPI payment failed but amount deducted from bank","payment","high","negative"),
    ("T-021","Subscription auto-renewal charged without notification","payment","medium","negative"),
    ("T-022","Invoice not generated after successful payment","payment","low","neutral"),
    ("T-023","Refund initiated but not reflecting in bank after 7 days","refund","high","negative"),
    ("T-024","Cashback not credited after eligible purchase","refund","medium","neutral"),
    ("T-025","Order cancelled but refund not initiated","refund","high","negative"),
    ("T-026","Social login with Google not working","login","medium","negative"),
    ("T-027","Session expires too quickly, logged out every 5 minutes","login","low","negative"),
    ("T-028","Profile picture not updating after upload","login","low","neutral"),
    ("T-029","Email verification link not working","login","medium","negative"),
    ("T-030","Shipment stuck at customs for 3 weeks","delivery","high","negative"),
    ("T-031","Delivery address not updated despite multiple requests","delivery","medium","negative"),
    ("T-032","Express delivery not delivered on promised date","delivery","high","negative"),
    ("T-033","Tracking number shows invalid on courier website","delivery","medium","negative"),
    ("T-034","Database connection timeout in production environment","technical","critical","negative"),
    ("T-035","SSL certificate expired causing HTTPS errors","technical","critical","negative"),
    ("T-036","Memory leak in background service causing crashes","technical","high","negative"),
    ("T-037","Search functionality returning incorrect results","technical","medium","negative"),
    ("T-038","Push notifications not being received on Android","technical","medium","negative"),
    ("T-039","Payment method not saved after adding card","payment","medium","negative"),
    ("T-040","Discount coupon not applying at checkout","payment","medium","neutral"),
    ("T-041","EMI option not available for eligible products","payment","low","neutral"),
    ("T-042","Refund processed to wrong account","refund","high","negative"),
    ("T-043","Return pickup not scheduled after refund approval","refund","medium","negative"),
    ("T-044","Account suspended without any prior notice","login","high","negative"),
    ("T-045","Unable to change registered email address","login","medium","neutral"),
    ("T-046","Bulk order delivery split without notification","delivery","medium","neutral"),
    ("T-047","Fragile item delivered damaged","delivery","high","negative"),
    ("T-048","API rate limit too restrictive for enterprise plan","technical","medium","neutral"),
    ("T-049","Export to CSV feature not working in dashboard","technical","low","neutral"),
    ("T-050","Mobile app not syncing with web dashboard","technical","medium","negative"),
    ("T-051","Payment declined for international card","payment","medium","negative"),
    ("T-052","Subscription plan downgrade not reflected","payment","medium","neutral"),
    ("T-053","Refund amount incorrect after partial return","refund","medium","negative"),
    ("T-054","Login works on web but not on mobile app","login","medium","negative"),
    ("T-055","Order tracking page shows blank","delivery","low","neutral"),
]

KB_ARTICLES = [
    ("KB-001","Payment Failed: Complete Troubleshooting Guide","If your payment failed, first check if the amount was deducted from your account. If deducted, wait 24 hours for automatic reversal. If not reversed, contact your bank with transaction ID. Common causes: insufficient funds, card expired, bank server timeout, incorrect CVV. Steps: 1) Verify card details 2) Check bank balance 3) Try different payment method 4) Contact bank if amount deducted 5) Raise support ticket with transaction ID.","payment"),
    ("KB-002","How to Request and Track a Refund","To request a refund: Go to Orders > Select Order > Request Refund. Refund timeline: UPI/Wallet 1-3 days, Debit Card 5-7 days, Credit Card 7-10 days, Net Banking 3-5 days. If refund not received after timeline, check with your bank using the refund reference number provided. Escalate to support if bank confirms no credit after 15 days.","refund"),
    ("KB-003","Account Login Issues and Recovery","If you cannot login: 1) Check caps lock 2) Use forgot password 3) Check spam folder for reset email 4) Clear browser cache 5) Try incognito mode. If account locked: wait 30 minutes or contact support. For 2FA issues: use backup codes or contact support to disable 2FA temporarily. Account recovery requires email verification and identity proof.","login"),
    ("KB-004","Order Delivery Tracking and Issues","Track your order at Orders > Track. If delivery delayed: check tracking for updates, contact delivery partner with tracking ID. If marked delivered but not received: file complaint within 48 hours with photo evidence. Wrong item delivered: initiate return within 7 days. Damaged item: report within 24 hours with unboxing video.","delivery"),
    ("KB-005","API Integration Troubleshooting","Common API errors: 500 Internal Server Error - check server status page, 429 Rate Limit - implement exponential backoff, 401 Unauthorized - refresh API token, 404 Not Found - verify endpoint URL. For webhook failures: check endpoint accessibility, verify SSL certificate, review payload format. API documentation available at docs.platform.com.","technical"),
    ("KB-006","Duplicate Payment Resolution","If charged twice: 1) Check bank statement for two separate transactions 2) Note both transaction IDs 3) Contact support with both IDs 4) Refund for duplicate will be processed within 3-5 business days. Prevention: do not click pay button multiple times, wait for confirmation page before closing browser.","payment"),
    ("KB-007","Password Reset Complete Guide","To reset password: 1) Click Forgot Password on login page 2) Enter registered email 3) Check inbox and spam folder 4) Click reset link within 15 minutes 5) Create new password with 8+ characters, uppercase, number, special character. If reset email not received: check spam, verify email address, try after 5 minutes, contact support if still not received.","login"),
    ("KB-008","Delivery Partner Contact and Escalation","Contact delivery partner directly using tracking ID on their website. For Delhivery: 1800-XXX-XXXX, For BlueDart: 1860-XXX-XXXX, For FedEx: 1800-XXX-XXXX. If delivery partner unresponsive, escalate to platform support with tracking ID and delivery partner name. Compensation policy: delay beyond 7 days qualifies for delivery fee refund.","delivery"),
    ("KB-009","Technical Error Codes Reference","Error 500: Server error - retry after 5 minutes. Error 503: Service unavailable - check status page. Error 429: Rate limited - reduce request frequency. Error 401: Authentication failed - re-login or refresh token. Error 403: Forbidden - check permissions. Error 404: Not found - verify URL. For persistent errors, collect error logs and contact technical support.","technical"),
    ("KB-010","Refund Status and Timeline Guide","Refund statuses: Initiated - refund request accepted, Processing - bank processing, Completed - credited to account. Check refund status at Orders > Refunds. If status shows Completed but not received: contact bank with refund reference number. Refund to original payment method only. Cash refunds not available for online payments.","refund"),
    ("KB-011","Two-Factor Authentication Setup and Issues","Enable 2FA: Account Settings > Security > Enable 2FA. Supported methods: SMS OTP, Authenticator App, Email OTP. If 2FA not working: check phone signal for SMS, sync time on authenticator app, use backup codes. Lost access to 2FA: contact support with account verification documents. Disable 2FA: requires identity verification.","login"),
    ("KB-012","International Delivery and Customs","International orders may be subject to customs duties. Customs clearance: 3-15 business days. If stuck at customs: check customs portal with tracking number, pay applicable duties. Customs duties are buyer's responsibility. Prohibited items list available on website. For customs queries, contact local customs office with commercial invoice.","delivery"),
    ("KB-013","Payment Gateway Integration Guide","Supported payment methods: Credit/Debit Cards (Visa, Mastercard, Amex), UPI (GPay, PhonePe, Paytm), Net Banking (50+ banks), Wallets (Paytm, Amazon Pay), EMI (6/12/24 months). For integration issues: verify API keys, check webhook configuration, test in sandbox environment first. PCI DSS compliance required for card storage.","payment"),
    ("KB-014","App Crash and Performance Issues","If app crashes: 1) Update to latest version 2) Clear app cache 3) Restart device 4) Reinstall app. For performance issues: check internet connection, close background apps, free up storage space. iOS specific: update iOS to latest version. Android specific: clear app data if cache clear doesn't help. Report crashes with device model and OS version.","technical"),
    ("KB-015","Subscription Management and Billing","Manage subscription: Account > Subscription. Cancel subscription: effective from next billing cycle. Downgrade plan: effective immediately with prorated refund. Upgrade plan: effective immediately, charged prorated amount. Auto-renewal: disabled 24 hours before renewal date. Billing history available in Account > Billing.","payment"),
    ("KB-016","Return and Exchange Policy","Return window: 7 days for most products, 30 days for electronics. Conditions: unused, original packaging, all accessories included. Initiate return: Orders > Return > Select reason. Exchange: available for wrong/defective items. Return pickup: scheduled within 2-3 business days. Refund after return inspection: 5-7 business days.","refund"),
    ("KB-017","Account Security and Suspicious Activity","If you notice suspicious activity: 1) Change password immediately 2) Enable 2FA 3) Review recent login history 4) Contact support. Signs of compromise: unrecognized logins, changed email/phone, unauthorized orders. Account recovery: requires email verification and government ID. Security tips: use unique password, enable 2FA, don't share credentials.","login"),
    ("KB-018","Bulk Order and Enterprise Delivery","For bulk orders (50+ items): contact enterprise team for dedicated delivery. Bulk delivery timeline: 5-10 business days. Tracking: single tracking ID for entire shipment. Partial delivery: possible for large orders, remaining items delivered within 2 days. Enterprise SLA: 99% on-time delivery guarantee with compensation for delays.","delivery"),
    ("KB-019","Webhook Configuration and Debugging","Configure webhooks: Settings > Integrations > Webhooks. Supported events: payment.success, payment.failed, order.created, order.shipped, refund.processed. Webhook payload format: JSON with event type, timestamp, and data object. Debugging: check webhook logs in dashboard, verify endpoint returns 200 status, implement retry logic for failed deliveries.","technical"),
    ("KB-020","EMI and Financing Options","EMI available on orders above ₹3000. Supported banks: HDFC, ICICI, SBI, Axis, Kotak. EMI tenures: 3, 6, 9, 12, 18, 24 months. No-cost EMI: available on select products. Processing fee: 0-2% depending on bank. EMI eligibility: based on credit card limit. Apply at checkout: select EMI option and choose tenure.","payment"),
    ("KB-021","Data Export and Reporting Issues","Export data: Reports > Export > Select format (CSV/Excel/PDF). If export fails: check file size limit (max 50MB), try smaller date range, use API for large exports. Scheduled reports: set up at Reports > Schedule. Report not received: check spam folder, verify email address. API export: use /api/reports endpoint with date range parameters.","technical"),
    ("KB-022","Partial Refund Processing","Partial refunds issued for: partial returns, price adjustments, promotional corrections. Partial refund timeline: same as full refund. Check partial refund amount at Orders > Refund Details. If partial refund amount incorrect: contact support with order ID and expected refund amount. Partial refunds cannot be converted to full refunds without return.","refund"),
    ("KB-023","Mobile App Login and Sync Issues","If mobile app login fails: 1) Check internet connection 2) Update app to latest version 3) Clear app cache 4) Try logging out and back in. Sync issues: pull down to refresh, check last sync time in settings. Data not syncing: ensure background app refresh enabled, check notification permissions. Cross-device sync: may take up to 5 minutes.","login"),
    ("KB-024","Express and Priority Delivery","Express delivery: next day delivery for orders placed before 2 PM. Priority delivery: 2-hour delivery in select cities. Express delivery not available: remote areas, heavy items, hazardous materials. If express delivery missed: automatic refund of delivery charges, compensation voucher for delay. Track express orders with priority tracking link.","delivery"),
    ("KB-025","Database and Infrastructure Troubleshooting","For database connection issues: check connection string, verify credentials, ensure database server is running. Connection pool exhaustion: increase pool size, implement connection timeout. Slow queries: add indexes, optimize query, use caching. For infrastructure issues: check cloud provider status page, review resource utilization, scale up if needed. Contact DevOps team for production incidents.","technical"),
]

os.makedirs("data", exist_ok=True)

with open("data/sample_tickets.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ticket_id","ticket_text","category","urgency","sentiment"])
    w.writerows(TICKETS)

with open("data/kb_articles.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["kb_id","title","content","category"])
    w.writerows(KB_ARTICLES)

print(f"Generated data/sample_tickets.csv ({len(TICKETS)} tickets)")
print(f"Generated data/kb_articles.csv ({len(KB_ARTICLES)} articles)")
