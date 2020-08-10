from .email import send_email
import celery
from . import create_app


app = create_app()
app.app_context().push()
send_email_task = celery.task(send_email)