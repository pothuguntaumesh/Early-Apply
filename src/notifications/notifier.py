import boto3
import logging

log=logging.getLogger(__name__)

SES_SENDER="umesh.interviewprep@gmail.com"
ses_client = boto3.client("ses", region_name="us-east-1") 

async def send_email(recipient:str, jobs:list) -> None:
    subject=f"New jobs matching your preferences"
    body=f"Hi there,\n\nHere are your job alerts:\n\n"
    for job in jobs:
       body += f"- {job.title} at {job.company}\n  {job.job_url}\n\n"
    body += "Good luck!\n\n– EarlyApply"
    
    try:
        response=ses_client.send_email(
            Source=SES_SENDER,
            Destination={"ToAddresses":[recipient]},
            Message={"Subject":{"Data":subject},
            "Body":{"Text":{"Data":body}}})
        
        log.info(f"Email sent to {recipient} with subject {subject}")
    except Exception as e:
        log.error(f"Error sending email to {recipient}: {e}")
        raise


