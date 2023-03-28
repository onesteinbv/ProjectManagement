# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    resource_amount = fields.Float(
        copy=False, help="Amount to be charged for the resource."
    )
