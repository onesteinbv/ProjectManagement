# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Project Timesheet Management",
    "version": "16.0.1.0.0",
    "summary": "A Module adds features to the Project Timesheet Management.",
    "author": """Serpent Consulting Services Pvt. Ltd.""",
    "website": "http://www.serpentcs.com",
    "category": "Project Budget Management",
    "license": "LGPL-3",
    "depends": ["project_scrum_agile"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rules.xml",
        "data/email_templates.xml",
        "views/project_project_view.xml",
        "views/analytic_line_view.xml",
        "wizard/timesheet_invoice_wiz_view.xml",
        "views/resource_calculation_view.xml",
        "views/res_users_view.xml",
        "views/res_partner_view.xml",
        "views/timesheet_invoice_view.xml",
        "report/report_timesheet_invoice.xml",
    ],
    "installable": True,
    "application": True,
}
