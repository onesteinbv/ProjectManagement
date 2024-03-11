# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models, _


class ProjectProject(models.Model):
    _inherit = "project.project"

    # def _compute_issues_count(self):
    #     """
    #     Compute issue_count, open_issues_count and close_issues_count
    #     """
    #     helpdesk_ticket_obj = self.env["helpdesk.ticket"]
    #     for project in self:
    #         ticket_count = helpdesk_ticket_obj.with_context(
    #             view_project_issues=1).search([
    #             ("project_id", "=", project.id),
    #             ])
    #         project.open_issues_count = len(ticket_count.filtered(
    #             lambda s: not s.closed))
    #         # project.close_issues_count = len(ticket_count.filtered(
    #         #     lambda s: s.closed))

    def _compute_tasks_count(self):
        """
        Compute tasks_count, open_tasks_count and close_tasks_count.
        """
        for project in self:
            project.open_tasks_count = len(project.task_ids)
            # project.close_tasks_count = len(task_count.filtered(
            #     lambda s: s.date_end and s.stage_id.fold))


    # To be shown on Dashboard
    # open_issues_count = fields.Integer(compute="_compute_issues_count")
    # close_issues_count = fields.Integer(
    #     compute="_compute_issues_count")
    open_tasks_count = fields.Integer(
        compute="_compute_tasks_count")
    # close_tasks_count = fields.Integer(compute="_compute_tasks_count")
    project_phase_stage = fields.Char(related="stage_id.name", string="Project Stage")
    forecast_up_range = fields.Float(related="company_id.forecast_up_range", string="Forecast Up Rang %")
    forecast_low_range = fields.Float(related="company_id.forecast_low_range", string="Forecast Low Rang %")

    @api.model
    def get_total_project_cost_for_vendors(self,project_ids):
        partner_dict = {}
        projects = self.env['project.project'].browse(project_ids)
        analytic_account_ids = projects.mapped('analytic_account_id').ids
        query = self.env['account.move.line'].sudo()._search(
            [('move_id.move_type', 'in', self.env['account.move'].get_purchase_types()),
             ('price_total', '!=', 0),
             ('parent_state', '=', 'posted'),
             ('is_downpayment', '=', False),('move_id.partner_id','!=',False)])
        query.add_where('account_move_line.analytic_distribution ?| %s',
                        [[str(analytic_account_id) for analytic_account_id in analytic_account_ids]],)
        query_string, query_param = query.select('price_total','account_move_line.partner_id')
        self._cr.execute(query_string, query_param)
        invoices_move_line_read = self._cr.dictfetchall()
        if invoices_move_line_read:
            partner_ids = {iml['partner_id'] for iml in invoices_move_line_read}
            partner_recs = self.env['res.partner'].search_read(
                domain=[('id', 'in', list(partner_ids))],
                fields=['name'],
            )
            partners = {partner['id'] : partner['name'] for partner in partner_recs}
            for line in invoices_move_line_read:
                partner_id = line['partner_id']
                if partner_id in partner_dict:
                    partner_dict[partner_id][1] += line['price_total']
                else:
                    partner_dict.update({partner_id:[partners[partner_id],line['price_total']]})
        sorted_partners_by_amounts = dict(sorted(partner_dict.items(), key=lambda x: x[1][1], reverse=True))
        return sorted_partners_by_amounts

    @api.model
    def action_view_open_vendor_bills(self,project_id):
        project = self.env['project.project'].browse(project_id)
        query = self.env['account.move.line']._search(
            [('move_id.move_type', 'in', self.env['account.move'].get_purchase_types()), ('move_id.state', '=', 'draft')])
        query.order = None
        query.add_where('analytic_distribution ? %s', [str(project.analytic_account_id.id)])
        query_string, query_param = query.select('DISTINCT account_move_line.move_id')
        self._cr.execute(query_string, query_param)
        move_ids = [line.get('move_id') for line in self._cr.dictfetchall()]
        result = {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "domain": [('id', 'in', move_ids)],
            "context": {"create": False, 'default_move_type': 'in_invoice'},
            "name": _("Vendor Bills"),
            'view_mode': 'tree,form',
            'views': [[False, 'list'], [False, 'form']],
        }
        return result

    @api.model
    def action_view_open_timesheet_sheets(self, project_id):
        project = self.env['project.project'].browse(project_id)
        sheet_ids = [timesheet.sheet_id.id for timesheet in project.timesheet_ids if
                     timesheet.sheet_state and timesheet.sheet_state != 'done']
        result = {
            "type": "ir.actions.act_window",
            "res_model": "hr_timesheet.sheet",
            "domain": [('id', 'in', sheet_ids)],
            "context": {"create": False},
            "name": _("Timesheet Sheets"),
            'view_mode': 'tree,form',
            'views': [[False, 'list'], [False, 'form']],
        }
        return result