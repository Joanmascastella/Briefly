import json
import datetime
import csv
from django.conf import settings
from django.utils.translation import gettext as _  # For language handling
from datetime import time
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
import pytz
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .supabase_client import supabase
from .helper_functions import get_access_token, sanitize, wants_json_response, validate_date_range
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
from .fetch_news import search_news
import csv
import os
import logging

logger = logging.getLogger(__name__)

# --------------------------------
# Public / Landing Views
# --------------------------------
def landing_page(request):
    try:
        if request.method == 'GET':
            user_authenticated, user_data = get_access_token(request)

            if not user_authenticated:
                if wants_json_response(request):
                    return JsonResponse({'error': 'Not authenticated'}, status=401)
                return redirect('/login')

            user_id = user_data.id
            account_info_exist = AccountInformation.objects.filter(user_id=user_id).exists()
            account_info = AccountInformation.objects.filter(user_id=user_id).first()
            user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
            roles = [user_role.role.name for user_role in user_roles]

            # Fetch previous searches for the user
            previous_searches = PreviousSearch.objects.filter(user_id=user_id).order_by('-created_at')

            # Pagination logic
            page = request.GET.get('page', 1)
            paginator = Paginator(previous_searches, 5)  # Show 5 searches per page

            try:
                paginated_searches = paginator.page(page)
            except PageNotAnInteger:
                paginated_searches = paginator.page(1)
            except EmptyPage:
                paginated_searches = paginator.page(paginator.num_pages)

            previous_searches_data = [
                {
                    'search_description': search.search_description,
                    'created_at': search.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'csv_file_path': search.csv_file_path
                }
                for search in paginated_searches
            ]

            if 'user' in roles:
                if not account_info_exist:
                    context = {
                        'title': 'Briefly - Home',
                        'user_authenticated': user_authenticated,
                        'user': user_data,
                        'timezones': pytz.all_timezones,
                        'new_user': 'true',
                        'navbar_partial': 'partials/authenticated_navbar_new_user.html',
                        'LANGUAGES': settings.LANGUAGES,
                    }
                    return render(request, 'main_page_new_user.html', context)

                context = {
                    'title': 'Briefly - Home',
                    'user_authenticated': user_authenticated,
                    'user': user_data,
                    'roles': roles,
                    'navbar_partial': 'partials/authenticated_navbar.html',
                    'LANGUAGES': settings.LANGUAGES,
                    'account_info': {
                        'full_name': account_info.full_name,
                    },
                    'previous_searches': previous_searches_data,
                    'paginator': paginator,
                    'current_page': paginated_searches.number,
                }
                return render(request, 'main_page.html', context)

            elif 'admin' in roles:
                return redirect('/custom-admin/dashboard/')
            else:
                if wants_json_response(request):
                    return JsonResponse({'error': 'Role not allowed'}, status=403)
                return redirect('/error/page/')
    except Exception as e:
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

        return render(request, '404.html')
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --------------------------------
# Authentication Views
# --------------------------------
@csrf_protect
def login_view(request):
    try:
        if request.method == 'GET':
            return render(request, 'loginForm.html', {
                'title': 'Briefly - Login',
                'navbar_partial': 'partials/not_authenticated_navbar.html'
            })

        elif request.method == 'POST':
            # Handle POST login
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON body'}, status=400)

            email = sanitize(data.get('email'))
            password = sanitize(data.get('password'))

            if not email or not password:
                return JsonResponse({'error': 'Email and password are required'}, status=400)

            # Attempt authentication with Supabase
            try:
                response = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if response.user:
                    # Save session
                    request.session['access_token'] = response.session.access_token
                    request.session['user'] = {
                        "id": response.user.id,
                        "email": response.user.email
                    }
                    return JsonResponse({'success': True, 'redirect_url': '/home/'}, status=200)

                return JsonResponse({'error': 'Invalid email or password'}, status=400)
            except Exception as e:
                return JsonResponse({'error': f'Authentication failed: {str(e)}'}, status=500)

        return JsonResponse({'error': 'Invalid request method'}, status=405)
    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)


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



@csrf_protect
def finalise_new_user(request):
    """
    Finalizes registration details for a new user (e.g., personal and account info).
    """
    try:
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            return JsonResponse({'error': 'Not authenticated'}, status=401)

        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

        if 'user' in roles:
            if request.method == 'POST':
                if request.content_type == 'application/json':
                    try:
                        payload = json.loads(request.body)
                    except json.JSONDecodeError:
                        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

                    # Extract and sanitize JSON fields
                    full_name = sanitize(payload.get('full_name'))
                    position = sanitize(payload.get('position'))
                    # report_email = sanitize(payload.get('report_email'))
                    # phonenr = sanitize(payload.get('phonenr'))
                    # target_audience = sanitize(payload.get('target_audience'))
                    # content_sentiment = sanitize(payload.get('content_sentiment'))
                    company = sanitize(payload.get('company'))
                    industry = sanitize(payload.get('industry'))
                    company_brief = sanitize(payload.get('company_brief'))
                    # recent_ventures = sanitize(payload.get('recent_ventures'))
                    account_version = "standard"
                    # email_reports = sanitize(payload.get('email_reports'))
                    # timezone = sanitize(payload.get('timezone'))

                    try:
                        # # Update or create user settings and account information
                        # Setting.objects.update_or_create(
                        #     user_id=user_id,
                        #     defaults={
                        #         'email_reports': email_reports,
                        #         'timezone': timezone,
                        #     }
                        # )

                        AccountInformation.objects.update_or_create(
                            user_id=user_id,
                            defaults={
                                "full_name": full_name,
                                "position": position,
                                # "phonenr": phonenr,
                                # "target_audience": target_audience,
                                # "content_sentiment": content_sentiment,
                                "company": company,
                                # "report_email": report_email,
                                "industry": industry,
                                "company_brief": company_brief,
                                # "recent_ventures": recent_ventures,
                                "account_version": account_version,
                            }
                        )

                        return JsonResponse({'message': 'Account setup successful'}, status=200)
                    except Exception as e:
                        return JsonResponse({'error': str(e)}, status=500)
                else:
                    return JsonResponse({'error': 'Unsupported content type'}, status=400)

            return JsonResponse({'error': 'Invalid request method'}, status=405)
        return JsonResponse({'error': 'Unauthorized role'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# --------------------------------
# Admin Views
# --------------------------------
@csrf_protect
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

        roles = []
        if user_data:
            user_id = user_data.id
            user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
            roles = [user_role.role.name for user_role in user_roles]

        # Handle GET request
        if request.method == 'GET':
            if 'admin' in roles:
                try:
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
                                # 'report_email': account_info.report_email,
                                # 'phonenr': account_info.phonenr,
                                # 'target_audience': account_info.target_audience,
                                'industry': account_info.industry,
                                # 'content_sentiment': account_info.content_sentiment,
                                'company_brief': account_info.company_brief,
                                # 'recent_ventures': account_info.recent_ventures,
                                # 'account_version': account_info.account_version,
                            })
                            total_users += 1

                    paginator = Paginator(users_with_account_info, 5)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)

                    return render(request, 'admin_dashboard.html', {
                        'title': 'Briefly - Admin Dashboard',
                        'navbar_partial': 'partials/authenticated_navbar_admin.html',
                        'user_authenticated': True,
                        'user_data': {
                            'id': user_data.id,
                            'email': user_data.email,
                        },
                        'roles': roles,
                        'page_obj': page_obj,
                        'is_paginated': page_obj.has_other_pages(),
                        'paginator': paginator,
                        'total_users': total_users,
                        'LANGUAGES': settings.LANGUAGES,
                    })
                except Exception as e:
                    return JsonResponse({'error': f'Failed to load dashboard: {str(e)}'}, status=500)

            return JsonResponse({'error': 'Not authorized'}, status=403)

        # Handle POST request
        elif request.method == 'POST':
            if 'admin' in roles:
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Invalid JSON body'}, status=400)

                user_id_to_update = sanitize(data.get('user_id'))
                new_account_version = sanitize(data.get('account_version'))

                if not user_id_to_update or not new_account_version:
                    return JsonResponse({'error': 'User ID and account version are required'}, status=400)

                try:
                    account_information_obj = AccountInformation.objects.get(user_id=user_id_to_update)
                    account_information_obj.account_version = new_account_version
                    account_information_obj.save()

                    return JsonResponse({
                        'success': True,
                        'message': 'Account version updated successfully',
                        'user_id': user_id_to_update,
                        'account_version': new_account_version,
                    }, status=200)
                except AccountInformation.DoesNotExist:
                    return JsonResponse({'error': 'Account not found'}, status=404)
                except Exception as e:
                    return JsonResponse({'error': f'Failed to update account: {str(e)}'}, status=500)

            return JsonResponse({'error': 'Not authorized'}, status=403)

        # Invalid request method
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    except Exception as e:
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

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
                    # "Report Email",
                    # "Phone Number",
                    # "Target Audience",
                    "Industry",
                    # "Content Sentiment",
                    "Company Brief",
                    # "Recent Ventures",
                    # "Account Version"
                ])

                # Write one row per user
                for user in users_with_role_user:
                    info = account_info_dict.get(user.id)
                    if info:
                        writer.writerow([
                            info.full_name,
                            info.position,
                            info.company,
                            # info.report_email,
                            # info.phonenr,
                            # info.target_audience,
                            info.industry,
                            # info.content_sentiment,
                            info.company_brief,
                            # info.recent_ventures,
                            # info.account_version
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
def get_settings_view(request):
    """
    GET: Fetch and display the user's settings + account info.
    """
    try:
        # 1) Authenticate user
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            if wants_json_response(request):
                return JsonResponse({'error': 'Not authenticated'}, status=401)
            return redirect('/login/')

        # 2) Gather user roles
        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]
        new_user_status = 'false'

        # 3) Handle GET
        if request.method == 'GET':
            if 'user' in roles:
                try:
                    # Fetch user settings & account information
                    # user_settings = Setting.objects.get(user_id=user_id)
                    account_information = AccountInformation.objects.get(user_id=user_id)

                    context = {
                        'title': 'Briefly - Settings',
                        'user_authenticated': True,
                        'user_data': {
                            'id': user_data.id,
                            'email': user_data.email,
                            # 'settings': {
                            #     'email_reports': user_settings.email_reports,
                            #     'timezone': user_settings.timezone,
                            # },
                            'account_info': {
                                'full_name': account_information.full_name,
                                'position': account_information.position,
                                # 'report_email': account_information.report_email,
                                # 'phonenr': account_information.phonenr,
                                # 'target_audience': account_information.target_audience,
                                # 'content_sentiment': account_information.content_sentiment,
                                'company': account_information.company,
                                'industry': account_information.industry,
                                'company_brief': account_information.company_brief,
                                # 'recent_ventures': account_information.recent_ventures,
                            },
                        },
                        'timezones': pytz.all_timezones,
                        'navbar_partial': 'partials/authenticated_navbar.html',
                        'error': None,
                        'LANGUAGES': settings.LANGUAGES,
                    }
                    if wants_json_response(request):
                        return JsonResponse(context, status=200)
                    return render(request, 'settings.html', context)

                except Setting.DoesNotExist:
                    if wants_json_response(request):
                        return JsonResponse({'error': 'User settings not found'}, status=404)
                    return redirect('/error/page/')
                except AccountInformation.DoesNotExist:
                    if wants_json_response(request):
                        return JsonResponse({'error': 'Account information not found'}, status=404)
                    return redirect('/error/page/')
            else:
                # Not a "user" role => 403
                if wants_json_response(request):
                    return JsonResponse({'error': 'Not authorized'}, status=403)
                return redirect('/error/page/')
        else:
            # Any other method => 405
            if wants_json_response(request):
                return JsonResponse({'error': 'Method not allowed'}, status=405)
            return redirect('/error/page/')

    except Exception as e:
        if wants_json_response(request):
            return JsonResponse({'error': 'Internal server error', 'details': str(e)}, status=500)
        return redirect('/error/page/')


# @csrf_protect
# def settings_modify_view(request):
#     """
#     POST: Update the user's settings (email reports, timezone).
#     """
#     try:
#         # 1) Authenticate user
#         user_authenticated, user_data = get_access_token(request)
#         if not user_authenticated or not user_data:
#             return JsonResponse({'error': 'Not authenticated'}, status=401)
#
#         user_id = user_data.id
#         user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
#         roles = [user_role.role.name for user_role in user_roles]
#
#         if request.method == 'POST':
#             if 'user' in roles:
#                 try:
#                     data = json.loads(request.body)
#
#                     email_reports = sanitize(data.get('emailReports'))
#                     timezone_value = sanitize(data.get('timezone'))
#
#                     # Update user settings
#                     try:
#                         user_settings = Setting.objects.get(user_id=user_id)
#                         if email_reports is not None:
#                             user_settings.email_reports = email_reports
#                         if timezone_value is not None:
#                             user_settings.timezone = timezone_value
#                         user_settings.save()
#
#                         return JsonResponse({'message': 'Settings updated successfully'}, status=200)
#
#                     except Setting.DoesNotExist:
#                         return JsonResponse({'error': 'User settings not found'}, status=404)
#                 except json.JSONDecodeError:
#                     return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
#                 except Exception as e:
#                     return JsonResponse({'error': str(e)}, status=500)
#             else:
#                 return JsonResponse({'error': 'Not authorized'}, status=403)
#         else:
#             return JsonResponse({'error': 'Method not allowed'}, status=405)
#
#     except Exception as e:
#         return JsonResponse({'error': 'Internal server error', 'details': str(e)}, status=500)


@csrf_protect
def account_modify_view(request):
    """
    POST: Update the user's account information (full name, phone, etc.).
    """
    try:
        # 1) Authenticate user
        user_authenticated, user_data = get_access_token(request)
        if not user_authenticated or not user_data:
            return JsonResponse({'error': 'Not authenticated'}, status=401)

        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

        if request.method == 'POST':
            if 'user' in roles:
                try:
                    data = json.loads(request.body)

                    try:
                        account_info = AccountInformation.objects.get(user_id=user_id)

                        if 'fullName' in data:
                            account_info.full_name = sanitize(data['fullName'])
                        if 'position' in data:
                            account_info.position = sanitize(data['position'])
                        # if 'reportEmail' in data:
                        #     account_info.report_email = sanitize(data['reportEmail'])
                        # if 'phonenr' in data:
                        #     account_info.phonenr = sanitize(data['phonenr'])
                        # if 'targetAudience' in data:
                        #     account_info.target_audience = sanitize(data['targetAudience'])
                        # if 'contentSentiment' in data:
                        #     account_info.content_sentiment = sanitize(data['contentSentiment'])
                        if 'company' in data:
                            account_info.company = sanitize(data['company'])
                        if 'industry' in data:
                            account_info.industry = sanitize(data['industry'])
                        if 'companyBrief' in data:
                            account_info.company_brief = sanitize(data['companyBrief'])
                        # if 'recentVentures' in data:
                        #     account_info.recent_ventures = sanitize(data['recentVentures'])

                        account_info.save()

                        return JsonResponse({'message': 'Account information updated successfully'}, status=200)

                    except AccountInformation.DoesNotExist:
                        return JsonResponse({'error': 'Account information not found'}, status=404)
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
                except Exception as e:
                    return JsonResponse({'error': str(e)}, status=500)
            else:
                return JsonResponse({'error': 'Not authorized'}, status=403)
        else:
            return JsonResponse({'error': 'Method not allowed'}, status=405)

    except Exception as e:
        return JsonResponse({'error': 'Internal server error', 'details': str(e)}, status=500)


# --------------------------------
# Search Views
# --------------------------------
@csrf_exempt
def search_view(request, language=None):
    try:
        user_authenticated, user_data = get_access_token(request)
        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

        if request.method == 'GET':
            if not user_authenticated:
                if wants_json_response(request):
                    return JsonResponse({'error': _('Not authenticated')}, status=401)
                return redirect('/login')

            if 'user' in roles:
                context = {
                    'title': _('Briefly - Search'),
                    'user_authenticated': user_authenticated,
                    'user': user_data,
                    'roles': roles,
                    'navbar_partial': 'partials/authenticated_navbar.html',
                    'LANGUAGES': settings.LANGUAGES,
                }
                return render(request, 'search_page.html', context)
            else:
                if wants_json_response(request):
                    return JsonResponse({'error': _('Role not allowed')}, status=403)
                return redirect('/error/page/')

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def search_results(request, language=None):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_authenticated, user_data = get_access_token(request)
            user_id = user_data.id

            title_of_search = sanitize(data.get('title'))
            keywords = sanitize(data.get('keywords'))
            specific_publishers = "",
            date_range = ""

            # Save search settings
            search_settings = SearchSetting.objects.create(
                user_id=user_id,
                publishers=specific_publishers,
                frequency=date_range,
                search_description=title_of_search,
                keywords=keywords,
                type_of_search="on_demand"
            )

            # Call the new search_news function (without Playwright)
            articles = search_news(keywords)

            # Log the articles for debugging
            logger.info(f"🔍 Articles fetched: {articles}")

            # If no articles are found, return an empty response
            if not articles:
                return JsonResponse({
                    'articles': [],
                    'csv_file_path': '',
                    'error': 'No articles found for the given search parameters.'
                }, status=200)

            # Define the correct path under MEDIA_ROOT
            csv_file_name = f"search_results_{user_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
            csv_file_path = os.path.join(settings.MEDIA_ROOT, "search_results", csv_file_name)

            # Ensure directory exists
            os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)

            # Write CSV file
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=['title', 'link', 'date', 'publisher', 'image'])
                writer.writeheader()
                writer.writerows(articles)

            # Save relative path to the database
            relative_csv_path = os.path.relpath(csv_file_path, settings.MEDIA_ROOT)

            # Save search results in the database
            PreviousSearch.objects.create(
                user_id=user_id,
                search_setting_id=search_settings.id,
                keyword=keywords,
                created_at=datetime.datetime.now(),
                csv_file_path=relative_csv_path,
                search_description=title_of_search
            )

            # Return search results
            return JsonResponse({
                'articles': articles,
                'csv_file_path': f"{settings.MEDIA_URL}{relative_csv_path}"
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': _('Invalid JSON body')}, status=400)
        except Exception as e:
            logger.error(f"⚠️ Error in search_results: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': _('Invalid request method')}, status=405)


def previous_searches(request):
    try:
        user_authenticated, user_data = get_access_token(request)
        user_id = user_data.id
        user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
        roles = [user_role.role.name for user_role in user_roles]

        if not user_authenticated:
            if wants_json_response(request):
                return JsonResponse({'error': _('Not authenticated')}, status=401)
            return redirect('/login')

        if 'user' in roles:
            # Fetch all previous searches for the user
            searches = PreviousSearch.objects.filter(user_id=user_id).order_by('-created_at')

            # Check if a specific CSV file is requested
            csv_file_path = request.GET.get('csv_file_path')
            rows = None
            if csv_file_path:
                absolute_csv_path = os.path.join(settings.MEDIA_ROOT, csv_file_path)
                print(f"🔍 Checking CSV file at: {absolute_csv_path}")  # Debugging

                if os.path.exists(absolute_csv_path):
                    with open(absolute_csv_path, mode='r', encoding='utf-8') as csv_file:
                        reader = csv.DictReader(csv_file)
                        rows = list(reader)
                else:
                    print(f"❌ File not found: {absolute_csv_path}")  # Debugging
                    return JsonResponse({'error': _('Invalid or missing CSV file path')}, status=400)

            # Paginate the search details if they exist
            if rows:
                paginator = Paginator(rows, 5)  # Show 5 search details per page
                page_number = request.GET.get('page', 1)
                page_obj = paginator.get_page(page_number)
            else:
                page_obj = None

            context = {
                'title': _('Briefly - Previous Searches'),
                'user_authenticated': user_authenticated,
                'user': user_data,
                'roles': roles,
                'navbar_partial': 'partials/authenticated_navbar.html',
                'LANGUAGES': settings.LANGUAGES,
                'previous_searches': searches,
                'search_details': page_obj,  # Pass paginated search details
                'paginator': page_obj.paginator if page_obj else None,
                'current_page': page_obj.number if page_obj else None,
            }
            return render(request, 'previous_searches.html', context)
        else:
            if wants_json_response(request):
                return JsonResponse({'error': _('Role not allowed')}, status=403)
            return redirect('/error/page/')

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)