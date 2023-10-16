{
    "name": "Project Team Leave Management",
    "version": "16.0.1.0.0",
    "summary": "A Module adds features to the Project Team Leave Management.",
    "author": """Serpent Consulting Services Pvt. Ltd.""",
    "website": "http://www.serpentcs.com",
    "category": "Project Leave Management",
    "license": "AGPL-3",
    "depends": ["project_scrum_agile"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rules.xml",
        "views/supplier_leave_view.xml",
        "views/supplier_leaves_calc_report_view.xml",
        "views/res_partner_view.xml",
        "views/res_users_view.xml",
        "views/analytic_line_view.xml",
    ],
    "installable": True,
    "application": True,
}
