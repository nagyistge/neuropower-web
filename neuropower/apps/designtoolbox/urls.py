from . import views
from django.conf.urls import url
from django.contrib import admin
import django.views.defaults

urlpatterns = [
    url(r'^start/$',views.start,name='DStart'),
    url(r'^maininput/$',views.maininput,name='DMainInput'),
    url(r'^consinput/$',views.consinput,name='DConsInput'),

    url(r'^FAQ/$',views.FAQ,name='DFAQ'),
    url(r'^tutorial/$',views.tutorial,name='DTutorial'),
    url(r'^methods/$',views.methods,name='DMethods'),
    ]