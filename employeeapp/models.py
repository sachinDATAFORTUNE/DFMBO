from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from fiscalyear import *
from django.db.models import Q
import math
# Create your models here.

class Supervisor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50)
    def __str__(self):
        return self.user.username

class Manager(models.Model):
    flag_choices = (
        ("Added","Added"),
        ("Not-Added","Not-Added")
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50)
    supervisor = models.ForeignKey("Supervisor", on_delete=models.CASCADE)
    flag = models.CharField(max_length=100,default="Not-Added",choices=flag_choices)
    
    def __str__(self):
        return self.user.username

class Developer(models.Model):
    flag_choices = (
        ("Added","Added"),
        ("Not-Added","Not-Added")
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=50)
    manager = models.ForeignKey("Manager", on_delete=models.CASCADE)
    flag = models.CharField(max_length=100,default="Not-Added",choices=flag_choices)
    
    def __str__(self):
        return self.user.username
    
class Measure(models.Model):
    measure_id = models.AutoField(primary_key=True)
    content = models.CharField(max_length=10000)
    
    def __str__(self):
        return self.content

class Objective(models.Model):
    status_choices = (
        ("Created","Created"),
        ("Sent-To-Manager","Sent-To-Manager"),
        ("Accepted","Accepted"),
        ("Rejected","Rejected"),
        ("Updated-By-Manager","Updated-By-Manager"),
        ("Sent-To-Supervisor","Sent-To-Supervisor"),
        ("Sent-To-Supervisor-After-Rejecting","Sent-To-Supervisor-After-Rejecting"),
        ("Sent-Back-To-Manager","Sent-Back-To-Manager"),
        ("Updated-By-Supervisor","Updated-By-Supervisor"),
        ("Approved","Approved"),
        # ("Confirmed-By-Manager","Confirmed-By-Manager")
        # ("Object-Created-And-Sent-To-Manager","Object-Created-And-Sent-To-Manager"),
        # ("Sent-To-Manager","Sent-To-Manager"),
        # ("Rejected-By-Manager","Rejected-By-Manager"),
        # ("Sent-To-Manager-To-Accept-Or-Reject","Sent-To-Manager-To-Accept-Or-Reject"),
        # ("Sent-To-Manager-To-Submit-Actual-Value","Sent-To-Manager-To-Submit-Actual-Value"),
        # ("sent to supervisor after accepted by manager","sent to supervisor after accepted by manager"),
        # ("Sent-To-Supervisor-After-Updating-Objective-By-Manager","Sent-To-Supervisor-After-Updating-Objective-By-Manager"),
        # ("sent to supervisor after rejected by manager","sent to supervisor after rejected by manager"),
        # ("After-Rejecting-By-Manager-Updated-By-Supervisor","After-Rejecting-By-Manager-Updated-By-Supervisor"),
        # ("Accepted-By-Manager","Accepted-By-Manager"),
        # ("Updated-By-Supervisor-After-Rejecting-By-Manager","Updated-By-Supervisor-After-Rejecting-By-Manager"),
        # ("Updated-By-Manager","Updated-By-Manager"),
        # ("Sent-To-Supervisor","Sent-To-Supervisor"),
        # ("Updated-By-Supervisor","Updated-By-Supervisor"),
        # ("Final-Update-By-Supervisor","Final-Update-By-Supervisor"),
        # ("Approved","Approved")
        )
    objective_id = models.AutoField(primary_key=True)
    objective_name = models.CharField(max_length=200)
    objective_subcategory = models.CharField(max_length=200,blank=True)
    measure = models.ForeignKey("Measure",on_delete=models.CASCADE)
    manager = models.ForeignKey("Manager",on_delete=models.CASCADE)
    # manager = models.OneToOneField(User, on_delete=models.CASCADE,blank=True,null=True)
    target1 = models.IntegerField(blank=True, default=0)
    target2 = models.IntegerField(blank=True, default=0)
    target3 = models.IntegerField(blank=True, default=0)
    weightage = models.IntegerField(blank=True, default=0)
    actual = models.IntegerField(blank=True, default=0)
    final = models.IntegerField(blank=True, default=0)
    achieved = models.IntegerField(blank=True, default=0)
    mbo_achievement = models.IntegerField(blank=True, default=None)
    weighted_score = models.IntegerField(blank=True, default=None)
    lower_percentage_for_weighted_score_calculation = models.IntegerField(blank=True, default=70)
    medium_percentage_for_weighted_score_calculation = models.IntegerField(blank=True, default=80)
    upper_percentage_for_weighted_score_calculation = models.IntegerField(blank=True, default=120)
    year = models.IntegerField(default=0)
    quarter = models.IntegerField(default=0)
    status= models.CharField(max_length=100,choices = status_choices,default="Created")
    comment = models.CharField(max_length=1000, blank=True)
    
    
    
    def save(self, *args, **kwargs):
        now = datetime.datetime.now()
        mbo_achievement=0
        achievded=0
        if self.target1 != 0:
            if self.final != 0:
                achievded = (self.final/self.target1)*100
            else:
                achievded = (self.actual/self.target1)*100
            if self.final != 0:
                mbo_achievement = (self.final/self.target1)*100
            else:
                mbo_achievement = (self.actual/self.target1)*100
        if self.target1 == 0 and self.status in ["Updated-By-Manager", "Sent-To-Supervisor","Updated-By-Supervisor","Approved"]:
            if self.actual == 0 and self.final==0:
                mbo_achievement = 100
                achievded = 100
            elif (self.actual < self.target2 or self.final < 0) and (self.actual < self.target2 or self.final < self.target2):
                calculation = ((self.target2 - self.actual)/self.target2)*(self.upper_percentage_for_weighted_score_calculation - self.medium_percentage_for_weighted_score_calculation)
                mbo_achievement = calculation + self.medium_percentage_for_weighted_score_calculation
                achievded = calculation + self.medium_percentage_for_weighted_score_calculation
            elif (self.actual == self.target2 or self.final == 0) and (self.actual == self.target2 or self.final == self.target2):
                mbo_achievement = self.medium_percentage_for_weighted_score_calculation
                achievded = self.medium_percentage_for_weighted_score_calculation
            elif self.actual > self.target2 or self.final > self.target2:
                mbo_achievement = 0
                achievded = 0
        # if "Zero account closure due to delivery" in str(self.measure):
        #     if self.status in ["Updated-By-Manager", "Sent-To-Supervisor","Updated-By-Supervisor","Approved"]:
        #         if self.actual == 0 and self.final==0:
        #             mbo_achievement = 120
        #             achievded = 120
        #         elif self.actual == 1 and self.final==1:
        #             mbo_achievement = 0
        #             achievded = 0
        #         elif self.actual == 0 and self.final==1:
        #             mbo_achievement = 0
        #             achievded = 0
        # if "No escalations for delivery" in str(self.measure):
        #     if self.status in ["Updated-By-Manager", "Sent-To-Supervisor","Updated-By-Supervisor","Approved"]:
        #         if self.actual == 0 and self.final==0:
        #             mbo_achievement = 100
        #             achievded = 100
        #         elif self.actual == 1 and self.final == 1:
        #             mbo_achievement = 50
        #             achievded = 50
        #         elif self.actual == 0 and self.final == 1:
        #             mbo_achievement = 50
        #             achievded = 50
        #         elif self.actual > 1 or self.final > 1:
        #             mbo_achievement = 0
        #             achievded = 0
        #         elif self.actual == 0 or self.final > 1:
        #             mbo_achievement = 0
        #             achievded = 0
        if mbo_achievement>self.upper_percentage_for_weighted_score_calculation:
            mbo_achievement=120
        elif mbo_achievement<self.lower_percentage_for_weighted_score_calculation:
            mbo_achievement=0
        #if "Attrition Less than 10% team size in 6 months" in self.measure.lower():
            #if self.actual == 0:
                #mbo_achievement = 100
            #elif self.actual == 1:
                #mbo_achievement = 50
            #elif self.actual > 1:
                #mbo_achievement = 0
        self.achieved = achievded
        self.mbo_achievement = mbo_achievement
        weighted_score = int(self.weightage)*mbo_achievement/100
        self.weighted_score = weighted_score
        current_fiscale_date = FiscalDate.today()
        self.year = current_fiscale_date.fiscal_year
        current_month=now.month
        quarter=0                
        if current_month in [1,2,3]:
            quarter=4
        elif current_month in [4,5,6]:
            quarter=1
        elif current_month in [7,8,9]:
            quarter=2
        if current_month in [10,11,12]:
            quarter=3
        self.quarter = quarter
        super(Objective, self).save(*args, **kwargs)

    
    def __str__(self):
        return self.objective_name
    
    
class Presale(models.Model):
    status_choices = (
        ("Open","Open"),
        ("Close","Close"),
        ("Active","Active"),
        ("On-HOld","On-HOld")
        )
    date = models.DateField()
    client_name = models.CharField(max_length=1000, default=None)
    company_name = models.CharField(max_length=1000, default=None)
    project = models.CharField(max_length=1000, default=None)
    technology = models.CharField(max_length=1000, default=None)
    status = models.CharField(max_length=1000, choices = status_choices,default=None)
    user = models.ForeignKey(User,on_delete=models.CASCADE, default=None)
    
    
    def __str__(self):
        return self.project
    

    
class WeightageScoreQuarterly(models.Model):
    year = models.IntegerField()
    weighatage_sum = models.IntegerField()
    first_quarter_value = models.IntegerField()
    second_quarter_value = models.IntegerField()
    third_quarter_value =  models.IntegerField()

class Role(models.Model):
    role = models.CharField(max_length=120)
    def __str__(self):
        return self.role
    
class ObjectiveTemplate(models.Model):
    objective_id = models.AutoField(primary_key=True)
    objective_name = models.CharField(max_length=200)
    objective_subcategory = models.CharField(max_length=200,blank=True)
    measure = models.ForeignKey("Measure",on_delete=models.CASCADE)
    role = models.ForeignKey("Role",on_delete=models.CASCADE)
    # manager = models.ForeignKey("Manager",on_delete=models.CASCADE)
    target1 = models.IntegerField(blank=True, default=0)
    target2 = models.IntegerField(blank=True, default=0)
    target3 = models.IntegerField(blank=True, default=0)
    weightage = models.IntegerField(blank=True, default=0)
    lower_percentage_for_weighted_score_calculation = models.IntegerField(blank=True, default=70)
    medium_percentage_for_weighted_score_calculation = models.IntegerField(blank=True, default=90)
    upper_percentage_for_weighted_score_calculation = models.IntegerField(blank=True, default=120)
        
    def __str__(self):
        return self.objective_name
    
class Template(models.Model):
    template_name = models.CharField(max_length=200)
    objective = models.ManyToManyField(ObjectiveTemplate,blank=True)
    # objective_name = models.CharField(max_length=200)
    # measure = models.ForeignKey("Measure",on_delete=models.CASCADE)
    # # role = models.ForeignKey("Role",on_delete=models.CASCADE)
    # manager = models.ForeignKey("Manager",on_delete=models.CASCADE)
    # target = models.IntegerField(blank=True, default=0)
    # weightage = models.IntegerField(blank=True, default=0)
    
    def __str__(self):
        return self.template_name
    