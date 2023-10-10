# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    def _compute_issues_count(self):
        """
        Compute issue_count, open_issues_count and close_issues_count
        """
        helpdesk_ticket_obj = self.env["helpdesk.ticket"]
        for project in self:
            ticket_count = helpdesk_ticket_obj.with_context(
                view_project_issues=1).search([
                ("project_id", "=", project.id),
                ])
            project.open_issues_count = len(ticket_count.filtered(
                lambda s: not s.closed))
            project.close_issues_count = len(ticket_count.filtered(
                lambda s: s.closed))

    def _compute_tasks_count(self):
        """
        Compute tasks_count, open_tasks_count and close_tasks_count.
        """
        task_obj = self.env["project.task"]
        for project in self:
            task_count = task_obj.search([
                ("project_id", "=", project.id)])
            project.open_tasks_count = len(task_count.filtered(
                lambda s: not s.date_end and not s.stage_id.fold))
            project.close_tasks_count = len(task_count.filtered(
                lambda s: s.date_end and s.stage_id.fold))

    def _compute_resource_count(self):
        for project in self:
            project.resource_count = len(project.resource_ids.filtered(
                lambda resource: not resource.is_company))

    # To be shown on Dashboard
    open_issues_count = fields.Integer(compute="_compute_issues_count")
    close_issues_count = fields.Integer(
        compute="_compute_issues_count")
    open_tasks_count = fields.Integer(
        compute="_compute_tasks_count")
    close_tasks_count = fields.Integer(compute="_compute_tasks_count")
    resource_count = fields.Integer(compute="_compute_resource_count")
    project_phase_stage = fields.Char(related="stage_id.name", string="Project Stage")
    forecast_up_range = fields.Float(related="company_id.forecast_up_range", string="Forecast Up Rang %")
    forecast_low_range = fields.Float(related="company_id.forecast_low_range", string="Forecast Low Rang %")
