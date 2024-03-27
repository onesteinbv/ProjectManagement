# Copyright 2024 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("analytic_line_ids.is_approved")
    def _compute_qty_delivered(self):
        return super(SaleOrderLine, self)._compute_qty_delivered()

    def _timesheet_compute_delivered_quantity_domain(self):
        """Non billable timesheets should not be considered"""
        domain = super(
            SaleOrderLine, self
        )._timesheet_compute_delivered_quantity_domain()
        domain += [("is_approved", "=", True)]
        return domain
