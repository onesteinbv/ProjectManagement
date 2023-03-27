# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    supplier_company_id = fields.Many2one(
        "res.partner",
        "Supplier Company",
        related="partner_id.parent_id",
        domain="[('is_company', '=', True)]",
    )
