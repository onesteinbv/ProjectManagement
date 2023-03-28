# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class ReviseBudgetWiz(models.TransientModel):
    _name = "revise.budget.wiz"
    _description = "Revise Budget Wizard"

    amount = fields.Float("Revised Amount", required=1)
    comment = fields.Text(required=1)

    def action_revise_budget(self):
        """
        Create a new record for Budget Revision
        """
        revised_budget_obj = self.env["project.revised.budget"]
        for wiz in self:
            project_id = self._context.get("active_id", False)
            project = self.env["project.project"].browse([project_id])
            if wiz.amount < project.spent_budget:
                raise ValidationError(
                    _(
                        "New budget can not be lower then "
                        "the Spent Budget of Project."
                    )
                )
            revised_budget_obj.create(
                {
                    "new_budget": wiz.amount,
                    "comment": wiz.comment,
                    "project_id": project_id,
                }
            )
            msg = (
                _(
                    """ <ul class="o_mail_thread_message_tracking">
                <li>Budget Revisions submitted by: <span> %s </span></li><li>
                Revised Amount: <span> %s </span></li>
                <li>Revised Comment: <span> %s </span>"""
                )
                % (self.env.user.name, str(wiz.amount), wiz.comment)
            )
            project.message_post(body=msg)
