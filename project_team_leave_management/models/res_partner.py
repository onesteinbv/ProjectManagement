# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _compute_total_users(self):
        """
        Compute the Total number of Users of a partner.
        """
        for partner in self:
            partner.total_users = len(partner.user_ids)

    public_holiday_ids = fields.One2many(
        "public.holidays", "partner_id", "Public Holidays"
    )
    total_users = fields.Integer(compute="_compute_total_users", string="Total Users")
    resource_calendar_id = fields.Many2one("resource.calendar", string="Working Hours")

    def action_view_partner_users(self):
        """
        Open a Form(If there's only one user) or
        Tree(If more then one user) view of res.users
        """
        self.ensure_one()
        action = self.env.ref("base.action_res_users")
        if self.total_users == 1:
            action["views"] = [(self.env.ref("base.view_users_form").id, "form")]
            action["res_id"] = self.user_ids.ids[0]
        result = action.read()[0]
        result["domain"] = "[('partner_id','=', %s)]" % (self.id)
        return result
