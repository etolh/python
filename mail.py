set MAIL_USERNAME=<sender mail>
set MAIL_PASSWORD=<mail password>
set FLASKY_TO=<sender to>

set MAIL_USERNAME=2137243608@qq.com
set MAIL_PASSWORD=dnasbitqdxwbfcac
set FLASKY_TO=820652313@qq.com

from flask.ext.mail import Message
from hello import mail
msg = Message('test subject', sender='2137243608@qq.com',recipients=['820652313@qq.com'])

msg.body = 'text body'
msg.html = '<b>HTML</b> body'
with app.app_context():
    mail.send(msg)