import json
import datetime
import csv
from datetime import time
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pytz
from django.core.paginator import Paginator

from .supabase_client import supabase
from .helper_functions import get_access_token, get_navbar_partial, sanitize, wants_json_response
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


# --------------------------------
# Public / Landing Views
# --------------------------------

def landing_page(request):
    """
    Displays the landing/home page for authenticated users or redirects to login if not authenticated.
    """
    try:
        user_authenticated, user_data = get_access_token(request)

        # Redirect or JSON error if user not authenticated
        if not user_authenticated:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authenticated'}, status=401)
            return redirect('/login')

        user_id = user_data.id
        settings_exist = Setting.objects.filter(user_id=user_id).exists()
        account_info_exist = AccountInformation.objects.filter(user_id=user_id).exists()

        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

        new_user_status = 'true' if (not settings_exist or not account_info_exist) else 'false'
        navbar_partial = get_navbar_partial(user_authenticated, new_user_status, roles)

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
            if wants_json_response(request):
                return JsonResponse({'error': 'Role not allowed'}, status=403)
            return redirect('/error/page/')
    except Exception as e:
        # In case there's a higher-level error
        return JsonResponse({'error': str(e)}, status=500)


def error_page(request):
    """
    Renders a generic error (404) page.
    """
    try:
        user_authenticated, user_data = get_access_token(request)
        new_user_status = 'false'
        roles = []

        if user_data:
            user_id = user_data.id
            user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
            roles = [user_role.role.name for user_role in user_roles]

        navbar_partial = get_navbar_partial(user_authenticated, new_user_status, roles)
        return render(request, '404.html', {'navbar_partial': navbar_partial})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --------------------------------
# Authentication Views
# --------------------------------

@csrf_exempt
def login_view(request):
    """
    Handles user login using Supabase authentication.
    Expects JSON data on POST (email, password) and returns JSON responses for errors or success.
    """
    try:
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
            'navbar_partial': navbar_partial,
        }
        # If GET, just render the login form (no error context).
        if request.method == 'GET':
            return render(request, 'loginForm.html', context)

        # If POST, parse JSON from request.body instead of request.POST
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                # If the body isn't valid JSON
                return JsonResponse({'error': 'Invalid JSON body'}, status=400)

            email = sanitize(data.get('email'))
            password = sanitize(data.get('password'))

            if not email or not password:
                return JsonResponse({'error': 'Email and password are required'}, status=400)

            # Attempt Supabase authentication
            try:
                response = supabase.auth.sign_in_with_password({"email": email, "password": password})

                if response.user:
                    # If successful, store session info
                    request.session['access_token'] = response.session.access_token
                    request.session['user'] = {
                        "id": response.user.id,
                        "email": response.user.email
                    }

                    # Check roles to know where to redirect
                    user_id = response.user.id
                    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
                    roles = [user_role.role.name for user_role in user_roles]

                    # Return JSON success, plus a recommended redirect
                    if 'admin' in roles:
                        return JsonResponse({'success': True, 'redirect_url': '/custom-admin/dashboard/'}, status=200)
                    else:
                        return JsonResponse({'success': True, 'redirect_url': '/'}, status=200)

                else:
                    # Invalid credentials
                    return JsonResponse({'error': 'Invalid email or password'}, status=400)

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        # If neither GET nor POST, return an error
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def logout_view(request):
    """
    Logs out the current user by clearing the session.
    """
    try:
        if request.method == 'GET':
            request.session.flush()
        return redirect('/login/')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def finalise_new_user(request):
    """
    Finalizes registration details for a new user (e.g., personal and account info).
    """
    try:
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authenticated'}, status=401)
            return redirect('/login/')

        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

        if 'user' in roles:
            if request.method == 'POST':
                full_name = sanitize(request.POST.get('full_name'))
                position = sanitize(request.POST.get('position'))
                report_email = sanitize(request.POST.get('report_email'))
                phonenr = sanitize(request.POST.get('phonenr'))
                target_audience = sanitize(request.POST.get('target_audience'))
                content_sentiment = sanitize(request.POST.get('content_sentiment'))
                company = sanitize(request.POST.get('company'))
                industry = sanitize(request.POST.get('industry'))
                company_brief = sanitize(request.POST.get('company_brief'))
                recent_ventures = sanitize(request.POST.get('recent_ventures'))
                account_version = "standard"

                email_reports = sanitize(request.POST.get('email_reports'))
                timezone = sanitize(request.POST.get('timezone'))

                try:
                    Setting.objects.update_or_create(
                        user_id=user_id,
                        defaults={
                            'email_reports': email_reports,
                            'timezone': timezone,
                        }
                    )

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
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)

            return redirect('/')
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --------------------------------
# Admin Views
# --------------------------------

@csrf_exempt
def admin_dashboard(request):
    """
    Displays the admin dashboard with a list of users and their account information.
    """
    try:
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authenticated'}, status=401)
            return redirect('/login/')

        new_user_status = 'false'
        roles = []
        if user_data:
            user_id = user_data.id
            user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
            roles = [user_role.role.name for user_role in user_roles]

        navbar_partial = get_navbar_partial(user_authenticated, new_user_status, roles)

        if request.method == 'GET':
            if 'admin' in roles:
                users = User.objects.all()
                user_roles = UserRole.objects.filter(role_id=2)
                user_ids_with_role_user = {ur.user_id for ur in user_roles}
                users_with_role_user = [u for u in users if u.id in user_ids_with_role_user]

                account_info_list = AccountInformation.objects.filter(user_id__in=user_ids_with_role_user)
                total_users = 0
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
                        total_users += 1
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
                    'total_users': total_users,
                }
                return render(request, 'admin_dashboard.html', context)
            else:
                if wants_json_response(request):
                    return JsonResponse({'error': 'Not authorized'}, status=403)
                return redirect('/error/page/')

        if request.method == 'POST':
            if 'admin' in roles:
                try:
                    data = json.loads(request.body)
                    user_id_to_update = data.get('user_id')
                    new_account_version = sanitize(data.get('account_version'))

                    account_information_obj = AccountInformation.objects.get(user_id=user_id_to_update)
                    account_information_obj.account_version = new_account_version
                    account_information_obj.save()

                    return JsonResponse({
                        'message': 'Account version updated successfully',
                        'account_version': new_account_version,
                        'user_id': user_id_to_update
                    }, status=200)
                except AccountInformation.DoesNotExist:
                    return JsonResponse({'error': 'Account not found'}, status=404)
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)
            else:
                return JsonResponse({'error': 'Not authorized'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Convert all client data to CSV
@csrf_exempt
def admin_dashboard_csv(request):
    """
    Exports CSV of user account info for admin.
    """
    try:
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authenticated'}, status=401)
            return redirect('/login/')

        roles = []
        if user_data:
            user_id = user_data.id
            user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
            roles = [user_role.role.name for user_role in user_roles]

        # Only allow GET for CSV export (or POST if you prefer)
        if request.method == 'GET':
            if 'admin' in roles:
                # Collect all relevant account info
                users = User.objects.all()
                user_roles = UserRole.objects.filter(role_id=2)
                user_ids_with_role_user = {ur.user_id for ur in user_roles}
                users_with_role_user = [u for u in users if u.id in user_ids_with_role_user]
                account_info_list = AccountInformation.objects.filter(user_id__in=user_ids_with_role_user)

                # Create a lookup dict from user_id -> account_info
                account_info_dict = {info.user_id: info for info in account_info_list}

                # Set up the HttpResponse with correct headers
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                response = HttpResponse(content_type="text/csv")
                response['Content-Disposition'] = f'attachment; filename="exported_client_data_{date_str}.csv"'

                # Create a CSV writer object
                writer = csv.writer(response)

                # Write a header row
                writer.writerow([
                    "Full Name",
                    "Position",
                    "Company",
                    "Report Email",
                    "Phone Number",
                    "Target Audience",
                    "Industry",
                    "Content Sentiment",
                    "Company Brief",
                    "Recent Ventures",
                    "Account Version"
                ])

                # Write one row per user
                for user in users_with_role_user:
                    info = account_info_dict.get(user.id)
                    if info:
                        writer.writerow([
                            info.full_name,
                            info.position,
                            info.company,
                            info.report_email,
                            info.phonenr,
                            info.target_audience,
                            info.industry,
                            info.content_sentiment,
                            info.company_brief,
                            info.recent_ventures,
                            info.account_version
                        ])

                return response
            else:
                if wants_json_response(request):
                    return JsonResponse({'error': 'Not authorized'}, status=403)
                return redirect('/error/page/')
        else:
            return JsonResponse({'error': 'Invalid request method'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# --------------------------------
# User Settings Views
# --------------------------------

def settings_view(request):
    """
    Fetches and displays the user's settings for editing.
    """
    try:
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authenticated'}, status=401)
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
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authorized'}, status=403)
            return redirect('/error/page/')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def settings_changed(request):
    """
    Handles updating user settings (date range, email reports, report time, timezone, language).
    """
    try:
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authenticated'}, status=401)
            return redirect('/login/')

        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

        if 'user' in roles:
            if request.method == "POST":
                date_range = sanitize(request.POST.get('date_range'))
                email_reports_str = sanitize(request.POST.get('email_reports'))
                email_reports = (email_reports_str == 'True')

                report_time_raw = sanitize(request.POST.get('report_time'))
                timezone_val = sanitize(request.POST.get('timezone'))
                language_val = sanitize(request.POST.get('language'))

                try:
                    if report_time_raw:
                        hours, minutes, seconds = map(int, report_time_raw.split(":"))
                        report_time_obj = time(hour=hours, minute=minutes, second=seconds)
                    else:
                        report_time_obj = None
                except ValueError:
                    return JsonResponse({'error': 'Invalid time format. Use HH:MM:SS.'}, status=400)

                try:
                    Setting.objects.update_or_create(
                        user_id=user_id,
                        defaults={
                            'date_range': date_range,
                            'email_reports': email_reports,
                            'report_time': report_time_obj,
                            'timezone': timezone_val,
                            'language': language_val,
                        }
                    )
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)

                return redirect('/settings/')

            return JsonResponse({'error': 'Invalid request method'}, status=400)
        else:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authorized'}, status=403)
            return redirect('/error/page/')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --------------------------------
# Account Views
# --------------------------------

def account_view(request):
    """
    Displays user's account information.
    """
    try:
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authenticated'}, status=401)
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
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authorized'}, status=403)
            return redirect('/error/page/')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def account_changed(request):
    """
    Handles updating user account information.
    """
    try:
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authenticated'}, status=401)
            return redirect('/login/')

        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

        if 'user' in roles:
            if request.method == "POST":
                full_name = sanitize(request.POST.get('full_name'))
                position = sanitize(request.POST.get('position'))
                company = sanitize(request.POST.get('company'))
                report_email = sanitize(request.POST.get('report_email'))
                phonenr = sanitize(request.POST.get('phonenr'))

                try:
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
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)

                return redirect('/account/')
            return JsonResponse({'error': 'Invalid request method'}, status=400)
        else:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authorized'}, status=403)
            return redirect('/error/page/')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --------------------------------
# Search Settings / News Views
# --------------------------------

@csrf_exempt
def modify_search_settings(request):
    """
    Handles creating or updating search settings and saving a PreviousSearch record.
    """
    try:
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authenticated'}, status=401)
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
                keywords = sanitize(request.POST.get('keywords'))
                publishers = sanitize(request.POST.get('publishers'))
                date_range = sanitize(request.POST.get('date-range'))
                description = sanitize(request.POST.get('description'))

                try:
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
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)

                return redirect('/')
            context = {
                'placeholders': placeholders,
                'navbar_partial': navbar_partial,
            }
            return render(request, 'main_page.html', context)
        else:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authorized'}, status=403)
            return redirect('/error/page/')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


async def get_news(request):
    """
    Asynchronously fetches news articles based on keywords, time period, and publishers.
    Returns JSON only, so no navbar context needed.
    """
    try:
        user_data = get_access_token(request)
        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

        if 'api' in roles:
            if request.method == "GET":
                print("Request GET parameters:", request.GET)  # Debugging
                keywords = sanitize(request.GET.get('keywords', '')).strip()
                period = sanitize(request.GET.get('period', '1'))
                publishers = [sanitize(pub) for pub in request.GET.getlist('publishers', [])]

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

        return JsonResponse({'error': 'Not authorized'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)