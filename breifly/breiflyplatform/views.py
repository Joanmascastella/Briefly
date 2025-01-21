import json
from datetime import time

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pytz

from .supabase_client import supabase
from .helper_functions import get_access_token, get_navbar_partial
from .models import (
    Setting,
    SearchSetting,
    PreviousSearch,
    Summary,
    UserRole,
    AccountInformation,
    ScheduledSearch,
    User
)
from .get_news import search_news, get_period_param
from django.core.paginator import Paginator


# --------------------------------
# Public / Landing Views
# --------------------------------

# Landing page of the website
def landing_page(request):
    """
    Displays the landing/home page for authenticated users or redirects to login if not authenticated.
    """
    # Get the access token from the session
    user_authenticated, user_data = get_access_token(request)

    # Redirect to login if the user is not authenticated
    if not user_authenticated:
        return redirect('/login')

    user_id = user_data.id

    # Check if Settings and Account Information exist
    settings_exist = Setting.objects.filter(user_id=user_id).exists()
    account_info_exist = AccountInformation.objects.filter(user_id=user_id).exists()

    # Fetch the user's roles
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    # Determine if user is "new_user"
    new_user_status = 'true' if (not settings_exist or not account_info_exist) else 'false'

    # Decide which navbar to use
    navbar_partial = get_navbar_partial(user_authenticated, new_user_status, roles)

    # If user is "new", you redirect to `main_page_new_user.html`
    if 'user' in roles:
        if not settings_exist or not account_info_exist:
            context = {
                'title': 'Briefly - Home',
                'user_authenticated': user_authenticated,
                'user': user_data,
                'timezones': pytz.all_timezones,
                'new_user': 'true',
                'navbar_partial': navbar_partial,
            }
            return render(request, 'main_page_new_user.html', context)

        # Otherwise, render the main page
        placeholders = {
            'keywords': '',
            'publishers': '',
            'date_range': 'anytime',
            'description': '',
        }
        try:
            search_settings = SearchSetting.objects.get(user_id=user_id)
            placeholders.update({
                'keywords': search_settings.keywords or '',
                'publishers': search_settings.publishers or '',
                'date_range': search_settings.frequency or 'anytime',
                'description': search_settings.search_description or '',
            })
        except SearchSetting.DoesNotExist:
            pass

        context = {
            'title': 'Briefly - Home',
            'user_authenticated': user_authenticated,
            'user': user_data,
            'placeholders': placeholders,
            'roles': roles,
            'navbar_partial': navbar_partial,
        }
        return render(request, 'main_page.html', context)

    elif 'admin' in roles:
        return redirect('/custom-admin/dashboard/')
    else:
        return redirect('/error/page/')


def error_page(request):
    """
    Renders a generic error (404) page.
    """
    # Even on the error page, we can decide to show a navbar if the user is logged in
    user_authenticated, user_data = get_access_token(request)
    new_user_status = 'false'
    roles = []

    if user_data:
        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

    navbar_partial = get_navbar_partial(user_authenticated, new_user_status, roles)

    return render(request, '404.html', {'navbar_partial': navbar_partial})


# --------------------------------
# Authentication Views
# --------------------------------

# Login page logic
def login_view(request):
    """
    Handles user login using Supabase authentication.
    """
    # Compute navbar partial even on the login screen
    user_authenticated, user_data = get_access_token(request)
    new_user_status = 'false'
    roles = []

    if user_data:
        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

    navbar_partial = get_navbar_partial(user_authenticated, new_user_status, roles)

    context = {
        'title': 'Briefly - Login',
        'error': '',
        'navbar_partial': navbar_partial,
    }

    if request.method == 'GET':
        return render(request, 'loginForm.html', context)


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

                # Fetch the user's roles
                user_id = response.user.id
                user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
                roles = [user_role.role.name for user_role in user_roles]

                if 'user' in roles:
                    return redirect('/')
                elif 'admin' in roles:
                    return redirect('/custom-admin/dashboard/')
            else:
                # Handle login errors
                context['error'] = 'Invalid email or password'
        except Exception as e:
            # Add the error message to context for frontend
            context['error'] = str(e)

    return render(request, 'main_page.html', context)


# Logout User
def logout_view(request):
    """
    Logs out the current user by clearing the session.
    """
    if request.method == 'GET':
        request.session.flush()

    # We only redirect, so no template is rendered (no navbar_partial needed here)
    return redirect('/login/')


@csrf_exempt
def finalise_new_user(request):
    """
    Finalizes registration details for a new user (e.g., personal and account info).
    """
    # This view redirects or returns JSON, so no need for navbar context
    user_authenticated, user_data = get_access_token(request)
    user_id = user_data.id

    if not user_authenticated or not user_data:
        return redirect('/login/')

    # Fetch the user's roles
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    if 'user' in roles:
        if request.method == 'POST':
            full_name = request.POST.get('full_name')
            position = request.POST.get('position')
            report_email = request.POST.get('report_email')
            phonenr = request.POST.get('phonenr')
            target_audience = request.POST.get('target_audience')
            content_sentiment = request.POST.get('content_sentiment')
            company = request.POST.get('company')
            industry = request.POST.get('industry')
            company_brief = request.POST.get('company_brief')
            recent_ventures = request.POST.get('recent_ventures')
            account_version = "standard"

            # Settings
            email_reports = request.POST.get('email_reports')
            timezone = request.POST.get('timezone')

            # Create the user's settings
            Setting.objects.update_or_create(
                user_id=user_id,
                defaults={
                    'email_reports': email_reports,
                    'timezone': timezone,
                }
            )

            # Create account information
            AccountInformation.objects.update_or_create(
                user_id=user_id,
                defaults={
                    "full_name": full_name,
                    "position": position,
                    "phonenr": phonenr,
                    "target_audience": target_audience,
                    "content_sentiment": content_sentiment,
                    "company": company,
                    "report_email": report_email,
                    "industry": industry,
                    "company_brief": company_brief,
                    "recent_ventures": recent_ventures,
                    "account_version": account_version,
                }
            )

        return redirect('/')

    return JsonResponse({'error': 'Invalid request method'}, status=400)


# --------------------------------
# Admin Views
# --------------------------------

def admin_dashboard(request):
    """
    Displays the admin dashboard with a list of users and their account information.
    """
    user_authenticated, user_data = get_access_token(request)
    new_user_status = 'false'
    roles = []

    if user_data:
        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

    navbar_partial = get_navbar_partial(user_authenticated, new_user_status, roles)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    if request.method == 'GET':
        if 'admin' in roles:
            # Step 1: Fetch all users from `auth.users`
            users = User.objects.all()

            # Step 2: Fetch all UserRole objects with `role_id=2` (user role)
            user_roles = UserRole.objects.filter(role_id=2)

            # Step 3: Match users with `user_id` from user_roles
            user_ids_with_role_user = {user_role.user_id for user_role in user_roles}
            users_with_role_user = [user for user in users if user.id in user_ids_with_role_user]

            # Step 4: Fetch AccountInformation for matched user IDs
            account_info_list = AccountInformation.objects.filter(user_id__in=user_ids_with_role_user)

            # Prepare the data for the template
            users_with_account_info = []
            for user in users_with_role_user:
                account_info = account_info_list.filter(user_id=user.id).first()
                if account_info:
                    users_with_account_info.append({
                        'user_id': user.id,
                        'email': user.email,
                        'full_name': account_info.full_name,
                        'position': account_info.position,
                        'company': account_info.company,
                        'report_email': account_info.report_email,
                        'phonenr': account_info.phonenr,
                        'target_audience': account_info.target_audience,
                        'industry': account_info.industry,
                        'content_sentiment': account_info.content_sentiment,
                        'company_brief': account_info.company_brief,
                        'recent_ventures': account_info.recent_ventures,
                        'account_version': account_info.account_version,
                    })

            # -- PAGINATION LOGIC --
            paginator = Paginator(users_with_account_info, 5)
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)

            context = {
                'title': 'Briefly - Admin Dashboard',
                'user_authenticated': True,
                'user_data': {
                    'id': user_data.id,
                    'email': user_data.email,
                },
                'roles': roles,
                'page_obj': page_obj,
                'is_paginated': page_obj.has_other_pages(),
                'paginator': paginator,
                'navbar_partial': navbar_partial,
            }

            return render(request, 'admin_dashboard.html', context)
        else:
            return redirect('/error/page/')

    # When an admin updates account_version via POST
    if request.method == 'POST':
        if 'admin' in roles:
            user_id_to_update = request.POST.get('user_id')
            new_account_version = request.POST.get('account_version')

            # Update that user's 'account_version' field in AccountInformation
            account_information_obj = AccountInformation.objects.get(user_id=user_id_to_update)
            account_information_obj.account_version = new_account_version
            account_information_obj.save()

            return redirect('/custom-admin/dashboard/')
        else:
            return JsonResponse({'error': 'Not authorized'}, status=403)


# --------------------------------
# User Settings Views
# --------------------------------

# Retrieve User Settings
def settings_view(request):
    """
    Fetches and displays the user's settings for editing.
    """
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    roles = []
    new_user_status = 'false'
    user_id = user_data.id

    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    navbar_partial = get_navbar_partial(user_authenticated, new_user_status, roles)

    if 'user' in roles:
        try:
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
                'timezones': pytz.all_timezones,
                'error': None,
                'navbar_partial': navbar_partial,
            }
        except Setting.DoesNotExist:
            context = {
                'title': 'Briefly - Create Settings',
                'user_authenticated': True,
                'user_data': {
                    'id': user_data.id,
                    'email': user_data.email,
                },
                'timezones': pytz.all_timezones,
                'error': 'User settings not found.',
                'navbar_partial': navbar_partial,
            }

        return render(request, 'settings.html', context)
    else:
        return redirect('/error/page/')


@csrf_exempt
def settings_changed(request):
    """
    Handles updating user settings (date range, email reports, report time, timezone, language).
    """
    # This view redirects, so no navbar needed
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    user_id = user_data.id
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    if 'user' in roles:
        if request.method == "POST":
            date_range = request.POST.get('date_range')
            email_reports = request.POST.get('email_reports') == 'True'
            report_time = request.POST.get('report_time')
            timezone = request.POST.get('timezone')
            language = request.POST.get('language')

            try:
                if report_time:
                    hours, minutes, seconds = map(int, report_time.split(":"))
                    report_time = time(hour=hours, minute=minutes, second=seconds)
            except ValueError:
                return JsonResponse({'error': 'Invalid time format. Use HH:MM:SS.'}, status=400)

            Setting.objects.update_or_create(
                user_id=user_id,
                defaults={
                    'date_range': date_range,
                    'email_reports': email_reports,
                    'report_time': report_time,
                    'timezone': timezone,
                    'language': language,
                }
            )

            return redirect('/settings/')

        return JsonResponse({'error': 'Invalid request method'}, status=400)
    else:
        return redirect('/error/page/')


# --------------------------------
# Account Views
# --------------------------------

def account_view(request):
    """
    Displays user's account information.
    """
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    user_id = user_data.id
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]
    new_user_status = 'false'

    navbar_partial = get_navbar_partial(user_authenticated, new_user_status, roles)

    if 'user' in roles:
        try:
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
                'navbar_partial': navbar_partial,
            }

        except AccountInformation.DoesNotExist:
            context = {
                'title': 'Briefly - Add Account Information',
                'user_authenticated': True,
                'user_data': {
                    'id': user_data.id,
                    'email': user_data.email,
                },
                'error': 'Account information for user not found.',
                'navbar_partial': navbar_partial,
            }

        return render(request, 'account.html', context)
    else:
        return redirect('/error/page/')


@csrf_exempt
def account_changed(request):
    """
    Handles updating user account information.
    """
    # This view redirects, so no navbar needed
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    user_id = user_data.id
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    if 'user' in roles:
        if request.method == "POST":
            full_name = request.POST.get('full_name')
            position = request.POST.get('position')
            company = request.POST.get('company')
            report_email = request.POST.get('report_email')
            phonenr = request.POST.get('phonenr')

            AccountInformation.objects.update_or_create(
                user_id=user_id,
                defaults={
                    'full_name': full_name,
                    'position': position,
                    'company': company,
                    'report_email': report_email,
                    'phonenr': phonenr
                }
            )

            return redirect('/account/')

        return JsonResponse({'error': 'Invalid request method'}, status=400)
    else:
        return redirect('/error/page/')


# --------------------------------
# Search Settings / News Views
# --------------------------------

@csrf_exempt
def modify_search_settings(request):
    """
    Handles creating or updating search settings and saving a PreviousSearch record.
    """
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    roles = []
    new_user_status = 'false'
    user_id = user_data.id

    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]
    navbar_partial = get_navbar_partial(user_authenticated, new_user_status, roles)

    if 'user' in roles:
        placeholders = {
            'keywords': '',
            'publishers': '',
            'date_range': 'anytime',
            'description': '',
        }
        try:
            search_settings = SearchSetting.objects.get(user_id=user_id)
            placeholders.update({
                'keywords': search_settings.keywords or '',
                'publishers': search_settings.publishers or '',
                'date_range': search_settings.frequency or 'anytime',
                'description': search_settings.search_description or '',
            })
        except SearchSetting.DoesNotExist:
            search_settings = None

        if request.method == 'POST':
            keywords = request.POST.get('keywords')
            publishers = request.POST.get('publishers')
            date_range = request.POST.get('date-range')
            description = request.POST.get('description')

            search_settings, created = SearchSetting.objects.update_or_create(
                user_id=user_id,
                defaults={
                    'keywords': keywords,
                    'publishers': publishers,
                    'frequency': date_range,
                    'search_description': description
                }
            )

            PreviousSearch.objects.create(
                user_id=user_id,
                search_setting=search_settings,
                keyword=keywords,
                search_description=description,
            )

            return redirect('/')

        context = {
            'placeholders': placeholders,
            'navbar_partial': navbar_partial,
        }

        return render(request, 'main_page.html', context)
    else:
        return redirect('/error/page/')


# Custom API for news access
async def get_news(request):
    """
    Asynchronously fetches news articles based on keywords, time period, and publishers.
    Returns JSON only, so no navbar context needed.
    """
    user_data = get_access_token(request)
    user_id = user_data.id
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    if 'api' in roles:
        if request.method == "GET":
            print("Request GET parameters:", request.GET)  # Debugging
            keywords = request.GET.get('keywords', '').strip()
            period = request.GET.get('period', '1')
            publishers = request.GET.getlist('publishers', [])

            print(f"Extracted keywords: {keywords}, period: {period}, publishers: {publishers}")

            if not keywords:
                return JsonResponse({'error': 'Keywords are required'}, status=400)

            if period not in ["1", "2", "3", "4", "5"]:
                return JsonResponse({'error': 'Invalid time period selected'}, status=400)

            try:
                articles = await search_news(keywords, get_period_param(period), publishers)
                return JsonResponse({'articles': articles}, safe=False)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'error': 'Invalid request method'}, status=400)

    # Fallback if the user doesn't have 'api' role
    return JsonResponse({'error': 'Not authorized'}, status=403)