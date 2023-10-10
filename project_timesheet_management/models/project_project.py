# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class ProjectProject(models.Model):
    _inherit = "project.project"

    def _compute_timesheet_inv_count(self):
        """
        Compute Timesheet Invoice Count
        """
        timesheet_invoice_obj = self.env["timesheet.invoice"]
        for project in self:
            project.timesheet_invoice_count = timesheet_invoice_obj.search_count(
                [("project_id", "=", project.id)]
            )

    resource_ids = fields.Many2many(
        "res.partner",
        "project_partner_rel",
        "project_id",
        "partner_id",
        "Resources",
        help="Resources working for this Project.",
    )
    timesheet_invoice_count = fields.Integer(
        compute="_compute_timesheet_inv_count",
        string="Number of Timesheet Invoices linked to this Project",
    )

    def action_view_invoices(self):
        """
        Open the Invoice Tree View

        Returns: Invoice Tree View.
        """
        action = self.env.ref(
            "project_timesheet_management.timesheet_invoice_action_form"
        )
        result = action.read()[0]
        if result.get("context"):
            action_context = safe_eval(action["context"], {"active_id": self.id})
            action_context["default_project_id"] = self.id
            result["context"] = action_context
        result["domain"] = "[('project_id','=', %s)]" % (self.id)
        return result
