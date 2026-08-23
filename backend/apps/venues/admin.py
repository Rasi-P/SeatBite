from django.contrib import admin
from .models import Screen, Seat, Venue

admin.site.register([Venue, Screen, Seat])
