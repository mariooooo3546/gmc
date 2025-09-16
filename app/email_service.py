"""Email service for sending alerts via SendGrid."""

import logging
from datetime import datetime
from typing import List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from .config import settings
from .models import ProductStatusCounts, IssueCode, ProductStatusSnapshot
from .database import db_service

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email alerts."""
    
    def __init__(self):
        self.sg = SendGridAPIClient(api_key=settings.sendgrid_api_key)
    
    def send_alert_email(
        self,
        totals: ProductStatusCounts,
        delta_disapproved: int,
        top_issues: List[IssueCode],
        country: str,
        reporting_context: str
    ) -> bool:
        """Send alert email when thresholds are exceeded."""
        try:
            subject = f"🚨 Merchant Center Alert - {country} ({reporting_context})"
            
            # Calculate total problematic products
            problematic_total = totals.disapproved + totals.suspended + totals.limited
            
            # Create email body
            body = self._create_alert_email_body(
                totals, delta_disapproved, top_issues, country, reporting_context
            )
            
            # Create email
            from_email = Email(settings.mail_from)
            to_email = To(settings.mail_to)
            content = Content("text/html", body)
            
            mail = Mail(from_email, to_email, subject, content)
            
            # Send email
            response = self.sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Alert email sent successfully to {settings.mail_to}")
                
                # Save email record to database
                db_service.save_email_alert(
                    to=settings.mail_to,
                    subject=subject,
                    body=body
                )
                
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending alert email: {e}")
            return False
    
    def _create_alert_email_body(
        self,
        totals: ProductStatusCounts,
        delta_disapproved: int,
        top_issues: List[IssueCode],
        country: str,
        reporting_context: str
    ) -> str:
        """Create HTML email body for alert."""
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Calculate totals
        total_products = (totals.approved + totals.pending + totals.disapproved + 
                         totals.limited + totals.suspended + totals.under_review + totals.processing)
        problematic_total = totals.disapproved + totals.suspended + totals.limited
        
        # Create issues table
        issues_table = ""
        if top_issues:
            issues_table = """
            <h3>🔍 Top Issue Codes:</h3>
            <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Issue Code</th>
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Description</th>
                        <th style="border: 1px solid #ddd; padding: 12px; text-align: center;">Count</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for issue in top_issues:
                issues_table += f"""
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 12px;"><code>{issue.code}</code></td>
                        <td style="border: 1px solid #ddd; padding: 12px;">{issue.description}</td>
                        <td style="border: 1px solid #ddd; padding: 12px; text-align: center; color: #dc3545; font-weight: bold;">{issue.count}</td>
                    </tr>
                """
            
            issues_table += """
                </tbody>
            </table>
            """
        
        # Delta indicator
        delta_indicator = ""
        if delta_disapproved > 0:
            delta_indicator = f'<span style="color: #dc3545; font-weight: bold;">+{delta_disapproved}</span>'
        elif delta_disapproved < 0:
            delta_indicator = f'<span style="color: #28a745; font-weight: bold;">{delta_disapproved}</span>'
        else:
            delta_indicator = '<span style="color: #6c757d;">0</span>'
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Merchant Center Alert</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin-bottom: 20px;">
                <h2 style="color: #721c24; margin: 0;">🚨 Merchant Center Alert</h2>
                <p style="margin: 5px 0 0 0; color: #721c24;">Product status thresholds exceeded</p>
            </div>
            
            <div style="background-color: #f8f9fa; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                <h3>📊 Check Details:</h3>
                <ul>
                    <li><strong>Time:</strong> {current_time}</li>
                    <li><strong>Country:</strong> {country}</li>
                    <li><strong>Reporting Context:</strong> {reporting_context}</li>
                </ul>
            </div>
            
            <div style="background-color: #fff; border: 1px solid #ddd; border-radius: 5px; padding: 20px; margin-bottom: 20px;">
                <h3>📈 Product Status Summary:</h3>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Total Products:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold;">{total_products:,}</td>
                    </tr>
                    <tr style="background-color: #d4edda;">
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>✅ Approved:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right; color: #155724; font-weight: bold;">{totals.approved:,}</td>
                    </tr>
                    <tr style="background-color: #fff3cd;">
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>⏳ Pending:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right; color: #856404; font-weight: bold;">{totals.pending:,}</td>
                    </tr>
                    <tr style="background-color: #f8d7da;">
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>❌ Disapproved:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right; color: #721c24; font-weight: bold;">{totals.disapproved:,}</td>
                    </tr>
                    <tr style="background-color: #f8d7da;">
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>⚠️ Limited:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right; color: #721c24; font-weight: bold;">{totals.limited:,}</td>
                    </tr>
                    <tr style="background-color: #f8d7da;">
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>🚫 Suspended:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right; color: #721c24; font-weight: bold;">{totals.suspended:,}</td>
                    </tr>
                    <tr style="background-color: #d1ecf1;">
                        <td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>🔍 Under Review:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right; color: #0c5460; font-weight: bold;">{totals.under_review:,}</td>
                    </tr>
                    <tr style="background-color: #e2e3e5;">
                        <td style="padding: 8px;"><strong>⚙️ Processing:</strong></td>
                        <td style="padding: 8px; text-align: right; color: #383d41; font-weight: bold;">{totals.processing:,}</td>
                    </tr>
                </table>
                
                <div style="margin-top: 15px; padding: 10px; background-color: #f8f9fa; border-radius: 3px;">
                    <strong>Problematic Products Total:</strong> <span style="color: #dc3545; font-weight: bold;">{problematic_total:,}</span><br>
                    <strong>Disapproved Delta:</strong> {delta_indicator}
                </div>
            </div>
            
            {issues_table}
            
            <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; padding: 15px; margin-top: 20px;">
                <h3>🔗 Quick Actions:</h3>
                <p>
                    <a href="https://merchants.google.com/mc/products?a={settings.merchant_account_id}" 
                       style="color: #0c5460; text-decoration: none; font-weight: bold;">
                        📋 View Products in Merchant Center
                    </a><br>
                    <a href="https://merchants.google.com/mc/diagnostics?a={settings.merchant_account_id}" 
                       style="color: #0c5460; text-decoration: none; font-weight: bold;">
                        🔧 View Diagnostics
                    </a>
                </p>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #6c757d; font-size: 12px;">
                <p>This alert was generated by the Merchant Center Monitoring Service.</p>
                <p>Check time: {current_time}</p>
            </div>
        </body>
        </html>
        """
        
        return html_body


# Global email service instance
email_service = EmailService()
