# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class SupplierLeavesReport(models.Model):
    _name = "supplier.leaves.report"
    _description = "Supplier Leaves Report"
    _auto = False
    _rec_name = "partner_id"

    partner_id = fields.Many2one("res.partner", "Team Member")
    date_from = fields.Date("Start Date")
    date_to = fields.Date("End Date")
    leave_category = fields.Selection(
        [
            ("supplier_leaves", "Team Leave"),
            ("public_holidays", "Public Holiday"),
            ("working_hours", "Working Hours"),
        ],
        "Leave Type",
    )

    @api.model
    def init(self):
        tools.drop_view_if_exists(self._cr, "supplier_leaves_report")
        self._cr.execute(
            """
            CREATE OR REPLACE VIEW supplier_leaves_report AS (
                SELECT
                CASE WHEN id = s.id
                     THEN 'supplier_leaves'
                END AS leave_category,
                s.id AS id,
                s.partner_id as partner_id,
                s.date_from as date_from,
                s.date_to as date_to
                FROM supplier_leaves as s
                GROUP BY s.id,s.partner_id,s.date_from,s.date_to
                )"""
        )
