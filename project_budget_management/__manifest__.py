# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Project Budget Management",
    "version": "16.0.1.0.0",
    "summary": "A Module adds features to the Project Budget Management.",
    "author": """Serpent Consulting Services Pvt. Ltd.""",
    "website": "http://www.serpentcs.com",
    "category": "Project Budget Management",
    "license": "LGPL-3",
    "depends": ["project_timesheet_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/project_revised_budget_view.xml",
        "wizard/revise_budget_wiz_view.xml",
        "wizard/project_approve_wiz_view.xml",
        "wizard/extend_end_date_view.xml",
        "views/project_project_views.xml",
    ],
    "installable": True,
    "application": True,
}
