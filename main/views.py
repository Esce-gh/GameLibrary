from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from main.models import UserGameLibrary


# Create your views here.
def index(request):
    return render(request, "main/index.html")


@login_required
def library(request):
    # TODO: paging
    games = UserGameLibrary.objects.filter(user=request.user)
    context = {"games": games}
    return render(request, "main/library.html", context)
