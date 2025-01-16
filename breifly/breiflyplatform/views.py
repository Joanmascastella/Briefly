from django.shortcuts import render, redirect
from django.http import JsonResponse
from .supabase_client import supabase


# Landing page of the website
def landing_page(request):
    # Get the access token from the session
    access_token = request.session.get('access_token')
    user_authenticated = False
    user_data = None

    if access_token:
        try:
            # Fetch user data using the access token
            user_response = supabase.auth.get_user(access_token)

            if user_response.user:
                # If valid, mark the user as authenticated and fetch user details
                user_authenticated = True
                user_data = user_response.user  # Access the user object
            else:
                # If invalid, clear the session
                request.session.flush()
        except Exception as e:
            print(f"Error verifying token: {e}")
            request.session.flush()

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
