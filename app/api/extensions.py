import hashlib
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
import yookassa
import uuid
import time
from app.extensions import db
import os

def shifrator(password):
    return hashlib.md5(password.encode("utf-8")).hexdigest()

def tokenizer(email):
    time_hash = time.time()
    email_hash = hashlib.sha256((email + str(time_hash)).encode("utf-8")).hexdigest()
    return email_hash

def renderMail(html, **kwargs):
    raw = open("templates/" + html).read()
    split_raw = raw.split("}}")
    sp = []
    for i in split_raw:
        sp.extend(i.split("{{"))
    mail = []
    for i in sp:
        if i in kwargs:
            mail.append(kwargs[i])
        else:
            mail.append(i)
    return "".join(mail)

def sendMail(client_mail, message, header, server_mail, server_pass):
    msg = MIMEText(message, "html", "utf-8")
    msg['Subject'] = header
    msg['From'] = server_mail
    msg['To'] = client_mail
    if "yandex" in server_mail:
        while True:
            try:
                smtp = SMTP_SSL('smtp.yandex.ru')
                break
            except TimeoutError:
                pass
    else:
        smtp = SMTP_SSL('smtp.gmail.com')
    smtp.login(server_mail, server_pass)
    smtp.sendmail(server_mail, client_mail, msg.as_string())
    smtp.quit()

def create_payment():
    yookassa.Configuration.account_id = 315655
    yookassa.Configuration.secret_key = ""
    idempotence_key = str(uuid.uuid4())
    payment = yookassa.Payment.create({
        "amount": {
            "value": "2.00",
            "currency": "RUB"
        },
        "payment_method_data": {
            "type": "bank_card"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://skillfix-platform.ru"
        },
        "description": "Подписка на курсы skillfix",
        "receipt": {
            "customer": {
                "email": "skillfix-platform@yandex.ru"
            },
            "items": [{
                "description": "Подписка на курсы skillfix",
                "amount": {
                    "value": "2.00",
                    "currency": "RUB"
                },
                "vat_code": 1,
                "quantity": 1
            }]
        }
    }, idempotence_key)

    # get confirmation url
    confirmation_url = payment.confirmation.confirmation_url
    payment_id = payment.id
    return confirmation_url, payment_id

def wait_payment(payment_id, user):
    start = time.time()
    while True:
        if time.time() - start > 15 * 60:
            break
        payment = yookassa.Payment.find_one(payment_id)
        if payment.status == "waiting_for_capture":
            idempotence_key = str(uuid.uuid4())
            response = yookassa.Payment.capture(
              payment_id,
              {
                "amount": {
                  "value": "2.00",
                  "currency": "RUB"
                }
              },
              idempotence_key
            )
            if response.status == "succeeded":
                user.submited = 1
                db.session.commit()
                break
        time.sleep(1)

def get_chunk(filename, byte1=None, byte2=None):
    full_path = 'app/api/video/' + filename
    file_size = os.stat(full_path).st_size
    start = 0
    
    if byte1 < file_size:
        start = byte1
    if byte2:
        length = byte2 + 1 - byte1
    else:
        length = file_size - start
    if length > 1324798487 / 1024 * 500:
        length = int(1324798487 / 1024 * 500)
    with open(full_path, 'rb') as f:
        f.seek(start)
        print(length)
        chunk = f.read(length)
    return chunk, start, length, file_size