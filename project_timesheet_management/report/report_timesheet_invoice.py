# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import _, api, models
from odoo.exceptions import UserError


class ReportTimesheetInvoice(models.AbstractModel):
    _name = "report.project_timesheet_management.report_timesheet_invoice"
    _description = "Report Timesheet Invoice"

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.env["timesheet.invoice"].browse(docids)
        if any(record.state not in ("approved", "completed") for record in records):
            raise UserError(
                _(
                    "Only Approved or Completed Timesheet "
                    "Invoices can be Printed."
                )
            )
        return {
            "doc_ids": docids,
            "doc_model": "timesheet.invoice",
            "docs": records,
            "data": data,
        }
