from django.shortcuts import render, reverse
from django.contrib.auth import login
from ippanel import Client
from random import randint
import os
import hashlib
from django.contrib.auth.models import User


def main_page(request):
    return render(request, 'misProject/force_redirect.html', {'url': reverse('score:lessons')})


def login_page(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return render(request, 'score/message_redirect.html',
                          {'url': reverse('score:lessons'), 'message': 'شما قبلا لاگین کرده اید.'})
        else:
            return render(request, 'misProject/login_page.html')
    else:
        # if post phone number
        if request.POST['verification_code'] == '':
            # Checking the user's existence
            user = User.objects.filter(username=request.POST['phone'])
            if not user:
                return render(request, 'score/message_redirect.html',
                              {'url': reverse('login_page'), 'message': 'شماره موبایل اشتباه است'})

            # api key that generated from panel
            api_key = os.getenv("SMS_API_KEY")
            # client instance
            sms = Client(api_key)
            # Changing the format of the number to the format accepted by the SMS system
            phone_number = '98' + request.POST['phone'][1:]
            # Variables within the SMS template
            pattern_values = {
                "verification-code": randint(1001, 9998),
            }
            message_id = sms.send_pattern(
                os.getenv("SMS_Pattern_Code"),  # SMS template code in the SMS system
                os.getenv("SMS_Sending_Number"),  # originator
                phone_number,  # recipient
                pattern_values,  # pattern values
            )

            # hash verification code
            verification_code_str = str(pattern_values["verification-code"])
            verification_code_hash = hashlib.sha1(verification_code_str.encode('utf-8')).hexdigest()
            return render(request, 'misProject/login_page.html',
                          {'level': 2, 'phone': request.POST['phone'],
                           'verification_code_hash': verification_code_hash})
        # post verification code
        else:
            verification_code_str = str(request.POST['verification_code'])
            verification_code_hash = hashlib.sha1(verification_code_str.encode('utf-8')).hexdigest()
            if verification_code_hash == request.POST['verification_code_hash']:
                phone = '0' + request.POST['phone']
                user = User.objects.filter(username=phone)
                login(request, user[0])
                return render(request, 'score/message_redirect.html',
                              {'url': reverse('score:lessons'), 'message': 'خوش آمدید'})
            else:
                return render(request, 'score/message_redirect.html',
                              {'url': reverse('login_page'), 'message': 'کد وارد شده اشتباه است'})
