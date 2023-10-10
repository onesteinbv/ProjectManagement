# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Project Management Dashboard',
    'version': '16.0.1.0.0',
    'summary': 'Provide summaries to manage project.',
    'author': '''Serpent Consulting Services Pvt. Ltd.''',
    'website': 'http://www.serpentcs.com',
    'category': 'Project Scrum Management',
    'license': "LGPL-3",
    'depends': [
        'project_budget_management',
        'project_team_leave_management',
        'project_scrum_agile_extended',
        'helpdesk_mgmt_project'
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_view.xml',
        'views/helpdesk_ticket_view.xml',
        'views/res_company_view.xml',
        'views/project_project_view.xml'
    ],
    'installable': True,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'management_dashboard/static/src/scss/management-admin.scss',
            'management_dashboard/static/src/js/management_dashbord.js',
            'management_dashboard/static/src/xml/management_dashboard.xml'
        ],

    },

}


