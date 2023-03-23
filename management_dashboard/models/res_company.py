# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    forecast_up_range = fields.Float("Forecast Up Rang %", default='120')
    forecast_low_range = fields.Float("Forecast Low Rang %", default='110')
