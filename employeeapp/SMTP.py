import os
import pandas as pd
from datetime import datetime
import smtplib
from smtplib import SMTPException 
from email.mime.text import MIMEText
from configparser import ConfigParser
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from django.conf import settings

def sending_mail(email_subject,email_to,mail_from,message):
    try:
        msg = MIMEMultipart()
        text = MIMEText(f"""
       Hi Team,
        
       {message}

       Thanks,

       BI Team

        """)
        msg['Subject'] = f"{email_subject}"
        msg['From'] = f'{mail_from}'
        msg['To'] = f"{email_to}"
        sender = f"{mail_from}"
        msg.attach(text)
        # smtpobj = smtplib.SMTP(f"{settings.smtp_server_name}",int(settings.smtp_port))
        smtpobj = smtplib.SMTP("smtp.office365.com",587)
        smtpobj.sendmail(sender, email_to, msg.as_string())
        print("Successfully sent mail *************************************************************")
    except Exception as e:
        print(f"We are facing issue while sending intimation mail and the error is - {e}###################################################")
