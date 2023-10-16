# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    supplier_company_id = fields.Many2one("res.partner",
                                          related="user_id.supplier_company_id",
                                          store=True,
                                          string="Supplier")
