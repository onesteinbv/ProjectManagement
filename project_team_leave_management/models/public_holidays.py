# See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError


class PublicHolidays(models.Model):
    _name = 'public.holidays'
    _description = 'Public Holidays'

    @api.depends('date')
    def _compute_weekday(self):
        """Compute weekday based on the date."""
        for day in self:
            day.weekday = ''
            if day.date:
                day.weekday = day.date.strftime("%A")

    partner_id = fields.Many2one('res.partner', string='Supplier')
    date = fields.Date('Date', required=True)
    weekday = fields.Char(compute='_compute_weekday', string='Day')
    reason = fields.Char('Reason')

    @api.constrains('date')
    def _check_holiday(self):
        """
        Check for the overlapping record

        Raises:
            ValidationError: If there's an overlapping record.
        """
        for holiday in self:
            domain = [
                ('date', '=', holiday.date),
                ('partner_id', '=', holiday.partner_id.id),
                ('id', '!=', holiday.id),
            ]
            if self.search_count(domain):
                raise ValidationError(_(
                    "Already, That day has been declared as holiday!"))
