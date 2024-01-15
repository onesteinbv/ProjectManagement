from odoo import fields, models, api


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    old_res_id = fields.Integer('Old Resource Id')
    res_model = fields.Char(readonly=False)
    res_id = fields.Many2oneReference(readonly=False)
    create_date_old = fields.Datetime('Old Created on')
    create_uid_old = fields.Many2one('res.users', string='Old Created by')
    write_date_old = fields.Datetime('Old Updated on')
    write_uid_old = fields.Many2one('res.users', string='Old Updated by')

    @api.model_create_multi
    def create(self, values_list):
        for vals in values_list:
            if vals.get("old_res_id", False) and vals.get("res_model") and not vals.get("res_id", False):
                vals["res_id"] = self.env[vals.get("res_model")].search([("old_id", "=", vals.get("old_res_id"))],
                                                                        limit=1).id
        return super().create(values_list)