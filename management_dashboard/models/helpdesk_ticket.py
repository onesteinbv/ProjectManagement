# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    ticket_aging = fields.Char(
        "Aging", compute="_compute_ticket_age",
        store=False, help="Support Ticket Age (in days).")

    # Keeping for future scope
    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     ctx = self.env.context.copy()
    #     if ctx.get('view_project_issues', False):
    #         args.append(('project_id', '!=', False))
    #     else:
    #         args.append(('project_id', '=', False))
    #     if self.env.user.has_group(
    #             "helpdesk_mgmt.group_helpdesk_user_team") and not self.env.user.has_group(
    #             "helpdesk_mgmt.group_helpdesk_manager"):
    #         args += ['|', ('user_id', '=', self.env.user.id), ('alias_user_id', '=', self.env.user.id)]
    #
    #     return super(HelpdeskTicket, self).search(
    #         args, offset=offset, limit=limit, order=order, count=count)

    def _compute_ticket_age(self):
        """
        This method is to calculate age for
        tickets which are not in resolved / closed state.
        :return: Ticket Age in days(Integer)
        """
        current_datetime = fields.Datetime.now()
        for ticket in self:
            ticket_aging = 0
            closed_date = ticket.closed_date
            creation_date = ticket.create_date
            if ticket.stage_id.closed and closed_date:
                difference = closed_date - creation_date
                ticket_aging = difference.days
            elif creation_date:
                difference = current_datetime - creation_date
                ticket_aging = difference.days
            ticket.ticket_aging = ticket_aging
