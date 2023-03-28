# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, fields, models


class ProjectApproveWiz(models.TransientModel):
    _name = "project.approve.wiz"
    _description = "Project Approve Wizard"

    reason = fields.Text(required=1)

    def action_approve(self):
        """
        Approve the Budget Revision or Date revision based on the Context.
        """
        state = self._context.get("state", False)
        model = self._context.get("active_model", False)
        active_id = self._context.get("active_id", False)
        if state and model and active_id:
            parent_rec = self.env[model].browse([active_id])
            for wiz in self:
                parent_rec.write(
                    {
                        "approval_reason": wiz.reason,
                        "approved_by": self.env.user.id,
                        "approved_date": fields.Datetime.now(),
                        "state": state,
                    }
                )
                rev = ""
                if self._context.get("extend_field", False):
                    if self._context.get("extend_field") == "revised_budget":
                        parent_rec.project_id.write(
                            {"revised_budget": parent_rec.new_budget}
                        )
                        rev = "Budget Revisions"
                    elif self._context.get("extend_field") == "expected_end_date":
                        parent_rec.project_id.write(
                            {
                                "expected_end_date": parent_rec.new_expected_end_date,
                                "rev_date": fields.Datetime.now(),
                            }
                        )
                        rev = "Project Revisions"
                msg = (
                    _(
                        """ <ul class="o_mail_thread_message_tracking">
                    <li>%s
                    <span style="text-transform: capitalize;">%s
                    </span> by: <span> %s </span></li>
                    <li>Reason: <span> %s </span>"""
                    )
                    % (rev, state, self.env.user.name, wiz.reason)
                )
                parent_rec.project_id.message_post(body=msg)
