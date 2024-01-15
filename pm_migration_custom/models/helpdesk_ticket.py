from odoo import fields, models, api


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    old_id = fields.Integer('Old Id')
    number = fields.Char(readonly=False)
    create_date_old = fields.Datetime('Old Created on')
    create_uid_old = fields.Many2one('res.users', string='Old Created by')
    write_date_old = fields.Datetime('Old Updated on')
    write_uid_old = fields.Many2one('res.users', string='Old Updated by')
