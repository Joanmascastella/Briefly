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



