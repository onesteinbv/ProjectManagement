from odoo import fields, models


class Sheet(models.Model):
    _inherit = "hr_timesheet.sheet"

    state = fields.Selection(readonly=False)
    review_policy = fields.Selection(readonly=False)
    reviewer_id = fields.Many2one(readonly=False)
    create_date_old = fields.Datetime('Old Created on')
    create_uid_old = fields.Many2one('res.users', string='Old Created by')
    write_date_old = fields.Datetime('Old Updated on')
    write_uid_old = fields.Many2one('res.users', string='Old Updated by')
