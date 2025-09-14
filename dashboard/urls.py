from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic import TemplateView

app_name = 'dashboard'

urlpatterns = [
    # Auth
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),

    # Dashboard pages
    path('', TemplateView.as_view(template_name='dashboard/home.html'), name='home'),
    path('users/', views.users_list, name='users'),
    path('roles/', views.roles_list, name='roles'),
    path('sessions/', views.sessions_list, name='sessions'),
    path('audit/', views.audit_logs, name='audit'),
    # Schema pages (disable if heavy or missing)
    # path('schema/', views.database_schema, name='schema'),
    # path('schema/excel/', views.download_schema_excel, name='schema_excel'),
    # path('schema/excel-single/', views.download_schema_excel_single, name='schema_excel_single'),
    # path('schema/csv/', views.download_schema_csv, name='schema_csv'),
    # path('er/', views.er_diagram_page, name='er'),
    
    # Student Management
    path('students/', views.students_list, name='students'),
    path('students/<uuid:student_id>/', views.student_detail, name='student_detail'),
    path('custom-fields/', views.custom_fields_list, name='custom_fields'),
    path('student-login/', views.student_login_page, name='student_login'),
    path('student-sessions/', views.student_sessions, name='student_sessions'),
    path('student-import/', views.student_import_page, name='student_import'),
    path('student-import/process/', views.student_import_process, name='student_import_process'),
    path('download-template/', views.download_template, name='download_template'),
    
    # Student Division Management
    path('students/divisions/', views.student_divisions, name='student_divisions'),
    path('students/assignments/', views.student_assignments, name='student_assignments'),
    path('students/division-statistics/', views.student_division_statistics, name='student_division_statistics'),
    path('api/students/bulk-assign/', views.bulk_assign_students, name='bulk_assign_students'),
    
    # Faculty Management
    path('faculty/', views.faculty_list, name='faculty_list'),
    path('faculty/create/', views.faculty_create, name='faculty_create'),
    path('faculty/<uuid:faculty_id>/', views.faculty_detail, name='faculty_detail'),
    path('faculty/<uuid:faculty_id>/update/', views.faculty_update, name='faculty_update'),
    path('faculty/performance/', views.faculty_performance_stats, name='faculty_performance'),
    path('faculty/leaves/', views.faculty_leave_stats, name='faculty_leaves'),
    path('faculty/documents/', views.faculty_document_list, name='faculty_documents'),
    path('faculty/custom-fields/', views.faculty_custom_fields_list, name='faculty_custom_fields'),
    path('faculty/custom-fields/create/', views.faculty_custom_field_create, name='faculty_custom_field_create'),
    path('faculty/custom-fields/<uuid:field_id>/update/', views.faculty_custom_field_update, name='faculty_custom_field_update'),
    path('faculty/custom-fields/<uuid:field_id>/delete/', views.faculty_custom_field_delete, name='faculty_custom_field_delete'),
    
    # Academics Management
    path('academics/', views.academics_dashboard, name='academics_dashboard'),
    path('academics/courses/', views.academics_courses_list, name='academics_courses'),
    path('academics/courses/<int:course_id>/', views.academics_course_detail, name='academics_course_detail'),
    path('academics/syllabi/', views.academics_syllabi_list, name='academics_syllabi'),
    path('academics/syllabi/<int:syllabus_id>/', views.academics_syllabus_detail, name='academics_syllabus_detail'),
    path('academics/timetables/', views.academics_timetables_list, name='academics_timetables'),
    path('academics/timetables/<int:timetable_id>/', views.academics_timetable_detail, name='academics_timetable_detail'),
    path('academics/enrollments/', views.academics_enrollments_list, name='academics_enrollments'),
    path('academics/enrollments/<int:enrollment_id>/', views.academics_enrollment_detail, name='academics_enrollment_detail'),
    path('academics/calendar/', views.academics_calendar_list, name='academics_calendar'),
    path('academics/calendar/<int:event_id>/', views.academics_calendar_detail, name='academics_calendar_detail'),
    
    # Academics API Endpoints (removed)
    
    # Facilities Management
    path('facilities/', views.facilities_dashboard, name='facilities_dashboard'),
    
    # Enrollment Management
    path('enrollment/', views.enrollment_dashboard, name='enrollment_dashboard'),
    path('enrollment/rules/', views.enrollment_rules_list, name='enrollment_rules'),
    path('enrollment/rules/<int:rule_id>/', views.enrollment_rule_detail, name='enrollment_rule_detail'),
    path('enrollment/course-assignments/', views.course_assignments_list, name='course_assignments'),
    path('enrollment/course-assignments/<int:assignment_id>/', views.course_assignment_detail, name='course_assignment_detail'),
    path('enrollment/faculty-assignments/', views.faculty_assignments_list, name='faculty_assignments'),
    path('enrollment/faculty-assignments/<int:assignment_id>/', views.faculty_assignment_detail, name='faculty_assignment_detail'),
    path('enrollment/plans/', views.enrollment_plans_list, name='enrollment_plans'),
    path('enrollment/plans/<int:plan_id>/', views.enrollment_plan_detail, name='enrollment_plan_detail'),
    path('enrollment/requests/', views.enrollment_requests_list, name='enrollment_requests'),
    path('enrollment/requests/<int:request_id>/', views.enrollment_request_detail, name='enrollment_request_detail'),
    path('enrollment/waitlist/', views.waitlist_entries_list, name='waitlist_entries'),
    path('enrollment/waitlist/<int:entry_id>/', views.waitlist_entry_detail, name='waitlist_entry_detail'),
    path('enrollment/departments/', views.departments_list, name='departments'),
    path('enrollment/departments/<int:department_id>/', views.department_detail, name='department_detail'),
    path('enrollment/programs/', views.academic_programs_list, name='academic_programs'),
    path('enrollment/programs/<int:program_id>/', views.academic_program_detail, name='academic_program_detail'),
    path('enrollment/sections/', views.course_sections_list, name='course_sections'),
    path('enrollment/sections/<int:section_id>/', views.course_section_detail, name='course_section_detail'),

    # Attendance Management
    path('attendance/sessions/', views.attendance_sessions, name='attendance_sessions'),
    path('attendance/sessions/<int:session_id>/', views.attendance_session_detail, name='attendance_session_detail'),
    path('attendance/sessions/<int:session_id>/mark/', views.attendance_mark, name='attendance_mark'),
    path('attendance/generate/', views.attendance_generate_sessions, name='attendance_generate_sessions'),
    
    # API dashboard endpoints (removed)
    
    # Exam Management
    path('exams/', views.exams_dashboard, name='exams_dashboard'),
    
    # Fee Management
    path('fees/', views.fees_dashboard, name='fees_dashboard'),
    path('fees/categories/', views.fees_categories_list, name='fees_categories_list'),
    path('fees/structures/', views.fees_structures_list, name='fees_structures_list'),
    path('fees/structures/<uuid:structure_id>/', views.fees_structure_detail, name='fees_structure_detail'),
    path('fees/student-fees/', views.fees_student_fees_list, name='fees_student_fees_list'),
    path('fees/student-fees/<uuid:student_fee_id>/', views.fees_student_fee_detail, name='fees_student_fee_detail'),
    path('fees/payments/', views.fees_payments_list, name='fees_payments_list'),
    path('fees/payments/<uuid:payment_id>/', views.fees_payment_detail, name='fees_payment_detail'),
    path('fees/waivers/', views.fees_waivers_list, name='fees_waivers_list'),
    path('fees/discounts/', views.fees_discounts_list, name='fees_discounts_list'),
    path('fees/receipts/', views.fees_receipts_list, name='fees_receipts_list'),
    path('fees/receipts/<uuid:receipt_id>/', views.fees_receipt_detail, name='fees_receipt_detail'),
    path('fees/reports/', views.fees_reports, name='fees_reports'),
    path('fees/api/', views.fees_api_endpoints, name='fees_api_endpoints'),
    path('exams/sessions/', views.exams_sessions_list, name='exams_sessions'),
    path('exams/sessions/<uuid:session_id>/', views.exams_session_detail, name='exams_session_detail'),
    path('exams/schedules/', views.exams_schedules_list, name='exams_schedules'),
    path('exams/schedules/<uuid:schedule_id>/', views.exams_schedule_detail, name='exams_schedule_detail'),
    path('exams/rooms/', views.exams_rooms_list, name='exams_rooms'),
    path('exams/rooms/<uuid:room_id>/', views.exams_room_detail, name='exams_room_detail'),
    path('exams/registrations/', views.exams_registrations_list, name='exams_registrations'),
    path('exams/registrations/<uuid:registration_id>/', views.exams_registration_detail, name='exams_registration_detail'),
    path('exams/hall-tickets/', views.exams_hall_tickets_list, name='exams_hall_tickets'),
    path('exams/hall-tickets/<uuid:ticket_id>/', views.exams_hall_ticket_detail, name='exams_hall_ticket_detail'),
    path('exams/attendance/', views.exams_attendance_list, name='exams_attendance'),
    path('exams/attendance/<uuid:attendance_id>/', views.exams_attendance_detail, name='exams_attendance_detail'),
    path('exams/results/', views.exams_results_list, name='exams_results'),
    path('exams/results/<uuid:result_id>/', views.exams_result_detail, name='exams_result_detail'),
    path('exams/dues/', views.exams_dues_list, name='exams_dues'),
    path('exams/dues/<uuid:due_id>/', views.exams_due_detail, name='exams_due_detail'),
    path('exams/violations/', views.exams_violations_list, name='exams_violations'),
    path('exams/violations/<uuid:violation_id>/', views.exams_violation_detail, name='exams_violation_detail'),
    path('exams/staff-assignments/', views.exams_staff_assignments_list, name='exams_staff_assignments'),
    path('exams/staff-assignments/<uuid:assignment_id>/', views.exams_staff_assignment_detail, name='exams_staff_assignment_detail'),
    path('exams/room-allocations/', views.exams_room_allocations_list, name='exams_room_allocations'),
    path('exams/room-allocations/<uuid:allocation_id>/', views.exams_room_allocation_detail, name='exams_room_allocation_detail'),
    
    # Mentoring Dashboard
    path('mentoring/', views.mentoring_dashboard, name='mentoring_dashboard'),
    path('mentoring/mentorships/', views.mentoring_mentorships, name='mentoring_mentorships'),
    path('mentoring/projects/', views.mentoring_projects, name='mentoring_projects'),
    path('mentoring/meetings/', views.mentoring_meetings, name='mentoring_meetings'),
    path('mentoring/feedback/', views.mentoring_feedback, name='mentoring_feedback'),
    
    # API Testing dashboard routes (removed)

    # Placements Dashboard
    path('placements/', views.placements_dashboard, name='placements_dashboard'),
    path('placements/companies/', views.placements_companies, name='placements_companies'),
    path('placements/jobs/', views.placements_jobs, name='placements_jobs'),
    path('placements/applications/', views.placements_applications, name='placements_applications'),
    path('placements/drives/', views.placements_drives, name='placements_drives'),
    path('placements/rounds/', views.placements_rounds, name='placements_rounds'),
    path('placements/offers/', views.placements_offers, name='placements_offers'),

    # Grads & Marks Dashboard
    path('grads/', views.grads_dashboard, name='grads_dashboard'),
    path('grads/grade-scales/', views.grads_grade_scales, name='grads_grade_scales'),
    path('grads/terms/', views.grads_terms, name='grads_terms'),
    path('grads/results/', views.grads_results, name='grads_results'),
    path('grads/bulk-entry/', views.grads_bulk_entry, name='grads_bulk_entry'),
    path('grads/ajax/sections/', views.grads_sections_api, name='grads_sections_api'),
    path('grads/ajax/students/', views.grads_students_api, name='grads_students_api'),
    path('grads/transcript/<uuid:student_id>/', views.grads_transcript, name='grads_transcript'),

    # R&D Dashboard
    path('rnd/', views.rnd_dashboard, name='rnd_dashboard'),
    path('rnd/projects/', views.rnd_projects, name='rnd_projects'),
    path('rnd/projects/<int:project_id>/', views.rnd_project_detail, name='rnd_project_detail'),
    path('rnd/researchers/', views.rnd_researchers, name='rnd_researchers'),
    path('rnd/researchers/<int:researcher_id>/', views.rnd_researcher_detail, name='rnd_researcher_detail'),
    path('rnd/grants/', views.rnd_grants, name='rnd_grants'),
    path('rnd/publications/', views.rnd_publications, name='rnd_publications'),
    path('rnd/patents/', views.rnd_patents, name='rnd_patents'),
    path('rnd/datasets/', views.rnd_datasets, name='rnd_datasets'),
    path('rnd/collaborations/', views.rnd_collaborations, name='rnd_collaborations'),

    # Transportation Dashboard
    path('transport/', views.transport_dashboard, name='transport_dashboard'),
    path('transport/vehicles/', views.transport_vehicles, name='transport_vehicles'),
    path('transport/drivers/', views.transport_drivers, name='transport_drivers'),
    path('transport/routes/', views.transport_routes, name='transport_routes'),
    path('transport/stops/', views.transport_stops, name='transport_stops'),
    path('transport/assignments/', views.transport_assignments, name='transport_assignments'),
    path('transport/schedules/', views.transport_schedules, name='transport_schedules'),
    path('transport/passes/', views.transport_passes, name='transport_passes'),
    path('transport/vehicles/create/', views.transport_vehicle_create, name='transport_vehicle_create'),
    path('transport/drivers/create/', views.transport_driver_create, name='transport_driver_create'),
    path('transport/routes/create/', views.transport_route_create, name='transport_route_create'),
    path('transport/stops/create/', views.transport_stop_create, name='transport_stop_create'),
    path('transport/assignments/create/', views.transport_assignment_create, name='transport_assignment_create'),
    path('transport/schedules/create/', views.transport_schedule_create, name='transport_schedule_create'),
    path('transport/passes/create/', views.transport_pass_create, name='transport_pass_create'),
    
    # Feedback Management
    path('feedback/', views.feedback_dashboard, name='feedback_dashboard'),
    path('feedback/items/', views.feedback_items_list, name='feedback_items_list'),
    path('feedback/items/create/', views.feedback_item_create, name='feedback_item_create'),
    path('feedback/items/<int:item_id>/', views.feedback_item_detail, name='feedback_item_detail'),

    # Open Requests (UI)
    # Open Requests removed
    
    # Assignments Management
    path('assignments/', views.assignments_dashboard, name='assignments_dashboard'),
    path('assignments/list/', views.assignments_list, name='assignments_list'),
    path('assignments/create/', views.assignment_create, name='assignment_create'),
    path('assignments/<uuid:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<uuid:assignment_id>/edit/', views.assignment_edit, name='assignment_edit'),
    path('assignments/<uuid:assignment_id>/submit/', views.assignment_submit, name='assignment_submit'),
    path('assignments/submissions/<uuid:submission_id>/grade/', views.assignment_grade, name='assignment_grade'),
    path('assignments/categories/', views.assignment_categories, name='assignment_categories'),
    path('assignments/templates/', views.assignment_templates, name='assignment_templates'),
    path('assignments/statistics/', views.assignment_statistics, name='assignment_statistics'),
    
    # Assignments AJAX Endpoints
    path('assignments/ajax/file-upload/', views.assignment_file_upload, name='assignment_file_upload'),
    path('assignments/ajax/<uuid:assignment_id>/publish/', views.assignment_publish_ajax, name='assignment_publish_ajax'),
    path('assignments/ajax/<uuid:assignment_id>/close/', views.assignment_close_ajax, name='assignment_close_ajax'),
    path('assignments/ajax/<uuid:assignment_id>/comment/', views.assignment_comment_ajax, name='assignment_comment_ajax'),
    path('assignments/ajax/stats/', views.assignment_stats_ajax, name='assignment_stats_ajax'),
    path('assignments/ajax/autocomplete/', views.assignment_autocomplete, name='assignment_autocomplete'),
            path('assignments/ajax/bulk-action/', views.assignment_bulk_action, name='assignment_bulk_action'),
            path('assignments/ajax/filter-students/', views.filter_students_ajax, name='filter_students_ajax'),
]
