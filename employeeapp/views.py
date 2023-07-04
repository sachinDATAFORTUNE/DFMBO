from django.shortcuts import render, redirect, HttpResponseRedirect
from .models import  Objective, Measure, Manager, Supervisor, Presale, Role, ObjectiveTemplate, Template
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth import authenticate, login
from datetime import datetime
from fiscalyear import *
import math
from django.db.models import Sum, Avg
from .forms import ObjectiveFormForManager, UpdateManagerForm, PresaleForm, ObjectiveFormForSupervisor, AddObjectiveForm
from django.db.models import Count, OuterRef, Subquery
from django.db.models import Func
from django.shortcuts import get_object_or_404
from django.db.models import Q
from datetime import date
from .SMTP import sending_mail
from fiscalyear import *
import pandas as pd
import json
from django.contrib.auth import logout
from django.db import connection
from django.conf import settings
from django.core.mail import send_mail

# Create your views here.
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        if "supervisor" in request.POST:
            user = auth.authenticate(username=username,password=password)
            if user is not None:
                login(request, user)
                return redirect("supervisor_url")
            else:
                return redirect('login_url')
        elif "manager" in request.POST:
            user = auth.authenticate(username=username,password=password)
            if user is not None:
                login(request, user)
                return redirect("manager_dashboard_url")
            else:
                return redirect('login_url')
        return redirect('login_url')
    else:
        return render(request, 'employeeapp/login.html')
        
def logout_view(request):
    logout(request)
    return redirect('login_url')

def update_manager_objective_view(request,object_id):
    username = request.user.username
    object = Objective.objects.get(pk=object_id)
    status = object.status
    actual = object.actual
    if status not in ["Accepted","Updated-By-Manager"]:
        return redirect("manager_mbo_url")
    elif status in ["Accepted","Updated-By-Manager"]:
        if request.method=="POST":
            actual = request.POST["actual"]
            object_by_filter = Objective.objects.filter(pk=object_id)
            # object_by_filter.update(actual=actual,status="Updated-By-Manager")
            for i in object_by_filter:
                i.actual = int(actual)
                i.status = "Updated-By-Manager"
                i.save()
            return redirect("manager_mbo_url")
    return render(request, 'employeeapp/update_manager_objective.html', {"username":username,"object":object,"object_id":object_id,"actual":actual})


def update_supervisor_objective_view(request,object_id,user_id):
    username = request.user.username
    object = Objective.objects.get(pk=object_id)
    user_id = object.manager.user.id
    status = object.status
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    current_month=now.month
    quarter=""
    if current_month in [1,2,3]:
        quarter=4
    elif current_month in [4,5,6]:
        quarter=1
    elif current_month in [7,8,9]:
        quarter=2
    if current_month in [10,11,12]:
        quarter=3
    weightage_sum = Manager.objects.filter(user_id=user_id,objective__year=year,objective__quarter=quarter).annotate(weighted_score_sum=Sum('objective__weightage')).values("weighted_score_sum")
    sum = weightage_sum[0]["weighted_score_sum"]
    if status in ["Sent-To-Supervisor","Created","Sent-To-Supervisor-After-Rejecting","Updated-By-Supervisor"]:
        if request.method=="POST":
            objective_name = request.POST["objective_name"]
            measure_content = request.POST["measure"]
            weightage = request.POST["weightage"]
            target = request.POST["target"]
            actual = request.POST["actual"]
            final = request.POST["final"]
            upper_percentage_for_weighted_score_calculation = request.POST["upper_percentage_for_weighted_score_calculation"]
            lower_percentage_for_weighted_score_calculation = request.POST["lower_percentage_for_weighted_score_calculation"]
            year = request.POST["year"]
            quarter = request.POST["quarter"]
            object_weightage = Objective.objects.filter(pk=object_id).values("weightage")
            previous_weightage_value= object_weightage[0]["weightage"]
            sum_of_weightage = (int(sum) - int(previous_weightage_value)) + int(weightage)
            measure1, created = Measure.objects.get_or_create(content=measure_content)
            measure = Measure.objects.get(content=measure1)
            object_by_filter = Objective.objects.filter(pk=object_id)
            if status in ["Updated-By-Supervisor","Sent-To-Supervisor"]:
                for i in object_by_filter:
                    i.objective_name=objective_name
                    i.measure=measure
                    i.weightage=weightage
                    i.target=int(target)
                    i.actual=int(actual)
                    i.final=int(final)
                    i.upper_percentage_for_weighted_score_calculation=int(upper_percentage_for_weighted_score_calculation)
                    i.lower_percentage_for_weighted_score_calculation=int(lower_percentage_for_weighted_score_calculation)
                    i.year=year
                    i.quarter=quarter
                    i.status="Updated-By-Supervisor"
                    i.save()
            elif status == "Created":
                for i in object_by_filter:
                    i.objective_name=objective_name
                    i.measure=measure
                    i.weightage=weightage
                    i.target=int(target)
                    i.actual=int(actual)
                    i.final=0
                    i.upper_percentage_for_weighted_score_calculation=int(upper_percentage_for_weighted_score_calculation)
                    i.lower_percentage_for_weighted_score_calculation=int(lower_percentage_for_weighted_score_calculation)
                    i.year=year
                    i.quarter=quarter
                    i.status="Created"
                    i.save()
            elif status == "Sent-To-Supervisor-After-Rejecting":
                        for i in object_by_filter:
                            i.objective_name=objective_name
                            i.measure=measure
                            i.weightage=weightage
                            i.target=int(target)
                            i.actual=int(actual)
                            i.final=0
                            i.upper_percentage_for_weighted_score_calculation=int(upper_percentage_for_weighted_score_calculation)
                            i.lower_percentage_for_weighted_score_calculation=int(lower_percentage_for_weighted_score_calculation)
                            i.year=year
                            i.quarter=quarter
                            i.status="Created"
                            i.comment = " "
                            i.save()
            return redirect("supervisor_manager_mbo_url",user_id=user_id)
        return render(request, 'employeeapp/update_supervisor_objective.html', {"username":username,"object":object,"user_id":user_id,"sum":sum,"status":status})
    return redirect("supervisor_manager_mbo_url",user_id=user_id)


def addpresale_data_view(request):
        user_id = request.user.id
        if request.method == 'POST':
            presale = Presale()
            presale.date = request.POST.get('date')
            presale.client= request.POST.get('client')
            presale.date = request.POST.get('company')
            presale.client= request.POST.get('project')
            presale.date = request.POST.get('technology')
            presale.client = request.POST.get('status')
            presale.date = request.POST.get('technology')
            presale.client = request.POST.get('status')
            presale.user_id = user_id
            presale.save()
            return render(request, 'employeeapp/manager.html')

        else:
                return render(request,'employeeapp/manager.html')
    

def supervisor_dashboard(request):
    user_id = request.user.id
    username = request.user.username
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    current_month=now.month
    if current_month in [1,2,3]:
        last_four_quarter = [4,3,2,1]
    elif current_month in [4,5,6]:
        last_four_quarter = [1,4,3,2]
    elif current_month in [7,8,9]:
        last_four_quarter = [2,1,4,3]
    elif current_month in [10,11,12]:
        last_four_quarter = [3,2,1,4]
    year_quarter = []
    if last_four_quarter[0]==4:
        year_quarter.append([(year,4),(year-1,3),(year-1,2),(year-1,1)])
    elif last_four_quarter[0]==1:
        year_quarter.append([(year,1),(year,4),(year-1,3),(year-1,2)])
    elif last_four_quarter[0]==2:
        year_quarter.append([(year,2),(year,1),(year,4),(year-1,3)])
    elif last_four_quarter[0]==3:
        year_quarter.append([(year,3),(year,2),(year,1),(year,4)])
    list_of_data_values = []
    list_of_labels =[]
    for i in year_quarter[0]:
        weightage_sum = Manager.objects.filter(supervisor_id__user_id=request.user.id,objective__year=i[0],objective__quarter=i[1]).annotate(weighted_score_sum=Sum('objective__weighted_score')).values("weighted_score_sum")
        if weightage_sum.exists():
            sum = weightage_sum[0]["weighted_score_sum"]
            list_of_data_values.append(sum)
        if i[1]==4:
            list_of_labels.append(f"Jan{str(i[0])[-2:]}-March{str(i[0])[-2:]}")
        elif i[1]==1:
            list_of_labels.append(f"April{str(i[0])[-2:]}-Jun{str(i[0])[-2:]}")
        elif i[1]==2:
            list_of_labels.append(f"July{str(i[0])[-2:]}-Sept{str(i[0])[-2:]}")
        elif i[1]==3:
            list_of_labels.append(f"Oct{str(i[0])[-2:]}-Dec{str(i[0])[-2:]}")
    raw_query = f"""
    select employee_id,
    (
            select username from auth_user where id = employeeapp_manager.user_id
        ) as username,(
        select ROUND(SUM(weighted_score)) from employeeapp_objective where year={year_quarter[0][0][0]} and quarter={year_quarter[0][0][1]} and manager_id = employeeapp_manager.id
        ) as q1_SUM_weighted_score,
        (
        select ROUND(SUM(weighted_score)) from employeeapp_objective where year={year_quarter[0][1][0]} and quarter={year_quarter[0][1][1]} and manager_id = employeeapp_manager.id
        ) as q2_SUM_weighted_score,
        (
        select ROUND(SUM(weighted_score)) from employeeapp_objective where year={year_quarter[0][2][0]} and quarter={year_quarter[0][2][1]} and manager_id = employeeapp_manager.id
        ) as q3_SUM_weighted_score,
        (
        select ROUND(SUM(weighted_score)) from employeeapp_objective where year={year_quarter[0][3][0]} and quarter={year_quarter[0][3][1]} and manager_id = employeeapp_manager.id
        ) as q4_SUM_weighted_score,
        user_id
        from employeeapp_manager where flag='Added'
    """
    raw_query = raw_query + ";"
    cursor = connection.cursor()
    cursor.execute(raw_query)
    row = cursor.fetchall()
    print(row,"This is row")
    return render(request, "employeeapp/supervisor.html", {"labels":list_of_labels,"username":username,"data":row,"user_id":user_id})


def get_objective(request):
    # user_id = request.user.id
    user_id = 2
    data = Objective.objects.filter(user_id__user_id=user_id).values("objective_id","objective_name",
                                                                    "measure__content","target",
                                                                    "weightage","actual","achieved",
                                                                    "mbo_achievement","weighted_score")
    # data = Objective.objects.filter(user_id=user_id)
    return render(request, "employeeapp/managermbo.html", {"data":data})

def updateManager(request, user_id):
    manager_list = Manager.objects.filter(user_id=user_id).values("employee_id","user__username","user__email")
    manager=manager_list[0]
    user = Manager.objects.get(user_id=user_id)
    updateForm = UpdateManagerForm(request.POST or None,instance=user)
    if updateForm.is_valid():
        updateForm.save()
        return redirect("supervisor_url")
    manager=manager_list[0]
    return render(request, "employeeapp/updatemanager.html", {"manager":manager})


def addmanager(request):
    username = request.user.username
    if request.method == "POST":
        employee_id = request.POST["employee_id"]
        employee_name = request.POST["employee_name"]
        email = request.POST["email"]
        manager = Manager.objects.filter(employee_id=employee_id)
        if manager.exists():
            manager.update(flag="Added")
            return redirect("supervisor_url")
        else:
            password = f"{employee_name}{employee_id}"
            create_user = User.objects.create_user(username=employee_name,email=email,password=password)
            create_user.save()
            supervisor = Supervisor.objects.get(user_id=request.user.id)
            manager = Manager.objects.create(employee_id=employee_id,user=create_user,supervisor=supervisor,flag="Added")
            manager.save()
            email=[email]
            password=password.replace(" ","")
            send_forget_password_mail(email, username,employee_name, password)
            return redirect("supervisor_url")
    return render(request, "employeeapp/addmanager.html",{"username":username})

def get_presale(request):
    data = "This is presale"
    return render(request, "employeeapp/presale.html", {"data":data})


def forgot_password(request):
    data = "This is presale"
    return render(request, "employeeapp/forgot-password.html", {"data":data})


def presale_for_manager_view(request):
    user_id = request.user.id
    data = Presale.objects.filter(user_id=user_id)
    return render(request, "employeeapp/presale_for_manager.html", {"data":data})

def presale_for_supervisor_view(request):
    user_id = request.user.id
    data = Presale.objects.filter(user_id=user_id)
    return render(request, "employeeapp/presale_for_supervisor.html", {"data":data})
    
class Round(Func):
    function = 'ROUND'
    template='%(function)s(%(expressions)s, 0)'

def manager_mbo(request):
    user_id = request.user.id
    username = request.user.username
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    current_month=now.month
    list_of_year = [year-i for i in range(4)]
    list_of_quarter = ["April-Jun","July-Sept","Oct-Dec","Jan-Mar"]
    quarter=0
    if current_month in [1,2,3]:
        quarter=4
    elif current_month in [4,5,6]:
        quarter=1
    elif current_month in [7,8,9]:
        quarter=2
    elif current_month in [10,11,12]:
        quarter=3
    # if request.method == "POST":
    #     data = request.POST
    #     if "actual" in data:
    #         actual = data.get("actual")
    #         objective_id = data.get("objective_id")
    #         print(objective_id,"****************************************************")
    #         object_by_filter = Objective.objects.filter(manager__user_id=user_id)
    #         # object_by_filter = Objective.objects.filter(objective_id=objective_id)
    #         object_by_filter.update(actual=actual,status="Updated-By-Manager")
    #         for i in object_by_filter:
    #             i.actual = int(actual)
    #             i.status = "Updated-By-Manager"
    #             i.save()
        if "year" in data:
            year = data.get("year")
            quarter = data.get("quarter")
            if quarter == "April-Jun":
                quarter = 1
            elif quarter == "July-Sept":
                quarter = 2
            if quarter == "Oct-Dec":
                quarter = 3
            elif quarter == "Jan-Mar":
                quarter = 4
    data = Objective.objects.filter(manager__user_id=user_id,year=year,quarter=quarter).order_by('objective_name').values("objective_id","objective_name","objective_subcategory",
                                                                    "measure__content","target1","target2","target3",
                                                                    "weightage","actual","achieved",
                                                                    "mbo_achievement","weighted_score","final",
                                                                    "lower_percentage_for_weighted_score_calculation",
                                                                    "upper_percentage_for_weighted_score_calculation","status")
    sum = Manager.objects.filter(user_id=user_id,objective__year=year,objective__quarter=quarter).annotate(weightage_sum=Sum('objective__weightage')).\
            annotate(weighted_score_sum=Sum('objective__weighted_score')).annotate(achieved_sum=Round(Avg('objective__achieved'))).\
            annotate(mbo_achievement_sum=Avg('objective__mbo_achievement')).values("weightage_sum","weighted_score_sum","achieved_sum","mbo_achievement_sum")
    if not data:
        weighted_score_sum = ""
        weightage_sum = ""
        achieved_sum = ""
        mbo_achievement_sum = ""
        
    else:
        for i in sum:
                if i["weighted_score_sum"] != None and i["weightage_sum"] != None and i["achieved_sum"] != None and i["mbo_achievement_sum"] != None:
                    weighted_score_sum = i["weighted_score_sum"]
                    weightage_sum = i["weightage_sum"]
                    achieved_sum = i["achieved_sum"]
                    mbo_achievement_sum = i["mbo_achievement_sum"]
                else:
                    weighted_score_sum = ""
                    weightage_sum = ""
                    achieved_sum = ""
                    mbo_achievement_sum = ""
    # accept_icon=""
    # reject_icon=""
    # status_in_data = [i["status"] for i in data]
    # for i in data:
    #     if "Sent-To-Manager" in status_in_data:
    #         reject_icon = f'<a href="/rejectedObjectiveByManager/{i.get("objective_id")}"><i class="fas fa-times close-icon" style="color:#A7090A"></i>&nbsp;</a>'
    #         accept_icon = f'<a href="/acceptedObjectiveByManager/{i.get("objective_id")}" onclick="AcceptingObjective()"><i class="fas fa-check" style="color:green"></i>&nbsp;</a>'  
    #     elif "Rejected" in status_in_data:
    #         reject_icon = f'<a href="/rejectedObjectiveByManager/{i.get("objective_id")}"><i class="fas fa-times close-icon" style="color:#A7090A"></i>&nbsp;</a>'
    #     else:
    #         accept_icon = f'<a href="/acceptedObjectiveByManager/{i.get("objective_id")}" onclick="AcceptingObjective()"><i class="fas fa-check" style="color:green"></i>&nbsp;</a>'
    # for i in data:
    #     if i.get("status") in ["Sent-To-Manager"]:
    #         reject_icon = f'<a href="/rejectedObjectiveByManager/{i.get("objective_id")}"><i class="fas fa-times close-icon" style="color:#A7090A"></i>&nbsp;</a>'
    #         accept_icon = f'<a href="/acceptedObjectiveByManager/{i.get("objective_id")}" onclick="AcceptingObjective()"><i class="fas fa-check" style="color:green"></i>&nbsp;</a>'
    #     elif i.get("status") in ["Rejected"]:
    #         reject_icon = f'<a href="/rejectedObjectiveByManager/{i.get("objective_id")}"><i class="fas fa-times close-icon" style="color:#A7090A"></i>&nbsp;</a>' 
        # else:
        #     accept_icon = f'<a href="/acceptedObjectiveByManager/{i.get("objective_id")}" onclick="AcceptingObjective()"><i class="fas fa-check" style="color:green"></i>&nbsp;</a>'
    return render(request, "employeeapp/managermbo.html", {"data":data,"username":username,"weighted_score_sum":weighted_score_sum,"achieved_sum":achieved_sum,
                "weightage_sum":weightage_sum,"mbo_achievement_sum":mbo_achievement_sum,"user_id":user_id,"year":list_of_year,"quarter":list_of_quarter})

def supervisor_manager_mbo(request,user_id):
    username = request.user.username
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    current_month=now.month
    quarter=""
    if current_month in [1,2,3]:
        quarter=4
    elif current_month in [4,5,6]:
        quarter=1
    elif current_month in [7,8,9]:
        quarter=2
    elif current_month in [10,11,12]:
        quarter=3
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    list_of_year = [year-i for i in range(4)]
    list_of_quarter = ["April-Jun","July-Sept","Oct-Dec","Jan-Mar"]
    number=[i for i in range(4)]
    manager = Manager.objects.get(user_id=user_id)
    if request.method == "POST":
        year = request.POST["year"]
        quarter = request.POST["quarter"]
        if quarter == "April-Jun":
            quarter = 1
        elif quarter == "July-Sept":
            quarter = 2
        if quarter == "Oct-Dec":
            quarter = 3
        elif quarter == "Jan-Mar":
            quarter = 4
    weightage_sum = Manager.objects.filter(id=manager.id,objective__year=year,objective__quarter=quarter).annotate(weighted_score_sum=Sum('objective__weightage')).values("weighted_score_sum")
    if weightage_sum.exists():
        sum_of_weightage = weightage_sum[0]["weighted_score_sum"]
    else:
        sum_of_weightage=0
    data = Objective.objects.filter(manager__user_id=user_id,year=year,quarter=quarter).order_by('objective_name').values("objective_id","objective_name","objective_subcategory",
                                                                "measure__content","target1","target2","target3",
                                                                "weightage","actual","final","achieved",
                                                                "mbo_achievement","weighted_score","status","comment")
    sum = Manager.objects.filter(user_id=user_id,objective__year=year,objective__quarter=quarter).annotate(weightage_sum=Sum('objective__weightage')).\
        annotate(weighted_score_sum=Sum('objective__weighted_score')).annotate(achieved_sum=Round(Avg('objective__achieved'))).\
        annotate(mbo_achievement_sum=Avg('objective__mbo_achievement')).values("weightage_sum","weighted_score_sum","achieved_sum","mbo_achievement_sum")
    if not data:
        weighted_score_sum = ""
        weightage_sum = ""
        achieved_sum = ""
        mbo_achievement_sum = ""
    else:
        for i in sum:
                if i["weighted_score_sum"] != None and i["weightage_sum"] != None and i["achieved_sum"] != None and i["mbo_achievement_sum"] != None:
                    weighted_score_sum = i["weighted_score_sum"]
                    weightage_sum = i["weightage_sum"]
                    achieved_sum = i["achieved_sum"]
                    mbo_achievement_sum = i["mbo_achievement_sum"]
                else:
                    weighted_score_sum = ""
                    weightage_sum = ""
                    achieved_sum = ""
                    mbo_achievement_sum = ""
    approve_button=""
    for i in data:
        if i.get("status") == "Updated-By-Supervisor":
            approve_button = f"<a href='/approvingObjectiveBySupervisor/{user_id}' class='btn btn-success btn-sm add-row' style='border-radius: 10px; padding: 5px; font-size: 14px; margin-bottom: 5px;' onclick='AlertApproving()''>Approve</a>"
    return render(request, "employeeapp/supervisor_manager_mbo.html", 
                {"data":data,"username":username,"weighted_score_sum":weighted_score_sum,"achieved_sum":achieved_sum,
                "weightage_sum":weightage_sum,"mbo_achievement_sum":mbo_achievement_sum,"user_id":user_id,"year":list_of_year,"quarter":list_of_quarter,"number":number,"year1":year,"quarter1":quarter,"sum":sum_of_weightage,"approve_button":approve_button})
def addobjective_view(request):
    username = request.user.username
    manager_queryset = Manager.objects.all()
    sum_of_weightage = 0
    if request.method=="POST":
        objective_name = request.POST["objective_name"]
        objective_subcategory = request.POST["objective_subcategory"]
        measure_content = request.POST["measure"]
        weightage = request.POST["weightage"]
        target1 = request.POST["target1"]
        target2 = request.POST["target2"]
        target3 = request.POST["target3"]
        user_id = request.POST["manager"]
        upper_percentage_for_weighted_score_calculation = request.POST["upper_percentage_for_weighted_score_calculation"]
        lower_percentage_for_weighted_score_calculation = request.POST["lower_percentage_for_weighted_score_calculation"]
        measure1, created = Measure.objects.get_or_create(content=measure_content)
        measure = Measure.objects.get(content=measure1)
        # object_by_filter = Objective.objects.filter(pk=object_id)
        manager = Manager.objects.get(id=user_id)
        # weightage_sum = Manager.objects.filter(id=manager.id,objective__year=2023,objective__quarter=2).annotate(weighted_score_sum=Sum('objective__weightage')).values("weighted_score_sum")
        # if weightage_sum.exists():
        #     sum_of_weightage = weightage_sum[0]["weighted_score_sum"] + int(weightage)
        # else:
        #     sum_of_weightage = int(weightage)
        Objective.objects.create(objective_name=objective_name,objective_subcategory=objective_subcategory,measure=measure,manager=manager,weightage=weightage,target1=int(target1),target2=int(target2),target3=int(target3),upper_percentage_for_weighted_score_calculation=int(upper_percentage_for_weighted_score_calculation),
            lower_percentage_for_weighted_score_calculation=int(lower_percentage_for_weighted_score_calculation),status="Created")
        return render(request, 'employeeapp/addobjective.html',{"manager":manager_queryset})
    return render(request, 'employeeapp/addobjective.html',{"manager":manager_queryset,"username":username})

def get_mbo(request):
    data = "This is presale"
    return render(request, "employeeapp/mbo.html", {"data":data})



def presale(request):
    data = "This is presale"
    return render(request, "employeeapp/presale.html", {"data":data})


def register(request):
    data = "This is presale"
    return render(request, "employeeapp/register.html", {"data":data})

def delete_manager(request, user_id):
    # manager = Manager.objects.get(user_id=user_id).delete()
    manager = get_object_or_404(Manager, user_id=user_id)
    manager_user = Manager.objects.filter(user_id=user_id)
    manager_user.update(flag="Not-Added")
    return redirect("supervisor_url")

def delete_objective(request, id):
    objective = get_object_or_404(Objective, objective_id=id)
    objective.delete()
    user_id = objective.manager.user.id
    return redirect("supervisor_manager_mbo_url",user_id=user_id)
    
    
    

def update_manager(request, user_id):
    manager = get_object_or_404(Manager, user_id=user_id)
    
    return redirect("supervisor_url") 

def updating_objective_status_after_submitting_info_by_manager(request,user_id):
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    current_month=now.month
    quarter=""
    if current_month in [1,2,3]:
        quarter=4
    elif current_month in [4,5,6]:
        quarter=1
    elif current_month in [7,8,9]:
        quarter=2
    elif current_month in [10,11,12]:
        quarter=3
    data = Objective.objects.filter(manager__user_id=user_id,year=year,quarter=quarter)
    status = data.values("status")
    for i in data:
        if i.status in ["Updated-By-Manager"]:
            i.status = "Sent-To-Supervisor"
            i.save()
        elif i.status in ["Rejected"]:
            i.status = "Sent-To-Supervisor-After-Rejecting"
            i.save()
            
    return redirect("manager_mbo_url")

def updating_objective_status_if_manager_rejects_it(request,user_id):
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    quarter = math.ceil(now.month/3)
    data = Objective.objects.filter(Q(status="Created"),user_id__user_id=user_id,year=year,quarter=quarter).values("status")
    data.update(status="Rejected")
    return redirect("manager_mbo_url")

def updating_objective_status_if_manager_accepts_it(request,user_id):
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    quarter = math.ceil(now.month/3)
    data = Objective.objects.filter(Q(status="Created"),user_id__user_id=user_id,year=year,quarter=quarter).values("status")
    data.update(status="Updated-By-Manager")
    return redirect("manager_mbo_url")


def sending_objective_to_manager(request,user_id):
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    quarter = math.ceil(now.month/3)
    # data = Objective.objects.filter(Q(status="Created") | Q(status="Updated-By-Supervisor"),Q(status="Accepted"),user_id__user_id=user_id,year=year,quarter=quarter)
    manager = Manager.objects.get(user_id=user_id)
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    current_month=now.month
    quarter=""
    if current_month in [1,2,3]:
        quarter=4
    elif current_month in [4,5,6]:
        quarter=1
    elif current_month in [7,8,9]:
        quarter=2
    if current_month in [10,11,12]:
        quarter=3
    weightage_sum = Manager.objects.filter(id=manager.id,objective__year=year,objective__quarter=quarter).annotate(weighted_score_sum=Sum('objective__weightage')).values("weighted_score_sum")
    sum_of_weightage = weightage_sum[0]["weighted_score_sum"]
    data = Objective.objects.filter(manager__user_id=user_id,year=year,quarter=quarter)
    if sum_of_weightage <= 100:
        for i in data:
            if i.status in ["Created"]:
                i.status="Sent-To-Manager"
                i.save()
                # email_subject = "MBO Intimation Mail"
                # email_to = "sachin.deshmukh@datafortune.com"
                # mail_from = "smtp.office365.com"
                # message="Objective Created by supervisor and sent for accept or reject, kindly accept or reject it"
            elif i.status in ["sent to supervisor after accepted by manager","Updated-By-Supervisor-After-Rejecting-By-Manager"]:
                i.status="Sent-To-Manager-To-Submit-Actual-Value"
                i.save()
        # sending_mail(email_subject,email_to,mail_from,message)
    return redirect("supervisor_manager_mbo_url",user_id=user_id)


def approving_objective_by_supervisor(request, user_id):
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    current_month=now.month
    quarter=""
    if current_month in [1,2,3]:
        quarter=4
    elif current_month in [4,5,6]:
        quarter=1
    elif current_month in [7,8,9]:
        quarter=2
    if current_month in [10,11,12]:
        quarter=3
    data = Objective.objects.filter(Q(status="Updated-By-Supervisor"),manager__user_id=user_id,year=year,quarter=quarter)
    for i in data:
        if str(i.measure) in ["No escalations for delivery","Zero account closure due to delivery"]:
            i.status = "Approved"
            i.save()
        elif i.final !=0:
            i.status = "Approved"
            i.save()
    # data.update(status="Approved")
    return redirect("supervisor_manager_mbo_url",user_id=user_id)


def accepted_objective_by_manager(request, objective_id):
    print(objective_id,"first check111111111111111111111111111111111111111111111111111111111111")
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    quarter = math.ceil(now.month/3)
    objective = Objective.objects.get(objective_id=objective_id)
    print(objective.status,"statussssssssssssssssssssssssssssssssssssssssssss")
    if objective.status == "Rejected":
        print("first if11111111111111111111111111111")    
        data = Objective.objects.filter(objective_id=objective_id)
        for i in data:
            i.status = "Accepted"
            i.save()
    elif objective.status == "Sent-To-Manager":
        print("second if2222222222222222222222222222222222222222222222") 
        data = Objective.objects.filter(objective_id=objective_id)
        for i in data:
            i.status = "Accepted"
            i.save()
    print("second check2222222222222222222222222222222222222222222222222222222222222222222222")
    # if objective.status == "Rejected":
    #     print("third if33333333333333333333333333333333333")   
    #     data = Objective.objects.filter(objective_id=objective_id)
    #     for i in data:
    #         i.status = "Accepted"
    #         i.save()
    #     data.update(status="Accepted")
    # print("third check33333333333333333333333333333333333333333333333333333333333333333333333333333333")
    return redirect("manager_mbo_url")
    

def rejected_objective_by_manager(request, objective_id):
    username = request.user.username
    current_fiscale_date = FiscalDate.today()
    now = datetime.datetime.now()
    objective = Objective.objects.get(objective_id=objective_id)
    if request.method == "POST":
        comment = request.POST["comment"]
        if objective.status == "Sent-To-Manager":    
            data = Objective.objects.filter(objective_id=objective_id)
            for i in data:
                i.status = "Rejected"
                i.comment = comment
                i.save()
        elif objective.status == "Accepted":    
            data = Objective.objects.filter(objective_id=objective_id)
            for i in data:
                i.status = "Rejected"
                i.comment = " "
                i.save()
        return redirect("manager_mbo_url")
    return render(request, "employeeapp/rejecting_objective.html", {"data":objective,"username":username})

# def rejected_objective_by_supervisor(request, user_id):
#     current_fiscale_date = FiscalDate.today()
#     year = current_fiscale_date.fiscal_year
#     now = datetime.datetime.now()
#     quarter = math.ceil(now.month/3)
#     data = Objective.objects.filter(Q(status="Sent-To-Supervisor"),user_id__user_id=user_id,year=year,quarter=quarter).values("status")
#     data.update(status="Rejected-By-Supervisor")
#     return redirect("supervisor_manager_mbo_url",user_id=user_id)

def create_copy_objective_view(request):
    username = request.user.username
    manager = Manager.objects.all().values("user_id","user__username")
    templates = Template.objects.all().values("template_name")
    return render(request, "employeeapp/copyobjective.html",{"username":username,"manager":manager,"templates":templates})

def copy_of_objective(request):
    username = request.user.username
    current_fiscale_date = FiscalDate.today()
    year = current_fiscale_date.fiscal_year
    now = datetime.datetime.now()
    current_month=now.month
    quarter=""
    if current_month in [1,2,3]:
        quarter=4
    elif current_month in [4,5,6]:
        quarter=1
    elif current_month in [7,8,9]:
        quarter=2
    if current_month in [10,11,12]:
        quarter=3
    if request.method=='POST':
        template_id = request.POST['templateid']
        manager_id = request.POST['managerid']
        print(manager_id,"****************************************88")
        template = Template.objects.filter(template_name=template_id).values("objective__objective_id")
        list_of_objective_template = []
        for i in template:
            list_of_objective_template.append(i["objective__objective_id"])
        for i in list_of_objective_template:
            print(i,"This is from iiiiiiiiiiiiiiiiiiiiiiiiiii")
            objective = ObjectiveTemplate.objects.get(objective_id=i)
            manager = Manager.objects.get(user__id=manager_id)
            Objective.objects.create(objective_name=objective.objective_name,
                                     objective_subcategory=objective.objective_subcategory,
                                     measure=objective.measure,target1=objective.target1,
                                     target2=objective.target2,target3=objective.target3,
                                     weightage=objective.weightage,manager=manager,
                                     lower_percentage_for_weighted_score_calculation=objective.lower_percentage_for_weighted_score_calculation,
                                     medium_percentage_for_weighted_score_calculation=objective.medium_percentage_for_weighted_score_calculation,
                                     upper_percentage_for_weighted_score_calculation=objective.upper_percentage_for_weighted_score_calculation)
        # print(list_of_objective_template,"*******************************************************")
        # data = Objective.objects.filter(manager__user_id=user_id1,year=year,quarter=quarter)
        # manager2 = Manager.objects.get(user_id=user_id2)
        # for i in data:
        #     i.pk = None
        #     i.manager = manager2
        #     i.actual = 0
        #     i.achieved = 0
        #     i.status = "Created"
        #     i.save()
    return redirect("supervisor_url")

def manager_dashboard(request):
        username = request.user.username
        current_fiscale_date = FiscalDate.today()
        year = current_fiscale_date.fiscal_year
        now = datetime.datetime.now()
        current_month=now.month
        if current_month in [1,2,3]:
            last_four_quarter = [4,3,2,1]
        elif current_month in [4,5,6]:
            last_four_quarter = [1,4,3,2]
        elif current_month in [7,8,9]:
            last_four_quarter = [2,1,4,3]
        elif current_month in [10,11,12]:
            last_four_quarter = [3,2,1,4]
        year_quarter = []
        if last_four_quarter[0]==4:
            year_quarter.append([(year,4),(year-1,3),(year-1,2),(year-1,1),(year-1,4),(year-2,3),(year-2,2),(year-1,1)])
        elif last_four_quarter[0]==1:
            year_quarter.append([(year,1),(year,4),(year-1,3),(year-1,2),(year-1,1),(year-1,4),(year-2,3),(year-2,2)])
        elif last_four_quarter[0]==2:
            year_quarter.append([(year,2),(year,1),(year,4),(year-1,3),(year-1,2),(year-1,1),(year-1,4),(year-2,3)])
        elif last_four_quarter[0]==3:
            year_quarter.append([(year,3),(year,2),(year,1),(year,4),(year-1,3),(year-1,2),(year-1,1),(year-1,4)])
        list_of_data_values = []
        list_of_labels =[]
        for i in year_quarter[0]:
                # weightage_sum = Manager.objects.filter(user_id=request.user.id,objective__year=i[0],objective__quarter=i[1]).annotate(weighted_score_sum=Sum('objective__weighted_score')).values("weighted_score_sum")
                weightage_sum = Manager.objects.filter(user_id=request.user.id,objective__year=i[0],objective__quarter=i[1]).annotate(weighted_score_sum=Sum('objective__weighted_score')).values("weighted_score_sum")
                if weightage_sum.exists():
                    sum = weightage_sum[0]["weighted_score_sum"]
                    list_of_data_values.append(sum) 
                if i[1]==4:
                    list_of_labels.append(f"Jan{str(i[0])[-2:]}-March{str(i[0])[-2:]}")
                elif i[1]==1:
                    list_of_labels.append(f"April{str(i[0])[-2:]}-Jun{str(i[0])[-2:]}")
                elif i[1]==2:
                    list_of_labels.append(f"July{str(i[0])[-2:]}-Sept{str(i[0])[-2:]}")
                elif i[1]==3:
                    list_of_labels.append(f"Oct{str(i[0])[-2:]}-Dec{str(i[0])[-2:]}")
        # list_of_labels = reversed(list_of_labels)
        # list_of_data_values = reversed(list_of_data_values)
        # print(list_of_labels)
        # print(list_of_data_values)
        if len(list_of_data_values) != 8:
            for i in range(len(list_of_data_values),8):
                list_of_data_values.append(0)
        return render(request, 'employeeapp/manager_dashboard.html', {
            'labels': json.dumps(list_of_labels[::-1]),
            'data': json.dumps(list_of_data_values[::-1]),
            'username':username
        })
        # return render(request, 'employeeapp/manager_dashboard.html',{
        #     "labels":json.dumps(labels),
        #     "data":json.dumps(data)
        #     })
    # current_fiscale_date = FiscalDate.today()
    # year = current_fiscale_date.fiscal_year
    # user_id = request.user.id
    # if request.method=='POST':
    #     year = request.POST["year"]
    #     user_id = request.user.id
    #     now = datetime.datetime.now()
    # first_quarter_weitage = Objective.objects.filter(quarter=1,year=int(year)).annotate(quarter_first=Sum("weightage")).values('quarter_first')
    # second_quarter_weitage = Objective.objects.filter(quarter=2,year=int(year)).annotate(quarter_second=Sum("weightage")).values('quarter_second')
    # third_quarter_weitage = Objective.objects.filter(quarter=3,year=int(year)).annotate(quarter_third=Sum("weightage")).values('quarter_third')
    # fourth_quarter_weitage = Objective.objects.filter(quarter=4,year=int(year)).annotate(quarter_fourth=Sum("weightage")).values('quarter_fourth')
    # print(type(second_quarter_weitage),"VVVVVVVVVVVVVVVVVVVVV")
    # if first_quarter_weitage.exists():
    #     first_quarter_weitage = first_quarter_weitage[0]["quarter_first"]
    # else:
    #     first_quarter_weitage = 0
    # if second_quarter_weitage.exists():
    #     second_quarter_weitage = second_quarter_weitage[0]["quarter_second"]
    # else:
    #     second_quarter_weitage = 0
    # if third_quarter_weitage.exists():
    #     third_quarter_weitage = third_quarter_weitage[0]["quarter_third"]
    # else:
    #     third_quarter_weitage = 0
    # if fourth_quarter_weitage.exists():
    #     fourth_quarter_weitage = fourth_quarter_weitage[0]["quarter_fourth"]
    # else:
    #     fourth_quarter_weitage = 0
    # # print(second_quarter_weitage,"**********************")
    # # print(third_quarter_weitage,"**********************")
    # # print(fourth_quarter_weitage,"****************************")
    # # data = Manager.objects.filter(supervisor_id__user_id=user_id)\
    # #         .annotate(quarter_first=Subquery(first_quarter_weitage))\
    # #         .annotate(quarter_second=Subquery(second_quarter_weitage))\
    # #         .annotate(quarter_third=Subquery(third_quarter_weitage))\
    # #         .annotate(quarter_fourth=Subquery(fourth_quarter_weitage))\
    # #         .values("user_id","employee_id","user__username","user__email","quarter_first","quarter_second","quarter_third","quarter_fourth")
    # # print(data,"**********************************************")
    # current_year = date.today().year
    # list_of_year = [current_year-i for i in range(4)]
    # data=""
    # return render(request, 'employeeapp/manager_dashboard.html',{"list_of_year":list_of_year,
    #                                                              "first":first_quarter_weitage,
    #                                                              "second":second_quarter_weitage,
    #                                                              "third":third_quarter_weitage,
    #                                                              "fourth":fourth_quarter_weitage})


def objective_template(request):
    role = Role.objects.all()
    username = request.user.username
    # # role = request.POST["role"]
    # if request.method == "POST":
    #     user_role = request.POST["userrole"]
    #     template = ObjectiveTemplate.objects.filter(role__role=user_role)
    # else:
    #     template = ObjectiveTemplate.objects.filter(role__role="Developer")
    template = Template.objects.all()
    return render(request, "employeeapp/objective_template.html",{"role":role,"username":username,"Template":template})

def objective_template_by_id(request,id):
    username = request.user.username
    # template = Template.objects.filter(id=id).values_list("objective__objective_name","objective__role","objective__target","objective__weightage")
    template = Template.objects.filter(id=id).values("template_name","objective__objective_id","objective__objective_name","objective__objective_subcategory","objective__measure__content","objective__target1","objective__target2","objective__target3","objective__weightage")
    # template_objective = ObjectiveTemplate.objects.filter(role__role="Manager").values("objective_id","objective_name","measure__content","target","weightage")
    return render(request,"employeeapp/objective_template_by_id.html",{"template_name":template[0].get("template_name"),"template_id":id,"username":username,"template_objective":template})

def create_template(request):
    username = request.user.username
    template_queryset = Template.objects.all()
    if request.method == "POST":
        template_name = request.POST["template_name"]
        Template.objects.create(template_name=template_name)
        return redirect("objective_template_url")
    return render(request, 'employeeapp/create_objective_template.html',{"template_queryset":template_queryset,"username":username})
        
    
    
def delete_template(request,id):
    objective = get_object_or_404(Template, id=id)
    objective.delete()
    return redirect("objective_template_url")
    

def delete_objective_template_by_ID(request,template_id,objective_id):
    objective = get_object_or_404(ObjectiveTemplate, objective_id=objective_id)
    objective.delete()
    return redirect("objective_template_by_id_url",id=template_id)

def edit_objective_template_by_ID(request,template_id,objective_id):
    username = request.user.username
    objective_template = ObjectiveTemplate.objects.get(objective_id=objective_id)
    if request.method=="POST":
            objective_name = request.POST["objective_name"]
            measure_content = request.POST["measure"]
            weightage = request.POST["weightage"]
            target = request.POST["target"]
            objective_by_filter = ObjectiveTemplate.objects.filter(objective_id=objective_id)
            measure1, created = Measure.objects.get_or_create(content=measure_content)
            measure = Measure.objects.get(content=measure1)
            for i in objective_by_filter:
                i.objective_name = objective_name
                i.measure = measure
                i.weightage = weightage
                i.target = target
                i.save()
            return redirect("objective_template_by_id_url",id=template_id)
    return render(request, 'employeeapp/edit_objective_template_by_ID.html', {"username":username,"object_template":objective_template,"template_id":template_id})
    
    
    
def add_objective_in_template(request,id):
    username = request.user.username
    if request.method=="POST":
        objective_name = request.POST["objective_name"]
        objective_subcategory = request.POST["objective_subcategory"]
        measure_content = request.POST["measure"]
        weightage = request.POST["weightage"]
        target1 = request.POST["target1"]
        target2 = request.POST["target2"]
        target3 = request.POST["target3"]
        upper_percentage_for_weighted_score_calculation = request.POST["upper_percentage_for_weighted_score_calculation"]
        medium_percentage_for_weighted_score_calculation = request.POST["medium_percentage_for_weighted_score_calculation"]
        lower_percentage_for_weighted_score_calculation = request.POST["lower_percentage_for_weighted_score_calculation"]
        measure1, created = Measure.objects.get_or_create(content=measure_content)
        measure = Measure.objects.get(content=measure1)
        role1, role_created = Role.objects.get_or_create(role="Manager")
        role = Role.objects.get(role=role1)
        objective = ObjectiveTemplate.objects.create(objective_name=objective_name,objective_subcategory=objective_subcategory,measure=measure,role=role,weightage=weightage,
                                                     target1=int(target1),target2=int(target2),target3=int(target3),
                                                     upper_percentage_for_weighted_score_calculation=int(upper_percentage_for_weighted_score_calculation),
                                                    medium_percentage_for_weighted_score_calculation=int(medium_percentage_for_weighted_score_calculation),
                                                    lower_percentage_for_weighted_score_calculation=int(lower_percentage_for_weighted_score_calculation))
        template = Template.objects.filter(id=id).values("objective__objective_id")
        list_of_objective_ids=[]
        for i in template:
            list_of_objective_ids.append(i["objective__objective_id"])
        list_of_objective_ids.append(objective.objective_id)
        template1 = Template.objects.get(id=id)
        template1.objective.add(objective)
        return redirect("objective_template_by_id_url",id=id)
    return render(request, 'employeeapp/add_objective_in_template.html',{"username":username})
   
   
def send_forget_password_mail(email, supervisor_name,username, password):
    subject = "Welcome to team, test mail for MBO user"
    message = f'''Hi,
you are added to {supervisor_name}'s team, following are credential.

Username = {username}
Password = {password}

Kindly login to this url and reset your password - http://20.10.177.33:8000/login.

Thanks.
    
    '''
    email_from = settings.EMAIL_HOST_USER
    recipient_list = email
    send_mail(subject, message, email_from, recipient_list)
    return True