from django.shortcuts import render


def display_metrics(request):
    message = 'Taiko Network metrics coming soon...'
    return render(request, 'metrics/metrics.html', {'message': message})
