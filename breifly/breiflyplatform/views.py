from django.shortcuts import render



def landing_page(request):
    context = {
        'title': 'Briefly - Home',
        'user_authenticated': request.user.is_authenticated,

    }

    return render(request, 'header.html', context)

