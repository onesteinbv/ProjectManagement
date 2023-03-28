# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class ResourceCalculation(models.Model):
    _name = "resource.calculation"
    _description = "Resource Calculation"

    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):

        res = super(ResourceCalculation, self).read_group(
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )

        if "resource_amount" in fields:
            for line in res:
                if line.get("__domain"):
                    line["resource_amount"] = False
        return res

    timesheet_invoice_id = fields.Many2one(
        "timesheet.invoice",
        "Timesheet Invoice",
        ondelete="restrict",
        required=True,
        help="Timesheet Invoice related to \
                                           this resource calculation.",
    )
    resource_id = fields.Many2one(
        "res.partner",
        "Resource",
        required=True,
        ondelete="restrict",
        help="Resource Related to this Calculation.",
    )
    partner_id = fields.Many2one(
        related="timesheet_invoice_id.partner_id", store=True, readonly=True
    )
    worked_hours = fields.Float()
    resource_amount = fields.Float(
        copy=False, help="Amount to be charged for the resource."
    )
    total_amount = fields.Float(
        "Total Amount",
        compute="_compute_total_amount",
        store=True,
        help="worked_hours * resource_amount",
    )
    project_id = fields.Many2one(
        related="timesheet_invoice_id.project_id", store=True, readonly=True
    )
    invoice_date = fields.Date(
        "Invoice Date", related="timesheet_invoice_id.submit_date",
    )

    @api.onchange("resource_id")
    def _onchange_resource_id(self):
        """
        Calculate the Resource Amount on change of Resource.
        """
        self.resource_amount = self.resource_id.resource_amount if self.resource_id else 0

    @api.depends("worked_hours", "resource_amount")
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.worked_hours * rec.resource_amount
