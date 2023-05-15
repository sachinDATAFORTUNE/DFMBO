
from django.forms import PasswordInput, EmailInput, ModelForm

from .models import Objective, Measure, Presale, Manager, Supervisor
from django.contrib.auth.models import User       

        
class ObjectiveFormForManager(ModelForm):
    class Meta:
        model = Objective
        fields = ["actual"]

        
class ObjectiveFormForSupervisor(ModelForm):
    class Meta:
        model = Objective
        fields = ["objective_name","weightage","measure","target","actual","final","upper_percentage_for_weighted_score_calculation","lower_percentage_for_weighted_score_calculation","year","quarter"]
 
        
class AddObjectiveForm(ModelForm):
    class Meta:
        model = Objective
        fields = ["objective_name","measure","target","weightage"]
        
                
class MeasureForm(ModelForm):
    class Meta:
        model = Measure
        fields = "__all__"

        
class PresaleForm(ModelForm):
    class Meta:
        model = Presale
        fields = ["date","client_name","company_name","project","technology","status"]
        
        
class UpdateManagerForm(ModelForm):
    class Meta:
        model = Manager
        fields = ["employee_id","user"]
        # fields = "__all__"
        
        
class createMeasureForm(ModelForm):
    class Meta:
        model = Measure
        fields = "__all__"