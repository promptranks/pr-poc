import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailService:
    @staticmethod
    def send_email(to_email: str, subject: str, html_body: str):
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("SMTP_FROM_EMAIL", smtp_user)

        if not smtp_user or not smtp_password:
            print(f"SMTP not configured, skipping email to {to_email}")
            return

        smtp_port = int(os.getenv("SMTP_PORT") or "587")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = to_email

        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")

    @staticmethod
    def send_welcome_email(to_email: str, name: str):
        subject = "Welcome to PromptRanks!"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>Welcome to PromptRanks!</h2>
            <p>Hi {name},</p>
            <p>You're all set. Here's what you can do:</p>
            <ul>
                <li>✓ Take unlimited quick assessments</li>
                <li>✓ View your scores on the leaderboard</li>
                <li>✓ Earn verifiable badges</li>
            </ul>
            <p>Want more? Upgrade to Premium for:</p>
            <ul>
                <li>• 3 full assessments per month</li>
                <li>• Industry & role targeting</li>
                <li>• Detailed analytics</li>
                <li>• Priority support</li>
            </ul>
            <p><a href="{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/pricing" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Upgrade to Premium</a></p>
            <p>Happy prompting!</p>
            <p>—<br>PromptRanks Team</p>
        </body>
        </html>
        """
        EmailService.send_email(to_email, subject, html_body)

    @staticmethod
    def send_upgrade_email(to_email: str, name: str):
        subject = "Welcome to PromptRanks Premium!"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>You're now a Premium member!</h2>
            <p>Hi {name},</p>
            <p>Your benefits:</p>
            <ul>
                <li>• 3 full assessments per month</li>
                <li>• Industry & role-specific insights</li>
                <li>• Advanced analytics dashboard</li>
                <li>• Priority support</li>
            </ul>
            <p><a href="{os.getenv('FRONTEND_URL', 'http://localhost:5173')}/dashboard" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Go to Dashboard</a></p>
            <p>Questions? Reply to this email.</p>
            <p>—<br>PromptRanks Team</p>
        </body>
        </html>
        """
        EmailService.send_email(to_email, subject, html_body)
