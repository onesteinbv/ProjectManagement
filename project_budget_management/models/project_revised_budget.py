# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectRevisedBudget(models.Model):
    _name = "project.revised.budget"
    _description = "Project Revised Budget"
    _order = "id DESC"

    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):

        res = super(ProjectRevisedBudget, self).read_group(
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )

        if "new_budget" in fields:
            for line in res:
                if line.get("__domain"):
                    if line.get("project_id"):
                        project_id = self.env["project.project"].search(
                            [("id", "=", line.get("project_id")[0])]
                        )
                        line["new_budget"] = project_id.revised_budget
                    domain = line.get("__domain") + [("state", "=", "approve")]
                    records = self.search(domain, limit=2, order="id desc")
                    if len(records) == 1:
                        line["prev_budget"] = 0.0
                    else:
                        for rec in records:
                            line["prev_budget"] = rec.new_budget
        return res

    @api.depends("project_id", "project_id.revised_budget", "project_id.actual_budget")
    def _compute_prev_budget(self):
        for budget_revision in self:
            if budget_revision.project_id:
                budget_revision.prev_budget = (
                    budget_revision.project_id.revised_budget
                    if budget_revision.project_id.revised_budget > 0
                    else budget_revision.project_id.actual_budget
                )

    project_id = fields.Many2one("project.project", "Project")
    create_uid = fields.Many2one("res.users", "Changed by", readonly=True)
    create_date = fields.Datetime("Changed On", default=fields.Datetime.now())
    new_budget = fields.Float("New Budget(Euro)", digits="Project Amount")
    prev_budget = fields.Float(
        "Previous Budget(Euro)",
        compute="_compute_prev_budget",
        store=True,
        digits="Project Amount",
    )
    comment = fields.Text(required=1)
    approved_by = fields.Many2one("res.users", "Approved by", readonly=True)
    approved_date = fields.Datetime("Approval/Reject On")
    approval_reason = fields.Text("Approval/Reject Reason")
    state = fields.Selection(
        [("draft", "Draft"), ("approve", "Approved"), ("reject", "Rejected")],
        default="draft",
    )

    def goto_project_rec(self):
        action = self.sudo().env.ref("project.open_view_project_all_config")
        for revision in self:
            action["views"] = [(self.env.ref("project.edit_project").id, "form")]
            action["res_id"] = revision.project_id.id
            result = action.read()[0]
            result["domain"] = "[('project_id','=', %s)]" % (revision.project_id.id)
            return result


class ProjectRevDate(models.Model):
    _name = "project.rev.date"
    _description = "Project Revision date"
    _order = "id DESC"

    project_id = fields.Many2one("project.project", "Project")
    create_uid = fields.Many2one("res.users", "Changed by", readonly=True)
    create_date = fields.Datetime("Changed On")
    new_expected_end_date = fields.Date("Expected Finish Date")
    comment = fields.Char(required=1)
    approval_reason = fields.Text("Approval/Reject Reason")
    approved_by = fields.Many2one("res.users", "Approved by", readonly=True)
    approved_date = fields.Datetime("Approval/Reject On")
    state = fields.Selection(
        [("draft", "Draft"), ("approve", "Approved"), ("reject", "Rejected")],
        default="draft",
    )

    @api.constrains("project_id", "new_expected_end_date")
    def _check_new_expected_end_date(self):
        """
        To check the project start date and end date.
        Raises:
            ValidationError: If the Project start date is
                             greater then the end date
        """
        for project_rev in self:
            if (
                project_rev.project_id.date_start
                and project_rev.project_id.date_start
                > project_rev.new_expected_end_date
            ):
                raise ValidationError(
                    _(
                        "Error! Project end date must be "
                        "greater than project start date."
                    )
                )
