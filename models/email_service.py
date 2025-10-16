import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailService:
    def __init__(self):
        # Email configuration
        self.mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
        self.mail_port = int(os.environ.get('MAIL_PORT', 587))
        self.mail_username = os.environ.get('MAIL_USERNAME')
        self.mail_password = os.environ.get('MAIL_PASSWORD')
        self.mail_use_tls = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'

    def send_email(self, to_email, subject, body):
        try:
            if not all([self.mail_username, self.mail_password, to_email]):
                print("Email configuration incomplete. Please set MAIL_USERNAME and MAIL_PASSWORD environment variables.")
                return False

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.mail_username
            msg['To'] = to_email
            msg['Subject'] = subject

            # Add body to email
            msg.attach(MIMEText(body, 'html'))

            # Create server connection
            server = smtplib.SMTP(self.mail_server, self.mail_port)
            if self.mail_use_tls:
                server.starttls()
            
            server.login(self.mail_username, self.mail_password)
            text = msg.as_string()
            server.sendmail(self.mail_username, to_email, text)
            server.quit()
            
            print(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_complaint_forward_email(self, department_email, complaint_details):
        subject = f"New Complaint Assigned - {complaint_details['category']}"
        body = f"""
        <html>
        <body>
            <h2>New Complaint Assignment</h2>
            <p>A new complaint has been assigned to your department:</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <h3>Complaint Details:</h3>
                <p><strong>Category:</strong> {complaint_details['category']}</p>
                <p><strong>Complaint Text:</strong> {complaint_details['text']}</p>
                <p><strong>Received:</strong> {complaint_details['timestamp']}</p>
                <p><strong>Complaint ID:</strong> {complaint_details['id']}</p>
            </div>
            
            <p>Please review this complaint and take appropriate action.</p>
            <p>Best regards,<br>Complaint Management System</p>
        </body>
        </html>
        """
        return self.send_email(department_email, subject, body)

    def send_case_completion_email(self, department_email, complaint_details):
        subject = f"Case Completed - Complaint #{complaint_details['id']}"
        body = f"""
        <html>
        <body>
            <h2>Case Successfully Resolved</h2>
            <p>The following complaint has been marked as completed:</p>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <h3>Complaint Details:</h3>
                <p><strong>Category:</strong> {complaint_details['category']}</p>
                <p><strong>Complaint Text:</strong> {complaint_details['text']}</p>
                <p><strong>Assigned To:</strong> {complaint_details['department']}</p>
                <p><strong>Completed At:</strong> {complaint_details['completed_at']}</p>
            </div>
            
            <p>This case is now closed in the system.</p>
            <p>Best regards,<br>Complaint Management System</p>
        </body>
        </html>
        """
        return self.send_email(department_email, subject, body)
    
    def send_sla_escalation_email(self, manager_email, complaint_details):
        subject = f"🚨 SLA Escalation - Complaint #{complaint_details['id']}"
        body = f"""
        <html>
        <body>
            <h2 style="color: #dc2626;">SLA Escalation Notice</h2>
            <p>The following complaint has exceeded the 24-hour response SLA and has been escalated:</p>
            
            <div style="background: #fef2f2; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #dc2626;">
                <h3>Complaint Details:</h3>
                <p><strong>ID:</strong> #{complaint_details['id']}</p>
                <p><strong>Category:</strong> {complaint_details['category']}</p>
                <p><strong>Received:</strong> {complaint_details['timestamp']}</p>
                <p><strong>Current Status:</strong> {complaint_details['status']}</p>
            </div>
            
            <p><strong>Action Required:</strong> Please review and ensure immediate attention.</p>
            <p>Best regards,<br>Complaint Management System</p>
        </body>
        </html>
        """
        return self.send_email(manager_email, subject, body)

    def send_resolution_feedback_email(self, customer_email, complaint_details):
        subject = f"Resolution Feedback - Complaint #{complaint_details['id']}"
        body = f"""
        <html>
        <body>
            <h2>How was your experience?</h2>
            <p>Your complaint has been resolved. We'd appreciate your feedback:</p>
            
            <div style="background: #f0f9ff; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <h3>Complaint Summary:</h3>
                <p><strong>Category:</strong> {complaint_details['category']}</p>
                <p><strong>Resolution:</strong> {complaint_details['resolution']}</p>
                <p><strong>Completed:</strong> {complaint_details['completed_at']}</p>
            </div>
            
            <p><a href="{complaint_details['feedback_link']}" style="background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Provide Feedback</a></p>
            
            <p>Thank you for helping us improve our service!</p>
            <p>Best regards,<br>Complaint Management System</p>
        </body>
        </html>
        """
        return self.send_email(customer_email, subject, body)