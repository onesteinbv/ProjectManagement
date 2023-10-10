# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from datetime import timedelta

from odoo import api, fields, models


class ProjectProjectStage(models.Model):
    _inherit = "project.project.stage"

    is_close = fields.Boolean("Closing Stage")


class ProjectProject(models.Model):
    _inherit = "project.project"

    def _compute_spent_budget(self):
        """
        Compute the Spent Budget of Project
        """
        timesheet_invoice_obj = self.env["timesheet.invoice"]
        for project in self:
            timesheet_invoice_records = timesheet_invoice_obj.sudo().search(
                [
                    ("project_id", "=", project.id),
                    ("state", "in", ("approved", "completed")),
                ]
            )
            project.spent_budget = sum(
                inv.total_amount for inv in timesheet_invoice_records
            )

    def _compute_running_cost(self):
        """
        Compute Running Cost of Project.
        """
        timesheet_invoice_obj = self.env["timesheet.invoice"]
        for project in self:
            timesheet_invoice_records = timesheet_invoice_obj.search(
                [
                    ("project_id", "=", project.id),
                    ("state", "in", ("draft", "confirm", "pre-approved")),
                ]
            )
            project.running_cost = sum(
                inv.total_amount for inv in timesheet_invoice_records
            )

    @api.depends("actual_budget", "revised_budget")
    def _compute_actual_revised_budget(self):
        for project in self:
            project.actual_revised_budget = (
                project.revised_budget
                if project.revised_budget > 0
                else project.actual_budget
            )

    @api.depends("actual_budget", "spent_budget", "percentage_completed")
    def _compute_budget_completion(self):
        for project in self:
            project.budget_of_completion = (
                                                   (
                                                           (100 - project.percentage_completed)
                                                           / project.percentage_completed
                                                   )
                                                   * project.spent_budget
                                           ) + project.spent_budget \
                if project.percentage_completed > 0 and project.stage_id.is_close is False else 0.0

    def _compute_assignee_id_editable(self):
        cann_pro_crd = self.env.user.has_group(
            "project_management_security.group_project_coordinator"
        )
        for record in self:
            record.assignee_id_editable = False if (cann_pro_crd) else True

    @api.depends("stage_id", "stage_id.is_close")
    def _compute_closing_stage(self):
        for rec in self:
            rec.is_closing_stage = (
                True if (rec.stage_id and rec.stage_id.is_close is True) else False
            )

    @api.depends("date_start", "percentage_completed", "expected_end_date", "stage_id", "stage_id.is_close")
    def _compute_projected_end_date(self):
        today_date = fields.Date.today()
        for project in self:
            proj_end_dt = False
            if (
                project.percentage_completed > 0
                and project.date_start
                and project.stage_id.is_close is not True
            ):
                start_date = project.date_start
                spent_days = (today_date - start_date).days if start_date else 0
                projected_days = (
                    (
                        (100 - project.percentage_completed)
                        / project.percentage_completed
                    )
                    * spent_days
                ) + spent_days
                if projected_days < 0:
                    proj_end_dt = (
                        project.expected_end_date
                        if project.expected_end_date
                        and project.expected_end_date >= project.date_start
                        else False
                    )
                else:
                    proj_end_dt = start_date + timedelta(projected_days)
            project.projected_end_date = proj_end_dt

    is_closing_stage = fields.Boolean(
        "Closing Stage?", compute="_compute_closing_stage"
    )
    actual_budget = fields.Float(
        "Actual Budget(Euro)",
        copy=False,
        digits="Project Amount",
        help="Actual Budget of the Project in Euro.",
    )
    revised_budget = fields.Float(
        "Revised Budget(Euro)",
        copy=False,
        readonly=1,
        digits="Project Amount",
        help="Revised Budget of the Project in Euro.",
    )
    spent_budget = fields.Float(
        compute="_compute_spent_budget",
        digits="Project Amount",
        help="Spent Budget on the Project in Euro.",
    )
    percentage_completed = fields.Float(copy=False)
    running_cost = fields.Float(
        "Pending Cost(Euro)",
        compute="_compute_running_cost",
        digits="Project Amount",
        help="Pending Cost on the Project in Euro.",
    )
    actual_revised_budget = fields.Float(
        "Budget(Euro)",
        compute="_compute_actual_revised_budget",
        digits="Project Amount",
        help="Revised Budget of the Project in Euro.",
    )
    budget_of_completion = fields.Float(
        "Budget at completion", compute="_compute_budget_completion"
    )
    project_rev_ids = fields.One2many(
        "project.rev.date", "project_id", "Date Revision", copy=False, readonly=1
    )
    project_rev_budget_ids = fields.One2many(
        "project.revised.budget",
        "project_id",
        string="Budget Revisions",
        copy=False,
        readonly=1,
    )
    assignee_id_editable = fields.Boolean(
        "Assignee Editable", compute="_compute_assignee_id_editable", store=False
    )
    expected_end_date = fields.Date(
        string="Expected Finish Date",
        tracking=True,
        copy=False,
        readonly=0,
        help="Expected End date of Project",
    )
    rev_date = fields.Date(
        string="Revised Date",
        copy=False,
        readonly=1,
        help="Expected End date Revised on",
        tracking=True,
    )
    date = fields.Date(string="Actual End Date", tracking=True)
    date_start = fields.Date(copy=False, tracking=True)
    projected_end_date = fields.Date(
        compute="_compute_projected_end_date",
        string="Projected End Date",
        store=True,
        tracking=True,
    )
