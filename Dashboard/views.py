from itertools import chain

import pytz
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect, reverse, render_to_response
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.http.response import HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import *
from django.views.generic import CreateView, FormView, UpdateView, TemplateView, ListView, DeleteView
from .models import Client, Restaurant, Dish, Category, Flavor, Shedule, Media, Social

# Create your views here.

''' 
------------------------------------------
Views sistema de autenticación de usuarios
------------------------------------------
'''


class NewUser(CreateView):
    model = User
    template_name = 'Dashboard/new-user-form.html'
    form_class = UserForm
    success_url = '/'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.object = None

    def get(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        detalle_cliente = ClientFormSet()
        return self.render_to_response(self.get_context_data(form=form, detalle_client_form_set=detalle_cliente))

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        client_form_set = ClientFormSet(request.POST)
        if form.is_valid() and client_form_set.is_valid():

            return self.form_valid(form, client_form_set)
        else:
            return self.form_invalid(form, client_form_set)

    def form_valid(self, form, client_form_set):
        self.object = form.save()
        self.object.set_password(form.cleaned_data['password'])
        self.object.save()
        self.object = authenticate(
            username=self.object.username, password=form.cleaned_data['password'])
        client_form_set.instance = self.object
        client_form_set.save()
        return HttpResponseRedirect(self.success_url)

    def form_invalid(self, form, client_form_set):
        return self.render_to_response(self.get_context_data(form=form, detalle_client_form_set=client_form_set))


class LoginView(FormView):
    form_class = AuthenticationForm
    template_name = 'Dashboard/login.html'
    success_url = reverse_lazy("Dashboard:panel")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(LoginView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            login(self.request, form.get_user())
            return super(LoginView, self).form_valid(form)
        else:
            return super(LoginView, self).form_invalid(form)


def logout_view(request):
    logout(request)
    return render(request, 'Dashboard/index.html')


''' 
------------------------------------------
Views landing page
------------------------------------------
'''


class Home(TemplateView):
    template_name = "Dashboard/index.html"


class ContactView(FormView):
    template_name = 'Dashboard/index.html'
    form_class = ContactForm
    success_url = '/'

    def form_valid(self, form):
        form.send_email()
        return super().form_valid(form)


''' 
------------------------------------------
Views panel de control
------------------------------------------
'''


class Panel(LoginRequiredMixin, TemplateView):
    template_name = "Panel/index.html"
    login_url = 'Dashboard:login'


class CreateRestaurant(LoginRequiredMixin, CreateView):
    form_class = RestaurantForm
    template_name = "Restaurants/new_restaurant.html"
    success_url = reverse_lazy("Dashboard:list_restaurant")

    login_url = 'Dashboard:login'

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            restaurant = form.save(commit=False)
            restaurant.owner = self.get_object()
            restaurant.save()
            return super(CreateRestaurant, self).form_valid(form)
        else:
            return super(CreateRestaurant, self).form_invalid(form)

    def get_object(self):
        client = Client.objects.get(user=self.request.user)
        return client


class UpdateRestaurant(LoginRequiredMixin, UpdateView):
    model = Restaurant
    form_class = RestaurantForm
    template_name = "Restaurants/update_restaurant.html"
    success_url = reverse_lazy("Dashboard:list_restaurant")
    login_url = 'Dashboard:login'

    def get_queryset(self):
        self.queryset = Restaurant.objects.filter(id=self.kwargs['pk'], owner=self.request.user.client, active=True)
        get_object_or_404(self.queryset, id=self.kwargs['pk'], owner=self.request.user.client, active=True)
        return self.queryset


class ListRestaurant(LoginRequiredMixin, ListView):
    model = Restaurant
    template_name = "Panel/list_restaurant.html"
    login_url = 'Dashboard:login'

    def get_queryset(self):
        queryset = Restaurant.objects.filter(
            owner=self.request.user.client, active=True)
        return queryset


class Detail(LoginRequiredMixin, TemplateView):
    model = Restaurant
    template_name = "Panel/restaurant_detail.html"
    login_url = 'Dashboard:login'

    def get_context_data(self, **kwargs):
        context = super(Detail, self).get_context_data(**kwargs)
        context['pk'] = self.kwargs['pk']
        return context


class CreateDish(LoginRequiredMixin, CreateView):
    model = Dish
    form_class = DishForm
    template_name = "Panel/create_dish.html"
    success_url = reverse_lazy("Dashboard:list_restaurant")

    def get_form(self, *args, **kwargs):
        form = super(CreateDish, self).get_form(*args, **kwargs)
        form.fields['restaurant'].queryset = Restaurant.objects.filter(id=self.kwargs['restaurant'])
        return form

    def get_success_url(self):
        pk = self.object.restaurant_id
        return reverse_lazy("Dashboard:list_dish", kwargs={"restaurant": pk})


class ListDish(LoginRequiredMixin, ListView):
    model = Dish
    template_name = "Panel/list_dish.html"
    form_class = DishForm

    def get_queryset(self):
        self.queryset = super(ListDish, self).get_queryset().filter(restaurant_id=self.kwargs['restaurant'])
        return self.queryset

    def get_context_data(self, **kwargs):
        context = super(ListDish, self).get_context_data(**kwargs)
        context['restaurant'] = self.kwargs['restaurant']
        return context


class UpdateDish(LoginRequiredMixin, UpdateView):
    model = Dish
    form_class = DishForm
    template_name = 'Panel/update_dish.html'
    success_url = reverse_lazy("Dashboard:list_restaurant")
    login_url = 'Dashboard:login'

    def get_success_url(self):
        pk = self.object.restaurant_id
        return reverse_lazy("Dashboard:list_dish", kwargs={"restaurant": pk})

    def get_queryset(self):
        self.queryset = super(UpdateDish, self).get_queryset().filter(id=self.kwargs['pk'],
                                                                      restaurant__owner_id=self.request.user.client.id)
        get_object_or_404(self.queryset, id=self.kwargs['pk'], restaurant__owner_id=self.request.user.client.id)
        return self.queryset


class DeleteDish(LoginRequiredMixin, DeleteView):
    model = Dish
    template_name = 'Panel/delete_dish.html'
    success_url = reverse_lazy("Dashboard:list_restaurant")
    login_url = 'Dashboard:login'

    def get_queryset(self):
        dish = self.kwargs['pk']
        return self.model.objects.filter(id=dish)

    def get_success_url(self):
        pk = self.object.restaurant_id
        return reverse_lazy("Dashboard:list_dish", kwargs={"restaurant": pk})


class CreateShedule(LoginRequiredMixin, CreateView):
    model = Shedule
    form_class = SheduleForm
    template_name = 'Panel/create_shedule.html'

    def get_form(self, *args, **kwargs):
        form = super(CreateShedule, self).get_form(*args, **kwargs)
        form.fields['restaurant'].queryset = Restaurant.objects.filter(id=self.kwargs['pk'], owner_id=self.request.user.client.id)
        return form

    def get_success_url(self):
        pk = self.object.restaurant_id
        return reverse_lazy("Dashboard:list_dish", kwargs={"restaurant": pk})


class ListShedule(LoginRequiredMixin, ListView):
    model = Shedule
    template_name = 'Panel/list_shedule.html'

    def get_queryset(self):
        self.queryset = Shedule.objects.filter(active=True, restaurant__id=self.kwargs['pk'], restaurant__owner_id=self.request.user.client.id)
        return self.queryset

    def get_context_data(self, **kwargs):
        context = super(ListShedule, self).get_context_data(**kwargs)
        context['pk'] = self.kwargs['pk']
        return context


class UpdateShedule(LoginRequiredMixin, UpdateView):
    model = Shedule
    template_name = 'Panel/update_shedule.html'
    form_class = SheduleForm

    def get_queryset(self):
        self.queryset = super(UpdateShedule, self).get_queryset().filter(active=True,
                                                                         restaurant__owner_id=self.request.user.client.id)
        get_object_or_404(self.queryset, id=self.kwargs['pk'], active=True,
                          restaurant__owner_id=self.request.user.client.id)
        return self.queryset

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy("Dashboard:list_shedule", kwargs={"pk": pk})


class DeleteShedule(LoginRequiredMixin, DeleteView):
    model = Shedule
    template_name = 'Panel/delete_shedule.html'
    success_url = reverse_lazy("Dashboard:list_shedule")
    login_url = 'Dashboard:login'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.active = False
        self.object.save()
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)


class CreateSocial(LoginRequiredMixin, CreateView):
    model = Social
    template_name = 'Panel/create_social.html'
    #form_class = SocialForm

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy("Dashboard:create_media", kwargs={"pk": pk})


class UpdateSocial(LoginRequiredMixin, UpdateView):
    model = Social
    template_name = 'Panel/update_social.html'
    #form_class = SocialForm

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy("Dashboard:list_media", kwargs={"pk": pk})


class CreateMedia(LoginRequiredMixin, CreateView):
    model = Media
    template_name = 'Panel/create_media.html'
    form_class = MediaForm

    def get_form(self, *args, **kwargs):
        form = super(CreateMedia, self).get_form(*args, **kwargs)
        form.fields['restaurant'].queryset = Restaurant.objects.filter(id=self.kwargs['pk'], owner_id=self.request.user.client.id)
        #form.fields['social'].queryset = Media.objects.filter(active=True, restaurant_id=self.kwargs['pk'],
                                                               #restaurant__owner_id=self.request.user.client.id)
        return form

    def get_context_data(self, **kwargs):
        context = super(CreateMedia, self).get_context_data(**kwargs)
        context['pk'] = self.kwargs['pk']
        return context

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy("Dashboard:list_media", kwargs={"pk": pk})


class ListMedia(LoginRequiredMixin, ListView):
    model = Media
    template_name = 'Panel/list_media.html'

    def get_queryset(self):
        self.queryset = Media.objects.filter(active=True, restaurant__id=self.kwargs['pk'], restaurant__owner_id=self.request.user.client.id)
        return self.queryset

    def get_context_data(self, **kwargs):
        context = super(ListMedia, self).get_context_data(**kwargs)
        context['pk'] = self.kwargs['pk']
        return context


class UpdateProfile(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'Panel/update_profile.html'
    form_class = UserUpdateForm
    second_form_class = UpdateProfileForm
    success_url = reverse_lazy("Dashboard:panel")

    login_url = 'Dashboard:login'

    def get_object(self):
        return User.objects.get(pk=self.request.user.pk)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = UserUpdateForm(instance=self.request.user)
        form2 = UpdateProfileForm(instance=self.request.user.client)

        return self.render_to_response(self.get_context_data(object=self.object, form=form, form2=form2))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        user = self.request.user
        client = self.request.user.client

        form = self.form_class(request.POST, instance=user)
        form2 = self.second_form_class(request.POST, instance=client)

        if form.is_valid() and form2.is_valid():

            userdata = form.save(commit=False)
            userdata.save()

            clientdata = form2.save(commit=False)
            clientdata.user = userdata
            clientdata.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form, form2=form2))


class DeleteRestaurant(LoginRequiredMixin, DeleteView):
    model = Restaurant
    template_name = 'Restaurants/delete_restaurant.html'
    success_url = reverse_lazy("Dashboard:list_restaurant")
    login_url = 'Dashboard:login'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.active = False
        self.object.save()
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)


class UpdatePlan(LoginRequiredMixin, UpdateView):
    model = Client
    fields = ['plan']
    template_name = "Panel/update_plan.html"
    success_url = reverse_lazy("Dashboard:update_profile")

    def get_object(self):
        client = Client.objects.get(user=self.request.user)
        return client

    def get_form(self, form_class=None):
        form = super(UpdatePlan, self).get_form()
        form.fields['plan'].widget.attrs.update({'class': 'form-control'})
        return form
