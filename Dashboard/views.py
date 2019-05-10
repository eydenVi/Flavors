from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from .forms import LoginForm, UserForm, ClientForm

# Create your views here.
def new_user(request):

    if request.method == 'POST':
        user_form = UserForm(request.POST)
        client_form = ClientForm(request.POST)
        if user_form.is_valid() and client_form.is_valid():
            user_form.save()
            client_form.save()
            return redirect('')
    else:
        user_form = UserForm()
        client_form = ClientForm()

    context = {'user_form':user_form, 'client_form':client_form}
    
    return render(request,'Dashboard/new-user-form.html',context)

def userlogin(request):

    if request.method == 'POST':
        
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )

        if user is not none:
            login(request, user)
            return redirect('')

def home(request):
    return render(request, 'Dashboard/index.html')
