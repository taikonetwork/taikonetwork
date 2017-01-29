from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_protect

from map import views


def index(request):
    return render(request, 'home/index.html')


def about(request):
    return render(request, 'home/about.html')


@csrf_protect
def login_form(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            return redirect(views.groupmap)
        else:
            return redirect(index)
    else:
        return redirect(index)


def retrieve_account(request):
    # try:
    email = request.GET.get('acct-email', ' ')
    # result = Member.objects.filter(email=email)
    test_emails = {'test@gmail.com': [{'firstname': 'John', 'lastname': 'Smith', 'sf_id': 'ID123456789'}],
                   'asdf@gmail.com': [{'firstname': 'TestFirst', 'lastname': 'TestLast', 'sf_id': 'ASDADGREE1243'}]
                   }
    result = test_emails.get(email, [None])

    if result[0]:
        name = result[0]['firstname'] + ' ' + result[0]['lastname']
        # sf_id = result[0]['sf_id']
        title = 'SUCCESS!'
        body = 'Are you the following member: {}?'.format(name)

        return render(request, 'home/login.html', {'status': 'success',
                                                   'alert_title': title,
                                                   'alert_body': body})
    else:
        title = 'SORRY!'
        body = 'No accounts matching the provided email address was found.'

        return render(request, 'home/login.html', {'status': 'error',
                                                   'alert_title': title,
                                                   'alert_body': body})
    # except:
    #    title = 'ERROR!'
    #    body = 'Unable to process request. Please try again.'

    #   return render(request, 'home/login.html', {'status': 'error',
    #                                              'alert_title': title,
    #                                              'alert_body': body})
