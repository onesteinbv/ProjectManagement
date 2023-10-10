from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TimesheetInvoice(models.Model):
    _inherit = "timesheet.invoice"

    def _check_budget(self):
        """
        Check and validate the Project Budget and Invoice amount
        Comparing the Invoice total with Revised Budget first, if not then
        with the Actual budget.
        Raises:
            UserError: If the project exceeds the Revised Budget
            UserError: If the project exceeds the Actual Budget
        """
        timesheet_inv_obj = self.env["timesheet.invoice"]
        for rec in self:
            project_invoices = timesheet_inv_obj.search(
                [
                    ("project_id", "=", rec.project_id.id),
                    ("state", "in", ("approved", "completed")),
                ]
            )
            total_amount = (
                    sum(invoice.total_amount for invoice in project_invoices)
                    + rec.total_amount
            )
            revised_budget = rec.project_id.revised_budget
            actual_budget = rec.project_id.actual_budget
            # Check Total amount is not greater than Revised budget
            # If not Revised budget: Check Total amount is not
            # greater than Actual budget
            if revised_budget and revised_budget < total_amount:
                raise UserError(
                    _(
                        "You can not enter the amount greater than "
                        "the Revised Budget of the Project"
                    )
                )
            elif actual_budget and not revised_budget and actual_budget < total_amount:
                raise UserError(
                    _(
                        "You can not enter the amount greater than "
                        "the Actual Budget of the Project"
                    )
                )
