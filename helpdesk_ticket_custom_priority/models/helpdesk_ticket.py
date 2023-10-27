# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    priority = fields.Selection(selection_add=[('0', 'Deferred Priority'),
                                               ('1', 'Low Priority'),
                                               ('2', 'Medium Priority'),
                                               ('3', 'High Priority'),
                                               ('4', 'Critical Priority'),
                                               ('5', 'Blocker Priority'),
                                               ], default="0", string="Priority")
