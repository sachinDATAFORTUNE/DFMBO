from django.contrib import admin
from django.urls import path, include
from employeeapp import urls
from django.contrib.auth import views as auth_views
from .views import (supervisor_dashboard,get_objective,login_view,addmanager,
                    get_presale,forgot_password,presale_for_manager_view,manager_mbo,presale_for_supervisor_view,
                    get_mbo, register, update_manager_objective_view,
                    update_supervisor_objective_view,addpresale_data_view,supervisor_manager_mbo,addobjective_view,
                    delete_manager,updating_objective_status_after_submitting_info_by_manager,updateManager,delete_objective,
                    sending_objective_to_manager,approving_objective_by_supervisor,accepted_objective_by_manager,rejected_objective_by_manager,create_copy_objective_view,
                    copy_of_objective,updating_objective_status_if_manager_rejects_it,updating_objective_status_if_manager_accepts_it,manager_dashboard,objective_template,
                    objective_template_by_id,delete_objective_template_by_ID,delete_template,create_template,add_objective_in_template,edit_objective_template_by_ID,logout_view)

urlpatterns = [
    path('addmanager', addmanager, name='add_manager_url'),
    path('forgotPassword', forgot_password, name='forgot_Password_url'),
    path('login', login_view, name='login_url'),
    path('manager', presale_for_manager_view, name='manager_url'),
    path('presale_supervisor', presale_for_supervisor_view, name='presale_supervisor_url'),
    path('manager_mbo', manager_mbo, name='manager_mbo_url'),
    path('supervisor_manager_mbo/<user_id>', supervisor_manager_mbo, name='supervisor_manager_mbo_url'),
    path('mbo', get_mbo, name='mbo_url'),
    path('objective', get_objective, name='objective_url'),
    path('presale', get_presale, name='presale_url'),
    path('supervisor', supervisor_dashboard, name='supervisor_url'),
    path('register', register, name='register_url'),
    path('update_manager_objective/<object_id>', update_manager_objective_view, name='update_manager_objective_url'),
    path('update_supervisor_objective/<object_id>/<user_id>', update_supervisor_objective_view, name='update_supervisor_objective_url'),
    path('addpresale/<user_id>', addpresale_data_view, name='addpresale_url'),
    path('addobjective', addobjective_view, name='addobjective_url'),
    path('deleteManager/<user_id>', delete_manager, name='delete_manager_url'),
    path('deleteObjective/<id>', delete_objective, name='delete_objective_url'),
    path('updatingObjectiveStatusAfterSubmittingInfoByManager/<user_id>',updating_objective_status_after_submitting_info_by_manager,name='updating_objective_status_after_submitting_info_by_manager_url'),
    path('update_manager/<user_id>',updateManager,name='update_manager_url'),
    path('sendingObjectiveToManager/<user_id>',sending_objective_to_manager,name='sending_objective_to_manager_url'),
    path('approvingObjectiveBySupervisor/<user_id>',approving_objective_by_supervisor,name='approving_objective_by_manager_url'),
    path('acceptedObjectiveByManager/<objective_id>',accepted_objective_by_manager,name='accepted_objective_by_manager_url'),
    path('rejectedObjectiveByManager/<objective_id>',rejected_objective_by_manager,name='rejected_objective_by_manager_url'),
    path('createCopyObjectiveView',create_copy_objective_view,name='create_copy_objective_view_url'),
    path('copyOfObjective',copy_of_objective,name='copy_of_objective_url'),
    path('updatingObjectiveStatusIfManagerRejectsIt',updating_objective_status_if_manager_rejects_it,name='updating_objective_status_if_manager_rejects_it_url'),
    path('updatingObjectiveStatusIfManagerAcceptsIt',updating_objective_status_if_manager_accepts_it,name='updating_objective_status_if_manager_accepts_it_url'),
    path('managerDashboard',manager_dashboard,name='manager_dashboard_url'), 
    path('objectiveTemplate',objective_template,name='objective_template_url'), 
    path('objectiveTemplateByID/<id>',objective_template_by_id,name='objective_template_by_id_url'), 
    path('deleteObjectiveTemplateByID/<template_id>/<objective_id>',delete_objective_template_by_ID,name='delete_objective_template_by_id_url'),
    path('deleteTemplate/<id>',delete_template,name='delete_template_url'),
    path('create_template',create_template,name='create_template_url'),
    path('<id>/add_objective_in_template',add_objective_in_template,name='add_objective_in_template_url'),
    path('edit_objective_template_by_ID/<template_id>/<objective_id>',edit_objective_template_by_ID,name='edit_objective_template_by_ID_url'),
    path('logout',logout_view,name='logout_view_url'),
     # Change Password
    path(
        'change-password/',
        auth_views.PasswordChangeView.as_view(
            template_name='employeeapp/change-password.html',
            success_url = 'mbo_url'
        ),
        name='change_password_url'
    ),
]
