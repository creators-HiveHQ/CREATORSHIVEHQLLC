"""
Email Service for Creators Hive HQ
Handles email notifications for proposal status changes using SendGrid.
Part of the Zero-Human Operational Model.
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Personalization
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """Exception raised when email delivery fails"""
    pass


class EmailService:
    """
    SendGrid-based email service for Creators Hive HQ.
    Handles all proposal notification emails.
    """
    
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.sender_email = os.environ.get('SENDER_EMAIL', 'notifications@hivehq.com')
        self.sender_name = os.environ.get('SENDER_NAME', 'Creators Hive HQ')
        self._client = None
        
    @property
    def client(self) -> Optional[SendGridAPIClient]:
        """Lazy initialization of SendGrid client"""
        if self._client is None and self.api_key:
            self._client = SendGridAPIClient(self.api_key)
        return self._client
    
    def is_configured(self) -> bool:
        """Check if email service is properly configured"""
        return bool(self.api_key)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML email body
            plain_content: Optional plain text fallback
            
        Returns:
            True if email was accepted for delivery, False otherwise
        """
        if not self.is_configured():
            logger.warning("Email service not configured - SENDGRID_API_KEY missing")
            return False
        
        try:
            message = Mail(
                from_email=Email(self.sender_email, self.sender_name),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )
            
            if plain_content:
                message.add_content(Content("text/plain", plain_content))
            
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
            else:
                logger.error(f"Email send failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise EmailDeliveryError(f"Failed to send email: {str(e)}")
    
    # ============== PROPOSAL STATUS EMAIL TEMPLATES ==============
    
    def _get_base_template(self, content: str) -> str:
        """Wrap content in base email template"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Creators Hive HQ</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f4f4f5;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 32px 40px; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700;">🐝 Creators Hive HQ</h1>
                            <p style="margin: 8px 0 0 0; color: rgba(255, 255, 255, 0.85); font-size: 14px;">Your Creative Partner</p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            {content}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 40px; background-color: #f9fafb; border-radius: 0 0 12px 12px; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #6b7280; font-size: 12px; text-align: center;">
                                © {datetime.now().year} Creators Hive HQ. All rights reserved.<br>
                                <span style="color: #9ca3af;">Powered by ARRIS Pattern Engine</span>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    async def send_proposal_submitted_notification(
        self,
        creator_email: str,
        creator_name: str,
        proposal_title: str,
        proposal_id: str
    ) -> bool:
        """Send notification when a proposal is submitted for review"""
        content = f"""
<h2 style="margin: 0 0 16px 0; color: #111827; font-size: 20px;">Proposal Submitted! 🚀</h2>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Hi {creator_name},
</p>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Your proposal has been successfully submitted for review:
</p>
<div style="background-color: #f3f4f6; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
    <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Proposal</p>
    <p style="margin: 0; color: #111827; font-size: 18px; font-weight: 600;">{proposal_title}</p>
    <p style="margin: 8px 0 0 0; color: #6b7280; font-size: 14px;">ID: {proposal_id}</p>
</div>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Our team and ARRIS AI are now reviewing your proposal. You'll receive another notification once a decision has been made.
</p>
<div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px;">
    <p style="margin: 0; color: #1e40af; font-size: 14px;">
        <strong>💡 Tip:</strong> You can track your proposal status in your Creator Dashboard.
    </p>
</div>
"""
        return await self.send_email(
            to_email=creator_email,
            subject=f"✅ Proposal Submitted: {proposal_title}",
            html_content=self._get_base_template(content)
        )
    
    async def send_proposal_approved_notification(
        self,
        creator_email: str,
        creator_name: str,
        proposal_title: str,
        proposal_id: str,
        project_id: str,
        review_notes: Optional[str] = None
    ) -> bool:
        """Send notification when a proposal is approved"""
        notes_section = ""
        if review_notes:
            notes_section = f"""
<div style="background-color: #f9fafb; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
    <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px; font-weight: 600;">Reviewer Notes:</p>
    <p style="margin: 0; color: #4b5563; font-size: 14px; line-height: 1.6;">{review_notes}</p>
</div>
"""
        
        content = f"""
<h2 style="margin: 0 0 16px 0; color: #059669; font-size: 20px;">🎉 Congratulations! Your Proposal is Approved!</h2>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Hi {creator_name},
</p>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Great news! Your proposal has been approved and a new project has been created.
</p>
<div style="background-color: #ecfdf5; border-radius: 8px; padding: 20px; margin-bottom: 24px; border: 1px solid #a7f3d0;">
    <p style="margin: 0 0 8px 0; color: #065f46; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Approved Proposal</p>
    <p style="margin: 0; color: #065f46; font-size: 18px; font-weight: 600;">{proposal_title}</p>
    <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #a7f3d0;">
        <p style="margin: 0 0 4px 0; color: #047857; font-size: 14px;"><strong>Project ID:</strong> {project_id}</p>
        <p style="margin: 0; color: #047857; font-size: 14px;"><strong>Status:</strong> In Progress</p>
    </div>
</div>
{notes_section}
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Your project is now active and ready for work. Log in to your dashboard to view project details and track progress.
</p>
<a href="#" style="display: inline-block; background-color: #6366f1; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; font-size: 14px;">View Your Project →</a>
"""
        return await self.send_email(
            to_email=creator_email,
            subject=f"🎉 Approved! {proposal_title}",
            html_content=self._get_base_template(content)
        )
    
    async def send_proposal_rejected_notification(
        self,
        creator_email: str,
        creator_name: str,
        proposal_title: str,
        proposal_id: str,
        rejection_reason: Optional[str] = None
    ) -> bool:
        """Send notification when a proposal is rejected"""
        reason_section = ""
        if rejection_reason:
            reason_section = f"""
<div style="background-color: #fef2f2; border-radius: 8px; padding: 16px; margin-bottom: 24px; border: 1px solid #fecaca;">
    <p style="margin: 0 0 8px 0; color: #991b1b; font-size: 14px; font-weight: 600;">Feedback from Reviewer:</p>
    <p style="margin: 0; color: #7f1d1d; font-size: 14px; line-height: 1.6;">{rejection_reason}</p>
</div>
"""
        
        content = f"""
<h2 style="margin: 0 0 16px 0; color: #dc2626; font-size: 20px;">Proposal Update</h2>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Hi {creator_name},
</p>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    We've reviewed your proposal and unfortunately, it wasn't approved at this time.
</p>
<div style="background-color: #f3f4f6; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
    <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Proposal</p>
    <p style="margin: 0; color: #111827; font-size: 18px; font-weight: 600;">{proposal_title}</p>
    <p style="margin: 8px 0 0 0; color: #6b7280; font-size: 14px;">ID: {proposal_id}</p>
</div>
{reason_section}
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Don't be discouraged! Many successful projects go through multiple iterations. We encourage you to:
</p>
<ul style="margin: 0 0 24px 0; padding-left: 24px; color: #4b5563; font-size: 15px; line-height: 1.8;">
    <li>Review the feedback provided above</li>
    <li>Refine your proposal based on the suggestions</li>
    <li>Submit a revised version when ready</li>
</ul>
<div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px;">
    <p style="margin: 0; color: #1e40af; font-size: 14px;">
        <strong>Need help?</strong> Our ARRIS AI can provide insights on how to strengthen your next proposal.
    </p>
</div>
"""
        return await self.send_email(
            to_email=creator_email,
            subject=f"Proposal Update: {proposal_title}",
            html_content=self._get_base_template(content)
        )
    
    async def send_proposal_under_review_notification(
        self,
        creator_email: str,
        creator_name: str,
        proposal_title: str,
        proposal_id: str
    ) -> bool:
        """Send notification when a proposal moves to under_review status"""
        content = f"""
<h2 style="margin: 0 0 16px 0; color: #0891b2; font-size: 20px;">📋 Your Proposal is Under Review</h2>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Hi {creator_name},
</p>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Good news! Your proposal has moved to the review stage.
</p>
<div style="background-color: #ecfeff; border-radius: 8px; padding: 20px; margin-bottom: 24px; border: 1px solid #a5f3fc;">
    <p style="margin: 0 0 8px 0; color: #0e7490; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Under Review</p>
    <p style="margin: 0; color: #0e7490; font-size: 18px; font-weight: 600;">{proposal_title}</p>
    <p style="margin: 8px 0 0 0; color: #0891b2; font-size: 14px;">ID: {proposal_id}</p>
</div>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    A reviewer is now actively evaluating your proposal. You'll be notified as soon as a decision is made.
</p>
<div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 16px; border-radius: 4px;">
    <p style="margin: 0; color: #92400e; font-size: 14px;">
        <strong>⏱ Average Review Time:</strong> Most proposals are reviewed within 24-48 hours.
    </p>
</div>
"""
        return await self.send_email(
            to_email=creator_email,
            subject=f"📋 Under Review: {proposal_title}",
            html_content=self._get_base_template(content)
        )
    
    async def send_proposal_completed_notification(
        self,
        creator_email: str,
        creator_name: str,
        proposal_title: str,
        proposal_id: str,
        project_id: str
    ) -> bool:
        """Send notification when a proposal/project is marked as completed"""
        content = f"""
<h2 style="margin: 0 0 16px 0; color: #7c3aed; font-size: 20px;">🏆 Project Completed!</h2>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Hi {creator_name},
</p>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Amazing work! Your project has been successfully completed.
</p>
<div style="background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%); border-radius: 8px; padding: 20px; margin-bottom: 24px;">
    <p style="margin: 0 0 8px 0; color: #5b21b6; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">✓ Completed</p>
    <p style="margin: 0; color: #5b21b6; font-size: 18px; font-weight: 600;">{proposal_title}</p>
    <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid rgba(139, 92, 246, 0.3);">
        <p style="margin: 0; color: #6d28d9; font-size: 14px;"><strong>Project ID:</strong> {project_id}</p>
    </div>
</div>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Thank you for being part of Creators Hive HQ! We hope this project was a success and look forward to your next venture.
</p>
<div style="background-color: #f0fdf4; border-left: 4px solid #22c55e; padding: 16px; border-radius: 4px; margin-bottom: 24px;">
    <p style="margin: 0; color: #166534; font-size: 14px;">
        <strong>🌟 What's Next?</strong> Ready for your next project? Start a new proposal anytime from your dashboard.
    </p>
</div>
<a href="#" style="display: inline-block; background-color: #6366f1; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; font-size: 14px;">Start New Proposal →</a>
"""
        return await self.send_email(
            to_email=creator_email,
            subject=f"🏆 Project Completed: {proposal_title}",
            html_content=self._get_base_template(content)
        )
    
    # ============== ELITE CONTACT US EMAIL TEMPLATES ==============
    
    async def send_elite_inquiry_to_sales(
        self,
        creator_name: str,
        creator_email: str,
        company_name: Optional[str],
        team_size: Optional[str],
        message: str,
        creator_id: str
    ) -> bool:
        """Send Elite tier inquiry to sales team"""
        sales_email = os.environ.get('SALES_EMAIL', 'sales@hivehq.com')
        
        company_section = f"""
<div style="background-color: #f3f4f6; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
    <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px; font-weight: 600;">Company Details</p>
    <p style="margin: 0; color: #111827; font-size: 14px;"><strong>Company:</strong> {company_name or 'Not provided'}</p>
    <p style="margin: 4px 0 0 0; color: #111827; font-size: 14px;"><strong>Team Size:</strong> {team_size or 'Not provided'}</p>
</div>
""" if company_name or team_size else ""
        
        content = f"""
<h2 style="margin: 0 0 16px 0; color: #f59e0b; font-size: 20px;">🌟 New Elite Plan Inquiry</h2>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    A creator has expressed interest in the Elite plan. Here are the details:
</p>

<div style="background-color: #fef3c7; border-radius: 8px; padding: 20px; margin-bottom: 24px; border: 1px solid #fcd34d;">
    <p style="margin: 0 0 12px 0; color: #92400e; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">Contact Information</p>
    <p style="margin: 0; color: #78350f; font-size: 18px; font-weight: 600;">{creator_name}</p>
    <p style="margin: 8px 0 0 0; color: #92400e; font-size: 14px;">Email: <a href="mailto:{creator_email}" style="color: #b45309; text-decoration: underline;">{creator_email}</a></p>
    <p style="margin: 4px 0 0 0; color: #92400e; font-size: 14px;">Creator ID: {creator_id}</p>
</div>

{company_section}

<div style="background-color: #f9fafb; border-radius: 8px; padding: 16px; margin-bottom: 24px; border-left: 4px solid #f59e0b;">
    <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px; font-weight: 600;">Message from Creator</p>
    <p style="margin: 0; color: #111827; font-size: 15px; line-height: 1.6; white-space: pre-wrap;">{message}</p>
</div>

<div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px;">
    <p style="margin: 0; color: #1e40af; font-size: 14px;">
        <strong>🎯 Action Required:</strong> Please respond to this inquiry within 24 hours to maintain our high-touch Elite service standards.
    </p>
</div>
"""
        return await self.send_email(
            to_email=sales_email,
            subject=f"🌟 Elite Plan Inquiry from {creator_name}",
            html_content=self._get_base_template(content)
        )
    
    async def send_elite_inquiry_confirmation(
        self,
        creator_email: str,
        creator_name: str
    ) -> bool:
        """Send confirmation email to creator who submitted Elite inquiry"""
        content = f"""
<h2 style="margin: 0 0 16px 0; color: #f59e0b; font-size: 20px;">🌟 Thank You for Your Interest in Elite!</h2>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Hi {creator_name},
</p>
<p style="margin: 0 0 24px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
    Thank you for your interest in our Elite plan! We've received your inquiry and our team is excited to connect with you.
</p>

<div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 8px; padding: 24px; margin-bottom: 24px;">
    <h3 style="margin: 0 0 16px 0; color: #92400e; font-size: 16px;">What happens next?</h3>
    <ol style="margin: 0; padding-left: 20px; color: #78350f; font-size: 15px; line-height: 2;">
        <li>Our Elite team will review your inquiry</li>
        <li>You'll receive a personalized response within 24 hours</li>
        <li>We'll schedule a call to discuss your specific needs</li>
        <li>Get a custom Elite package tailored to your goals</li>
    </ol>
</div>

<div style="background-color: #f3f4f6; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
    <h3 style="margin: 0 0 12px 0; color: #111827; font-size: 16px;">Elite Plan Includes:</h3>
    <ul style="margin: 0; padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.8;">
        <li>✨ Custom ARRIS workflows tailored to your needs</li>
        <li>🤝 Brand partnership integrations & tracking</li>
        <li>⚡ Priority ARRIS processing (fastest)</li>
        <li>📊 Fully customizable dashboard</li>
        <li>🎯 Dedicated account manager</li>
        <li>💬 SLA-guaranteed support</li>
    </ul>
</div>

<div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px;">
    <p style="margin: 0; color: #1e40af; font-size: 14px;">
        <strong>Questions?</strong> Feel free to reply to this email or reach out to us directly at <a href="mailto:sales@hivehq.com" style="color: #2563eb;">sales@hivehq.com</a>
    </p>
</div>
"""
        return await self.send_email(
            to_email=creator_email,
            subject="🌟 We've Received Your Elite Plan Inquiry!",
            html_content=self._get_base_template(content)
        )


# Singleton instance
email_service = EmailService()
