import json
from datetime import time
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .supabase_client import supabase
from .helper_functions import get_access_token
from .models import Setting, SearchSetting, PreviousSearch, Summary, UserRole, AccountInformation, ScheduledSearch
from django.views.decorators.csrf import csrf_exempt
import pytz
from .get_news import search_news, get_period_param


# Landing page of the website
def landing_page(request):
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

    if 'user' in roles:
        # Retrieve Search Settings for Placeholders
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
            # If no settings exist, use defaults
            pass

        if not settings_exist or not account_info_exist:
            context = {
                'title': 'Briefly - Home',
                'user_authenticated': user_authenticated,
                'user': user_data,
                'timezones': pytz.all_timezones,
                'new_user': 'true'
            }
            return render(request, 'main_page_new_user.html', context)

        # Render the main page if everything exists
        context = {
            'title': 'Briefly - Home',
            'user_authenticated': user_authenticated,
            'user': user_data,
            'placeholders': placeholders,
            'roles': roles
        }
        return render(request, 'main_page.html', context)
    else:
        # Redirect to logout or an appropriate error page
        return redirect('/error/page/')

@csrf_exempt
def finalise_new_user(request):
    # Retrieve the access token and user data
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



def  error_page(request):
    return render(request, '404.html')


# Login page logic
def login_view(request):
    context = {
        'title': 'Briefly - Login',
        'error': None,
    }

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
                context['error'] = 'Invalid email or password'
        except Exception as e:
            # Add the error message to context for frontend
            context['error'] = str(e)

    return render(request, 'main_page.html', context)


# Logout User
def logout_view(request):
    if request.method == 'GET':
        request.session.flush()

    context = {
        'title': 'Briefly - Login',
    }

    return render(request, 'main_page.html', context)


# Retrieve User Settings
def settings_view(request):
    # Retrieve the access token and user data
    user_authenticated, user_data = get_access_token(request)
    user_id = user_data.id

    if not user_authenticated or not user_data:
        return redirect('/login/')

    # Fetch the user's roles
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    if 'user' in roles:
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
    else:
        # Redirect to logout or an appropriate error page
        return redirect('/error/page/')


@csrf_exempt
def settings_changed(request):
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    user_id = user_data.id
    # Fetch the user's roles
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    if 'user' in roles:
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
    else:
        # Redirect to logout or an appropriate error page
        return redirect('/error/page/')



def account_view(request):
    # Retrieve the access token and user data
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')


    user_id = user_data.id
    # Fetch the user's roles
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    if 'user' in roles:
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
    else:
        # Redirect to logout or an appropriate error page
        return redirect('/error/page/')

@csrf_exempt
def account_changed(request):
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')


    user_id = user_data.id
    # Fetch the user's roles
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    if 'user' in roles:
        if request.method == "POST":
            # Retrieve the form data
            full_name = request.POST.get('full_name')
            position = request.POST.get('position')
            company = request.POST.get('company')
            report_email = request.POST.get('report_email')
            phonenr = request.POST.get('phonenr')

            # Get or create the user's account settings
            user_id = user_data.id
            account_information, created = AccountInformation.objects.update_or_create(
                user_id=user_id,
                defaults={
                    'full_name': full_name,
                    'position': position,
                    'company': company,
                    'report_email': report_email,
                    'phonenr': phonenr
                }
            )

            context = {
                'updated_account_information': account_information,
                'created': created
            }

            return redirect('/account/', context)

        return JsonResponse({'error': 'Invalid request method'}, status=400)
    else:
        # Redirect to logout or an appropriate error page
        return redirect('/error/page/')

@csrf_exempt
def modify_search_settings(request):
    user_authenticated, user_data = get_access_token(request)

    if not user_authenticated or not user_data:
        return redirect('/login/')

    user_id = user_data.id

    # Initialize placeholders with defaults
    placeholders = {
        'keywords': '',
        'publishers': '',
        'date_range': 'anytime',
        'description': '',
    }

    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    if 'user' in roles:
        try:
            # Retrieve existing search settings
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
            # Retrieve Data from the form
            keywords = request.POST.get('keywords')
            publishers = request.POST.get('publishers')
            date_range = request.POST.get('date-range')
            description = request.POST.get('description')

            # Update or create the user's search settings
            search_settings, created = SearchSetting.objects.update_or_create(
                user_id=user_id,
                defaults={
                    'keywords': keywords,
                    'publishers': publishers,
                    'frequency': date_range,
                    'search_description': description
                }
            )

            # Create a new previous search referencing the updated search setting
            PreviousSearch.objects.create(
                user_id=user_id,
                search_setting=search_settings,
                keyword=keywords,
                search_description=description,
            )

            return redirect('/')

        context = {
            'placeholders': placeholders,
        }

        return render(request, 'main_page.html', context)
    else:
        # Redirect to logout or an appropriate error page
        return redirect('/error/page/')


# Custom API for news access
async def get_news(request):
    user_data = get_access_token(request)
    user_id = user_data.id
    user_roles = UserRole.objects.filter(user_id=user_id).select_related('role')
    roles = [user_role.role.name for user_role in user_roles]

    if 'api' in roles:
        if request.method == "GET":
            print("Request GET parameters:", request.GET)  # Debugging
            keywords = request.GET.get('keywords', '').strip()  # Ensure whitespace is trimmed
            period = request.GET.get('period', '1')  # Default to "Anytime"
            publishers = request.GET.getlist('publishers', [])

            print(f"Extracted keywords: {keywords}, period: {period}, publishers: {publishers}")  # Debugging

            if not keywords:
                return JsonResponse({'error': 'Keywords are required'}, status=400)

            if period not in ["1", "2", "3", "4", "5"]:
                return JsonResponse({'error': 'Invalid time period selected'}, status=400)

            try:
                # Await the result of the async function
                articles = await search_news(keywords, get_period_param(period), publishers)
                return JsonResponse({'articles': articles}, safe=False)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'error': 'Invalid request method'}, status=400)