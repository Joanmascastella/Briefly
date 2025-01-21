from django.shortcuts import render, redirect
from django.http import JsonResponse
from .supabase_client import supabase


def get_access_token(request):
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

    return user_authenticated, user_data

def get_navbar_partial(user_authenticated, new_user, roles):
    """
    Return the path to the appropriate navbar partial
    based on authentication, new_user status, and roles.
    """
    if not user_authenticated:
        return 'partials/not_authenticated_navbar.html'
    elif 'admin' in roles:
        return 'partials/authenticated_navbar_admin.html'
    elif new_user == 'true':
        return 'partials/authenticated_navbar_new_user.html'
    else:
        return 'partials/authenticated_navbar.html'



