# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models


class ResourceCalculationWiz(models.TransientModel):
    _name = "resource.calculation.wiz"
    _description = "Resource Calculation"

    timesheet_invoice_id = fields.Many2one(
        "timesheet.invoice.wiz",
        "Timesheet Invoice",
        help="Timesheet Invoice related to "
             "this resource calculation.",
    )
    resource_id = fields.Many2one(
        "res.partner",
        "Resource",
        ondelete="restrict",
        help="Resource Related to this Calculation.",
    )
    worked_hours = fields.Float()
    resource_amount = fields.Float(
        copy=False, help="Amount to be charged for the resource."
    )


class TimesheetInvoiceWiz(models.TransientModel):
    """Timesheet invoice wizard for edit the details."""

    _name = "timesheet.invoice.wiz"
    _description = "Timesheet Invoice Wizard"

    def _get_partner_domain(self):
        """Partner Domain to limit Partner to Parent Company's resources."""
        domain = [("supplier_rank", ">", 0), ("is_company", "=", True)]
        if self.env.user.supplier_company_id:
            domain.append(("id", "=", self.env.user.supplier_company_id.id))
        return domain

    partner_id = fields.Many2one(
        "res.partner",
        "Supplier",
        domain=lambda self: self._get_partner_domain(),
        ondelete="restrict",
        help="Supplier of the Project.",
    )
    project_id = fields.Many2one(
        "project.project",
        "Project",
        ondelete="restrict",
        help="Project related to the timesheet.",
    )
    submit_date = fields.Date()
    date_due = fields.Date("Due Date", index=True, copy=False)
    document_type = fields.Selection(
        [("invoice", "Invoice"), ("timesheet", "Timesheet")]
    )
    ref_no = fields.Char("Reference No.")
    wiz_resource_calculation_ids = fields.One2many(
        "resource.calculation.wiz", "timesheet_invoice_id", "Resource Calculation"
    )
    description = fields.Text(help="Description of the field")

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Update the project value."""
        self.project_id = False

    def action_save(self):
        """Save the timesheet invoice details."""
        model = self._context.get("active_model", False)
        active_id = self._context.get("active_id", False)
        r_c_obj = self.env["resource.calculation"]
        if model and active_id:
            parent_rec = self.env[model].browse([active_id])
            for wiz in self:
                parent_rec.write(
                    {
                        "partner_id": wiz.partner_id.id or parent_rec.partner_id.id,
                        "project_id": wiz.project_id.id or parent_rec.project_id.id,
                        "submit_date": wiz.submit_date or parent_rec.submit_date,
                        "date_due": wiz.date_due or parent_rec.date_due,
                        "document_type": wiz.document_type or parent_rec.document_type,
                        "ref_no": wiz.ref_no or parent_rec.ref_no,
                        #                     'entity_id': wiz.entity_id.id or parent_rec.entity_id.id,
                        "description": wiz.description or parent_rec.description,
                    }
                )
                r_c_list = []
                for res in wiz.wiz_resource_calculation_ids:
                    vals = {
                        "resource_id": res.resource_id.id,
                        "worked_hours": res.worked_hours,
                        "resource_amount": res.resource_amount,
                        "timesheet_invoice_id": parent_rec.id,
                        "partner_id": parent_rec.partner_id.id,
                        "project_id": parent_rec.project_id.id,
                    }

                    r_c_obj.create(vals)
                    r_c_list.append(
                        [res.resource_id.name, res.worked_hours, res.resource_amount]
                    )

                message = (
                    """<div class="o_thread_message_content"><p>Hello ,
                    <br>The Timesheet Invoice with the following details has been updated <strong>"""
                    + self.env.user.name
                    + """</strong> :"""
                )
                if wiz.ref_no:
                    message += """<br><b>Reference No.</b> : """ + wiz.ref_no
                if wiz.partner_id:
                    message += """<br><b>Supplier</b> : """ + wiz.partner_id.name
                if wiz.project_id:
                    message += """<br><b>Project</b> : """ + wiz.project_id.name
                if wiz.submit_date:
                    message += """<br><b>Submit date</b> : %s""" % wiz.submit_date
                if wiz.date_due:
                    message += """<br><b>Due date</b> : %s""" % wiz.date_due
                if wiz.document_type:
                    message += """<br><b>Document Type</b> : """ + wiz.document_type
                if wiz.description:
                    message += """<br><b>Note</b> : """ + wiz.description
                if r_c_list:
                    message += """<br><b>Resource Calculation:</b> : """ + str(r_c_list)
                msg = _(message)
                parent_rec.message_post(body=msg)
