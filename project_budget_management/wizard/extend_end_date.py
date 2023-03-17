# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, fields, models


class ExtendEndDate(models.TransientModel):
    _name = "extend.end.date.wiz"
    _description = "Extend End Date"

    date = fields.Date("Expected Finish Date", required=1)
    comment = fields.Char(required=1)

    def action_extend_date(self):
        """
        Create a new project revision record.
        """
        model = self._context.get("active_model", False)
        active_id = self._context.get("active_id", False)
        parent_rec = self.env[model].browse([active_id])
        rev_date_obj = self.env["project.rev.date"]
        for wiz in self:
            rev_date_obj.create(
                {
                    "new_expected_end_date": wiz.date,
                    "comment": wiz.comment,
                    "project_id": active_id,
                }
            )
            msg = (
                _(
                    """ <ul class="o_mail_thread_message_tracking">
                <li>Project Revisions submitted by: <span> %s </span></li><li>
                Expected Finish Date: <span> %s </span></li>
                <li>Revised Comment: <span> %s </span>"""
                )
                % (self.env.user.name, str(wiz.date), wiz.comment)
            )
            parent_rec.message_post(body=msg)
