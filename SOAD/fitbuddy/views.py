from django.shortcuts import render,redirect, get_object_or_404, HttpResponseRedirect
from django.contrib.auth import login,logout,authenticate
from django.views.generic import CreateView
from .models import User, Customer, FitnessCenter, Program, Review
from .forms import CustomerRegistrationForm,FitnessRegistrationForm, ProgramForm, ReviewForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime
from fitbuddy.decorators import *
from django.db.models import Q 
from django.db.models import Avg

# Create your views here
def index_view(request):
    list={}
    fitcenter = FitnessCenter.objects.all()
    list["fitcenter"] = fitcenter
    context = {"fitcenter":fitcenter}
    return render(request, "fitbuddy/home.html",context=context)


@login_required
def profile_view(request):
    return render(request, "fitbuddy/profile.html")

# def index(request):
#     return render(request,'fitbuddy/index.html')

# def register(request):
#     return render(request,'fitbuddy/register.html')

def view_programs(request):
    return render(request,'fitbuddy/program_list.html',context={'programs': Program.objects.all()})

def program_detail(request, slug):
    program = Program.objects.get(slug=slug)
    reviews = Review.objects.filter(program=program).order_by("-comment")
    average = reviews.aggregate(Avg("rating"))["rating__avg"]
    if average == None:
        average = 0
    average = round(average, 2)
    context = {
        "program" : program,
        'reviews' : reviews,
        "average": average
    }
    return render(request, 'fitbuddy/program_detail.html',context)

class customer_register(CreateView):
    model = User
    form_class = CustomerRegistrationForm
    template_name = 'fitbuddy/customer_register.html'

    def form_valid(self,form):
        user = form.save()
        login(self.request,user)
        return redirect('/')


class fitness_register(CreateView):
    model = User
    form_class = FitnessRegistrationForm
    template_name = 'fitbuddy/fitness_register.html'

    def form_valid(self,form):
        user = form.save()
        login(self.request,user)
        return redirect('/')

def login_view(request):
    if request.method=='POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username,password=password)
            if user is not None:
                login(request,user)
                return redirect('/')
            else:
                messages.error(request,"Invalid username or password")
        else:
                messages.error(request,"Invalid username or password")

    return render(request,'fitbuddy/login.html',context={'form':AuthenticationForm()})

def logout_view(request):
    logout(request)
    return redirect('/')

@fitness_center_required
def add_program(request):
    if request.method == "POST":
        form = ProgramForm(request.POST, request.FILES)

        if form.is_valid():
            data = form.save(commit=False)
            fcenter = FitnessCenter.objects.get(user=request.user)
            data.fcenter = fcenter
            data.slug = datetime.now().strftime("%c")
            data.save()
            return redirect('/')

    else:
        form = ProgramForm()
    return render(request, 'fitbuddy/add_program.html',{"form":form})

@fitness_center_required
def edit_program(request, slug):    
	program = Program.objects.get(slug=slug)
	if request.method == "POST" and request.user == program.fcenter.user:
		form = ProgramForm(request.POST, instance=program)
		if form.is_valid():
				data = form.save(commit=False)
				data.save()
				return redirect("program_detail", slug)
	else:
		form = ProgramForm(instance=program)
	return render(request, 'fitbuddy/add_program.html', {"form": form})

@fitness_center_required
def delete_program(request, slug):
    context = {}
    program = get_object_or_404(Program, slug=slug)
    if request.method == "POST" and request.user == program.fcenter.user :
        program.delete()
        return redirect("list_programs")
    return render(request, 'fitbuddy/program_delete.html',context)

def search_programs(request):
    query=request.GET.get('q1')
    if query:
        all_programs=Program.objects.all()
        results=all_programs.filter(Q(title__icontains=query)|Q(category__icontains=query))
    else:
        results=Program.objects.all()
    context={
        'programs' : results
    }
    return render(request,'fitbuddy/program_list.html',context)

def pricerange1(request):
	programs = Program.objects.filter(price__range=(0,1500))
	context={
		'programs' : programs
	}
	return render(request,'fitbuddy/program_list.html',context)	

def pricerange2(request):
	programs = Program.objects.filter(price__range=(1500,3000))
	context={
		'programs' : programs
	}
	return render(request,'fitbuddy/program_list.html',context)	

def pricerange3(request):
	programs = Program.objects.filter(price__range=(3000,5000))
	context={
		'programs' : programs
	}
	return render(request,'fitbuddy/program_list.html',context)	

def pricerange4(request):
	programs = Program.objects.filter(price__range=(5000,10000))
	context={
		'programs' : programs
	}
	return render(request,'fitbuddy/program_list.html',context)	

def add_review(request, slug):
    if request.user.is_authenticated:
        program = Program.objects.get(slug=slug)
        if request.method == "POST":
            form = ReviewForm(request.POST or None)
            if form.is_valid():
                data = form.save(commit=False)
                data.comment = request.POST["comment"]
                data.rating = request.POST["rating"]
                data.user = request.user
                data.program = program
                data.slug = datetime.now().strftime("%c")
                data.save()
                return redirect("program_detail", slug)
        else:
            form = ReviewForm()
        return render(request, 'fitbuddy/program_detail.html', {"form": form})
    else:
        return redirect("fitbuddy/login.html")

def edit_review(request, program_slug, review_slug):
    if request.user.is_authenticated:
        program = Program.objects.get(slug=program_slug)
        # review
        review = Review.objects.get(program=program, slug=review_slug)

        # check if the review was done by the logged in user
        if request.user == review.user:
            # grant permission
            if request.method == "POST":
                form = ReviewForm(request.POST, instance=review)
                if form.is_valid():
                    data = form.save(commit=False)
                    if (data.rating > 10) or (data.rating < 0):
                         error = "Out or range. Please select rating from 0 to 10."
                         return render(request, 'fitbuddy/edit_review.html', {"error": error, "form": form})
                    else:
                        data.save()
                        return redirect("program_detail", program_slug)
            else:
                form = ReviewForm(instance=review)
            return render(request, 'fitbuddy/edit_review.html', {"form": form})
        else:
            return redirect("program_detail", program_slug)
    else:
        return redirect("login")

def delete_review(request, program_slug, review_slug):
    if request.user.is_authenticated:
        program = Program.objects.get(slug=program_slug)
        # review
        review = Review.objects.get(program=program, slug=review_slug)

        # check if the review was done by the logged in user
        if request.user == review.user:
            # grant permission to delete
            review.delete()

        return redirect("program_detail", program_slug)
            
    else:
        return redirect("login")