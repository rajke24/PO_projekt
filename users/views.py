from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login

from .forms import TeamForm, ParticipantForm
from .models import Participant, Team
from competition.models import Configuration
from .decorators import unauthenticated_user


def no_team_slots_available(request):
    if __is_any_team_slot_available():
        return redirect('registration')
    return render(request, 'users/team_limit.html')


def registration_successful(request, team):
    return render(request, 'users/registration_success.html', context={
        'team': team, 'team_members': Participant.objects.all().filter(team=team)
    })


@unauthenticated_user
def register(request):
    if not __is_any_team_slot_available():
        return redirect('register-no-team-slots-available')
    if request.method == 'POST':
        team_members = int(request.POST['participants_spinner'])
        team_form = TeamForm(request.POST, prefix='team')
        participant_forms = [
            ParticipantForm(request.POST, prefix='participant_1'),
            ParticipantForm(request.POST, prefix='participant_2'),
            ParticipantForm(request.POST, prefix='participant_3')
        ]
        are_forms_valid = __are_forms_valid(
            team_form, participant_forms, team_members)
        if are_forms_valid:
            if __is_any_team_slot_available():
                team = __save_team(team_form)
                __save_participants(participant_forms, team_members, team)
                return registration_successful(request, team)
            else:
                return redirect('register-no-team-slots-available')
        else:
            # jeżeli któraś z form jest niepoprawna, zwracamy je z powrotem żeby wyświetliły się błędy
            # odtwarzamy na nowo formy participantów które były zdisablowane na froncie, bo inaczej będą one oznaczone jako błędnie wypełnione
            __recreate_empty_forms(participant_forms, team_members)
            return render(request, 'users/registration.html',
                          {'participants': participant_forms,
                           'team': team_form,
                           })
    else:
        team = TeamForm(prefix='team')
        participant_1 = ParticipantForm(prefix='participant_1')
        participant_2 = ParticipantForm(prefix='participant_2')
        participant_3 = ParticipantForm(prefix='participant_3')
        return render(request, 'users/registration.html',
                      {'participants': [participant_1, participant_2, participant_3],
                       'team': team})


def __are_forms_valid(team_form, participant_forms, team_members):
    if not team_form or not team_form.is_valid():
        return False
    team_members_emails = []
    for i in range(team_members):
        if not participant_forms[i] or not participant_forms[i].is_valid():
            return False
        else:
            member_email = participant_forms[i].cleaned_data['email']
            if member_email in team_members_emails:
                participant_forms[i].add_error(
                    'email', 'Ten email jest już używany przez innego członka zespołu')
                return False
            team_members_emails.append(member_email)
    return True


def __is_any_team_slot_available():
    limit = Configuration.objects.all()[0].participants_limit
    teams_total = Team.objects.all().count()
    return teams_total < limit


def __save_team(team_form):
    team_city = team_form.cleaned_data['school_city']
    team_user = User.objects.create_user(
        username=__generate_username(team_city), password=team_form.cleaned_data['password'])
    team = team_form.save(commit=False)
    group = Group.objects.get(name="team")
    team_user.groups.add(group)
    team.team_as_user = team_user
    team.save()
    return team


def __generate_username(team_city):
    team_city_formatted = __sanitize_team_city(team_city)
    index = 1
    is_username_free = False
    username = None
    while not is_username_free:
        username = "{}{}".format(team_city_formatted, index)
        is_username_free = __is_username_free(username)
        index = index + 1
    return username


def __sanitize_team_city(team_city):
    return "".join(filter(str.isalpha, team_city)).lower().replace('ł', 'l').replace('ś', 's').replace('ó', 'o').replace('ż', 'z').replace('ź', 'z').replace('ę', 'e').replace('ą', 'a').replace('ć', 'c')


def __is_username_free(username):
    return not User.objects.filter(username__exact=username).exists()


def __save_participants(participant_forms, team_members, team):
    for i in range(team_members):
        participant = participant_forms[i].save(commit=False)
        participant.team = team
        participant.save()


def __recreate_empty_forms(participant_forms, team_members):
    for i in range(team_members, 3):
        participant_forms[i] = ParticipantForm(prefix="participant_".format(i))


@unauthenticated_user
def login_page(request):
    context = {}
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        context['invalid_user'] = True
    return render(request, 'users/login.html', context)
