from django.shortcuts import render

def tailwind_home(request):
    return render(request, "base.html")
