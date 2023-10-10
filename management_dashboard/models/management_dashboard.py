# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).


import time
from collections import defaultdict
from datetime import datetime

from odoo import api, models


class ManagementDashboard(models.Model):
    _name = 'management.dashboard'
    _description = "Project Management Dashboard"

    @api.model
    def get_task_chart_data(self):
        """
        Map the Stage Colour and Name to id

        Returns:
            dictionary -- stage_id as key and details as value
        """
        task_obj = self.env['project.task']
        task_rec = task_obj.search([])
        groups = defaultdict(list)

        for obj in task_rec:
            groups[obj.stage_id].append(obj)
        result = {}
        for rec in groups.items():
            result.update({
                rec[0].name: {
                    'count': len(rec[1]),
                    'color': rec[0].color,
                    'name': rec[0].name,
                }})
        return result

    @api.model
    def get_config_values(self):
        """
        To get the Colour value for dashboard.
        Using sudo env to bypass the access right.
        Returns:
            dictionary -- Dictionary of config colours.
        """
        result = self.env['res.config.settings'].sudo().get_values()
        return {
            'color_close_state': result.get('color_close_state', False),
            'color_control_state': result.get('color_control_state', False),
            'color_execute_state': result.get('color_execute_state', False),
            'color_init_state': result.get('color_init_state', False),
            'color_plan_state': result.get('color_plan_state', False),
            'card_header_color': result.get('card_header_color', False),
        }

    @api.model
    def get_color_code(self, project):
        # 0:Green, 1:Orange, 2:Red
        open_task = 0
        open_issue = 0
        spent_budget = 0
        pending_invoice = 0
        # ('date_start', '>=', self._context.get('start_date')),
        # ('date_start', '<=', self._context.get('end_date')),
        project_tasks = self.env['project.task'].search(
            [('project_id', '=', project['id']),
             ('stage_id.name',
                'not in',
                ("Done", "Completed", "Approval",
                 "Canceled", "Closure", "Release",
                 "Implementation")),
             ('date_end', '=', False)])

        today_date = datetime.strptime(
            time.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
        for task in project_tasks:
            if task.schedule_date:
                schedule_date = datetime.strptime(
                    str(task.schedule_date), '%Y-%m-%d %H:%M:%S').date()
                daysdiff = (schedule_date - today_date).days
                if daysdiff <= 1:
                    open_task = 2
                if 7 >= daysdiff > 1 and open_task != 2:
                    open_task = 1
                if daysdiff > 7 and open_task not in (2, 1):
                    open_task = 0

        project_issues = self.env['helpdesk.ticket'].with_context(
            view_project_issues=1).search([
                ('stage_id.closed', '!=', True),
                ('project_id.id', '=', project['id']),
                ('closed_date', '=', False)])
        for issue in project_issues or []:
            if ((int(int(issue.ticket_aging)) > 30 and issue.priority == '0') or
                    (int(issue.ticket_aging) > 10 and issue.priority == '1') or
                    (int(issue.ticket_aging) > 2 and issue.priority in
                        ('2', '3'))):
                open_issue = 2
            if ((10 < int(issue.ticket_aging) <= 30 and
                 issue.priority == '0') or
                    (2 < int(issue.ticket_aging) <= 10 and
                     issue.priority == '1') or
                    (0 < int(issue.ticket_aging) <= 2 and
                     issue.priority in ('2', '3')) and
                    open_issue != 2):
                open_issue = 1
            if ((int(issue.ticket_aging) <= 10 and issue.priority == '0') or
                    (int(issue.ticket_aging) <= 2 and issue.priority == '1') or
                    (int(issue.ticket_aging) == 0 and issue.priority in
                        ('2', '3')) and
                    open_issue not in (2, 1)):
                open_issue = 0

        budget = 0
        if project['spent_budget'] > 0 and project['actual_budget'] > 0:
            budget = ((project['spent_budget'] - project['actual_budget'])/project['actual_budget']) * 100

        if budget > 30:
            spent_budget = 2
        elif 10 < budget <= 30:
            spent_budget = 1
        elif budget <= 10:
            spent_budget = 0

        invoices = self.env['timesheet.invoice'].search([
            ('project_id', '=', project['id']),
            ('state', 'in', ('draft', 'confirm', 'pre-approved'))])

        for inv in invoices or []:
            if int(inv.timesheet_inv_age) > 30:
                pending_invoice = 2
            elif 10 < int(inv.timesheet_inv_age) < 30 and pending_invoice != 2:
                pending_invoice = 1
            elif int(inv.timesheet_inv_age) < 10 and pending_invoice not in (2, 1):
                pending_invoice = 0
        return {
                'spent_budget': spent_budget,
                'pending_invoice': pending_invoice,
                'open_task': open_task,
                'open_issue': open_issue}

    @api.model
    def get_treeview_id(self, view):
        return self.env.ref(view).id,
