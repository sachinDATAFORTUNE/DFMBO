from django.contrib import admin
from .models import Measure, Objective, Manager, Supervisor, Presale, ObjectiveTemplate, Template, Role

# Register your models here.

class ObjectiveAdminModel(admin.ModelAdmin):
    list_display=("objective_name","target1","target2","target3","weightage","actual","achieved","mbo_achievement","weighted_score","year","quarter","status")
        
class ObjectiveTemplateAdminModel(admin.ModelAdmin):
    list_display=("objective_name","measure","target1","weightage")
        


# admin.site.register(Employee)
admin.site.register(Measure)
admin.site.register(Objective, ObjectiveAdminModel)
# admin.site.register(Objective)
admin.site.register(Supervisor)
admin.site.register(Manager)
admin.site.register(Presale)
admin.site.register(Role)
admin.site.register(ObjectiveTemplate,ObjectiveTemplateAdminModel)
admin.site.register(Template)
