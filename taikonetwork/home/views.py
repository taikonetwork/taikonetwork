from django.shortcuts import render


def index(request):
    return render(request, 'home/index.html')


def about(request):
    return render(request, 'home/about.html')


def login(request):
    return render(request, 'home/login.html')


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
