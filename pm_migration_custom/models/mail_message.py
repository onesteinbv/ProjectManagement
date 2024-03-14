from odoo import fields, models, api


class MailMessage(models.Model):
    _inherit = "mail.message"
    _order = "date desc"

    old_res_id = fields.Integer('Old Resource Id')
    create_date_old = fields.Datetime('Old Created on')
    create_uid_old = fields.Many2one('res.users', string='Old Created by')
    write_date_old = fields.Datetime('Old Updated on')
    write_uid_old = fields.Many2one('res.users', string='Old Updated by')

    @api.model_create_multi
    def create(self, values_list):
        for vals in values_list:
            if vals.get("old_res_id", False) and vals.get("model") and not vals.get("res_id", False):
                vals["res_id"] = self.env[vals.get("model")].search([("old_id", "=", vals.get("old_res_id"))],
                                                                    limit=1).id
            if 'body' in vals and not vals.get('body'):
                vals.pop('body')
        return super().create(values_list)


class MailTracking(models.Model):
    _inherit = "mail.tracking.value"

    field = fields.Many2one(readonly=0)
    field_desc = fields.Char(readonly=0)

    old_value_integer = fields.Integer(readonly=0)
    old_value_float = fields.Float(readonly=0)
    old_value_monetary = fields.Float(readonly=0)
    old_value_char = fields.Char(readonly=0)
    old_value_text = fields.Text(readonly=0)
    old_value_datetime = fields.Datetime(readonly=0)

    new_value_integer = fields.Integer(readonly=0)
    new_value_float = fields.Float(readonly=0)
    new_value_monetary = fields.Float(readonly=0)
    new_value_char = fields.Char(readonly=0)
    new_value_text = fields.Text(readonly=0)
    new_value_datetime = fields.Datetime(readonly=0)

    currency_id = fields.Many2one(readonly=0)
    mail_message_id = fields.Many2one(required=False)
    tracking_sequence = fields.Integer('Tracking field sequence', readonly=0, default=100)
    field_model = fields.Char('Field Model')
    field_name = fields.Char('Field Name')

    @api.model_create_multi
    def create(self, values_list):
        for vals in values_list:
            if vals.get("field_model", False) and vals.get("field_name") and not vals.get("field", False):
                vals["field"] = self.env["ir.model.fields"].search(
                    [("name", "=", vals.get("field_name")), ('model_id.model', '=', vals.get("field_model"))],
                    limit=1).id
        return super().create(values_list)