from datetime import time
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .supabase_client import supabase
from .helper_functions import get_access_token
from .models import Setting, SearchSetting, PreviousSearch, Summary, AccountInformation
from django.views.decorators.csrf import csrf_exempt
import pytz


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

    context = {
        'title': 'Briefly - Login',
    }

    return render(request, 'header.html', context)


# Logout User
def logout_view(request):
    if request.method == 'GET':
        request.session.flush()

    context = {
        'title': 'Briefly - Login',
    }

    return render(request, 'header.html', context)


# Retrieve User Settings
def settings_view(request):
    # Retrieve the access token and user data
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    try:
        # Fetch the user settings
        user_id = user_data.id
        user_settings = Setting.objects.get(user_id=user_id)

        context = {
            'title': 'Briefly - Settings',
            'user_authenticated': True,
            'user_data': {
                'id': user_data.id,
                'email': user_data.email,
                'settings': {
                    'date_range': user_settings.date_range,
                    'email_reports': user_settings.email_reports,
                    'report_time': user_settings.report_time,
                    'timezone': user_settings.timezone,
                    'language': user_settings.language,
                },
            },
            'timezones': pytz.all_timezones,  # Pass the list of all time zones
            'error': None,
        }
    except Setting.DoesNotExist:
        # If no settings exist, allow the user to create them
        context = {
            'title': 'Briefly - Create Settings',
            'user_authenticated': True,
            'user_data': {
                'id': user_data.id,
                'email': user_data.email,
            },
            'timezones': pytz.all_timezones,  # Pass the list of all time zones
            'error': 'User settings not found.',
        }

    return render(request, 'settings.html', context)



@csrf_exempt
def settings_changed(request):
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    if request.method == "POST":
        # Retrieve the form data
        date_range = request.POST.get('date_range')
        email_reports = request.POST.get('email_reports') == 'True'
        report_time = request.POST.get('report_time')
        timezone = request.POST.get('timezone')
        language = request.POST.get('language')

        # Validate and parse report_time
        try:
            if report_time:
                hours, minutes, seconds = map(int, report_time.split(":"))
                report_time = time(hour=hours, minute=minutes, second=seconds)
        except ValueError:
            return JsonResponse({'error': 'Invalid time format. Use HH:MM:SS.'}, status=400)

        # Get or create the user's settings
        user_id = user_data.id
        setting, created = Setting.objects.update_or_create(
            user_id=user_id,
            defaults={
                'date_range': date_range,
                'email_reports': email_reports,
                'report_time': report_time,
                'timezone': timezone,
                'language': language,
            }
        )

        context = {
            'updated_settings': setting,
            'created': created
        }

        return redirect('/settings/', context)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def account_view(request):
    # Retrieve the access token and user data
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    try:
        # Fetch the user settings
        user_id = user_data.id
        account_information = AccountInformation.objects.get(user_id=user_id)

        context = {
            'title': 'Briefly - Account',
            'user_authenticated': True,
            'user_data': {
                'id': user_data.id,
                'email': user_data.email,
                'account': {
                    'full_name': account_information.full_name,
                    'position': account_information.position,
                    'company': account_information.company,
                    'report_email': account_information.report_email,
                    'phonenr': account_information.phonenr
                },
            },
            'error': None,
        }

    except AccountInformation.DoesNotExist:
        # If no account_information exist, allow the user to create them
        context = {
            'title': 'Briefly - Add Account Information',
            'user_authenticated': True,
            'user_data': {
                'id': user_data.id,
                'email': user_data.email,
            },
            'error': 'Account information for user not found.',
        }

    return render(request, 'account.html', context)

def account_changed(request):
    return