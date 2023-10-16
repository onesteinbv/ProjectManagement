# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from datetime import timedelta, date

from odoo import api, fields, models
from odoo.osv import expression


class ProjectProjectStage(models.Model):
    _inherit = "project.project.stage"

    is_close = fields.Boolean("Closing Stage")


class ProjectProject(models.Model):
    _inherit = "project.project"

    def _get_cost_items_from_vendor_bills(self):
        """
        Get all cost items from vendor bills

        :param state state of 'account.move' to be considered
        when fetching the move lines, for example 'draft' for draft vendor bills for calculating
        running costs
        """
        amount_invoiced = amount_to_invoice = 0.0
        query = self.env['account.move.line'].sudo()._search(
            [('move_id.move_type', 'in', self.env['account.move'].get_purchase_types()),
             ('price_subtotal', '!=', 0),
             ('parent_state', 'in', ['draft', 'posted']),
             ('is_downpayment', '=', False), ('partner_id', '!=', False)])
        query.add_where('account_move_line.analytic_distribution ? %s', [str(self.analytic_account_id.id)])
        # account_move_line__move_id is the alias of the joined table account_move in the query
        # we can use it, because of the "move_id.move_type" clause in the domain of the query, which generates the join
        # this is faster than a search_read followed by a browse on the move_id to retrieve the move_type of each account.move.line
        query_string, query_param = query.select('price_subtotal', 'parent_state', 'account_move_line.currency_id',
                                                 'account_move_line.analytic_distribution',
                                                 'account_move_line__move_id.move_type')
        self._cr.execute(query_string, query_param)
        invoices_move_line_read = self._cr.dictfetchall()
        if invoices_move_line_read:
            # Get conversion rate from currencies to currency of the project
            currency_ids = {iml['currency_id'] for iml in
                            invoices_move_line_read + [{'currency_id': self.currency_id.id}]}
            rates = self.env['res.currency'].browse(list(currency_ids))._get_rates(self.company_id, date.today())
            conversion_rates = {cid: rates[self.currency_id.id] / rate_from for cid, rate_from in rates.items()}
            for moves_read in invoices_move_line_read:
                price_subtotal = self.currency_id.round(
                    moves_read['price_subtotal'] * conversion_rates[moves_read['currency_id']])
                analytic_contribution = moves_read['analytic_distribution'][str(self.analytic_account_id.id)] / 100.
                if moves_read['parent_state'] == 'draft':
                    if moves_read['move_type'] == 'in_invoice':
                        amount_to_invoice += price_subtotal * analytic_contribution
                    else:  # moves_read['move_type'] == 'out_refund'
                        amount_to_invoice -= price_subtotal * analytic_contribution
                else:  # moves_read['parent_state'] == 'posted'
                    if moves_read['move_type'] == 'in_invoice':
                        amount_invoiced += price_subtotal * analytic_contribution
                    else:  # moves_read['move_type'] == 'out_refund'
                        amount_invoiced -= price_subtotal * analytic_contribution
        return amount_invoiced, amount_to_invoice

    def _compute_spent_budget_and_running_cost(self):
        """
        Compute the Spent Budget of Project
        """
        for project in self:
            amount_invoiced, amount_to_invoice = project._get_cost_items_from_vendor_bills()
            amount_invoiced += sum(
                timesheet.amount for timesheet in project.timesheet_ids if
                (not timesheet.sheet_state or (timesheet.sheet_state and timesheet.sheet_state == 'done'))
            )
            running_cost_for_timesheets = sum(
                timesheet.amount for timesheet in project.timesheet_ids if
                timesheet.sheet_state and timesheet.sheet_state != 'done'
            )
            project.spent_budget = amount_invoiced
            project.running_cost_for_invoices = amount_to_invoice
            project.running_cost_for_timesheets = running_cost_for_timesheets
            project.running_cost = running_cost_for_timesheets + amount_to_invoice

    @api.depends("actual_budget", "revised_budget")
    def _compute_actual_revised_budget(self):
        for project in self:
            project.actual_revised_budget = (
                project.revised_budget
                if project.revised_budget > 0
                else project.actual_budget
            )

    @api.depends("actual_budget", "spent_budget", "percentage_completed", "stage_id")
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
    actual_budget = fields.Monetary(
        "Actual Budget",
        copy=False,

        help="Actual Budget of the Project",
    )
    revised_budget = fields.Monetary(
        "Revised Budget",
        copy=False,
        readonly=1,

        help="Revised Budget of the Project."
    )
    spent_budget = fields.Monetary(
        compute="_compute_spent_budget_and_running_cost",

        help="Spent Budget on the Project", currency_field="currency_id"
    )
    percentage_completed = fields.Float(copy=False)
    running_cost = fields.Monetary(
        "Pending Cost",
        compute="_compute_spent_budget_and_running_cost",
        help="Pending Cost on the Project",
    )
    running_cost_for_invoices = fields.Monetary(
        "Pending Cost for Invoices",
        compute="_compute_spent_budget_and_running_cost",
    )
    running_cost_for_timesheets = fields.Monetary(
        "Pending Cost for Timesheets",
        compute="_compute_spent_budget_and_running_cost",
    )
    actual_revised_budget = fields.Monetary(
        "Budget",
        compute="_compute_actual_revised_budget",

        help="Revised Budget of the Project",
    )
    budget_of_completion = fields.Monetary(
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
