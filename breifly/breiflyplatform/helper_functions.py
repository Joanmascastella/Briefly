from django.shortcuts import render, redirect
from django.http import JsonResponse
from .supabase_client import supabase
from django.utils.html import strip_tags
from django.middleware.csrf import CsrfViewMiddleware

# Helper functions

def validate_csrf(request):
    try:
        CsrfViewMiddleware().process_view(request, None, None, None)
    except Exception as e:
        return JsonResponse({'error': 'CSRF token validation failed'}, status=403)

# Helper function to get the access token from the session
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

# Helper function to sanitize user input
def sanitize(value):
    """
    Removes any HTML tags and strips leading/trailing whitespace.
    """
    if value is None:
        return ''
    return strip_tags(value).strip()


# Helper function to check if the request is for JSON
def wants_json_response(request):
    """
    Helper to check if the client prefers JSON (e.g., for AJAX calls).
    We'll look for 'Accept: application/json' or a similar indicator.
    """
    accept_header = request.headers.get('Accept', '')
    return 'application/json' in accept_header

def validate_date_range(date_range):
    """
    Ensures date_range matches the valid database enum values.
    """
    valid_ranges = {"anytime", "past_hour", "past_twenty_four_hours", "past_week", "past_year"}
    return date_range if date_range in valid_ranges else "anytime"