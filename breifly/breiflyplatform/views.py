from django.shortcuts import render, redirect
from django.http import JsonResponse
from .supabase_client import supabase
from .helper_functions import get_access_token

# Landing page of the website
def landing_page(request):
    # Get the access token from the session
    user_authenticated, user_data = get_access_token(request)

    context = {
        'title': 'Briefly - Home',
        'user_authenticated': user_authenticated,
        'user': user_data,
    }

    return render(request, 'header.html', context)


# Login page logic
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # Sign in the user with email and password
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})

            if response.user:
                # Save the access token and user data in the session
                request.session['access_token'] = response.session.access_token
                request.session['user'] = {
                    "id": response.user.id,
                    "email": response.user.email
                }
                return redirect('/')
            else:
                # Handle login errors
                return JsonResponse({'error': 'Invalid email or password'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'header.html')


def logout_view(request):
    if request.method == 'GET':
        request.session.flush()

    return render(request, 'header.html')

def settings_view(request):
    user_authenticated, user_data = get_access_token(request)

    context = {
        'user_authenticated': user_authenticated,
        'user_data': user_data
    }

    return render(request, 'settings.html', context)