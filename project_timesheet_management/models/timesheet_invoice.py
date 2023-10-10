# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.http import request
from werkzeug import urls


class TimesheetInvoice(models.Model):
    _name = "timesheet.invoice"
    _description = "Timesheet Invoice"
    _rec_name = "ref_no"
    _order = "submit_date DESC"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):

        res = super(TimesheetInvoice, self).read_group(
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )

        if "total_amount" in fields:
            for line in res:
                if line.get("__domain"):
                    domain = line.get("__domain") + [("state", "=", "rejected")]
                    records = self.search(domain)
                    amt_sum = 0
                    for rec in records or []:
                        amt_sum += rec.total_amount
                    line["total_amount"] = line["total_amount"] - amt_sum
        return res

    @api.depends("resource_calculation_ids.worked_hours",
                 "resource_calculation_ids")
    def _compute_total_hours(self):
        """
        Compute the total hours.
        """
        for rec in self:
            rec.total_hours = sum(
                resource.worked_hours for resource in rec.resource_calculation_ids
            )

    def _get_partner_domain(self):
        """
        Partner Domain to limit Partner to Parent Company's resources
        """
        domain = [("supplier_rank", ">", 0), ("is_company", "=", True)]
        if self.env.user.supplier_company_id:
            domain.append(("id", "=", self.env.user.supplier_company_id.id))
        return domain

    @api.depends("state")
    def _compute_show_reject_draft_btn(self):
        """
        Show or Hide Reject and Set to Draft button based
        on the current state and user's access right.
        """
        has_group = self.env.user.has_group
        is_po = has_group("project_management_security.group_project_coordinator")
        is_pm = has_group("project_management_security.group_im")
        other_groups = ["base.group_system", "project_management_security.group_cio"]
        for timesheet_inv in self:
            show_reject_draft_btn = False
            if is_po:
                show_reject_draft_btn = (
                    False
                    if timesheet_inv.state in ("confirm", "pre-approved", "approved")
                    else True
                )
            elif is_pm:
                show_reject_draft_btn = (
                    False
                    if timesheet_inv.state in ("pre-approved", "approved")
                    else True
                )
            elif (
                any([has_group(group) for group in other_groups])
                and timesheet_inv.state not in "approved"
            ):
                show_reject_draft_btn = True
            timesheet_inv.show_reject_draft_btn = show_reject_draft_btn

    def _compute_timesheet_inv_age(self):
        """
        This is compute field method to calculate age for timesheet invoice.
        """
        for timesheet_inv in self:
            if (
                timesheet_inv.state in ("completed", "approved")
                and timesheet_inv.approved_on
                or timesheet_inv.completed_date
            ):

                create_date = timesheet_inv.submit_date
                if timesheet_inv.approved_on:
                    completed_date = timesheet_inv.approved_on.date()
                else:
                    completed_date = timesheet_inv.completed_date
                diff = completed_date - create_date
                timesheet_inv.timesheet_inv_age = diff.days if diff.days > 0 else 0

            elif timesheet_inv.create_date:
                create_datetime = timesheet_inv.create_date
                current_datetime = datetime.now()
                difference = current_datetime - create_datetime
                timesheet_inv.timesheet_inv_age = (
                    difference.days if difference.days > 0 else 0
                )
            else:
                timesheet_inv.timesheet_inv_age = 0

    partner_id = fields.Many2one(
        "res.partner",
        "Supplier",
        domain=lambda self: self._get_partner_domain(),
        ondelete="restrict",
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Supplier of the Project.",
    )
    project_id = fields.Many2one(
        "project.project",
        "Project",
        required=True,
        readonly=True,
        ondelete="restrict",
        states={"draft": [("readonly", False)]},
        help="Project related to the timesheet.",
    )
    submit_date = fields.Date(
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=fields.Date.context_today,
    )
    date_due = fields.Date(
        "Due Date",
        readonly=True,
        states={
            "draft": [("readonly", False)],
            "confirm": [("readonly", False)],
            "pre-approved": [("readonly", False)],
        },
        index=True,
        copy=False,
    )
    document_type = fields.Selection(
        [("invoice", "Invoice"), ("timesheet", "Timesheet")],
        required=1,
        readonly=True,
        default="timesheet",
        copy=False,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Confirm"),
            ("pre-approved", "Pre Approved"),
            ("approved", "Approved"),
            ("completed", "Completed"),
            ("rejected", "Rejected"),
        ],
        "Status",
        default="draft",
        copy=False,
    )
    ref_no = fields.Char(
        "Reference No.",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    #     entity_id = fields.Many2one(
    #         string="Entity", readonly=True,
    #         states={'draft': [('readonly', False)]},
    #         track_visibility='onchange',
    #         comodel_name="ticket.entity",
    #         ondelete="restrict",
    #         help="Entity Related to this Timesheet Invoice.")
    total_amount = fields.Float(
        copy=False,
        help="Total amount of the Timesheet Invoice.",
        digits=("Project Amount"),
    )
    total_hours = fields.Float(
        compute="_compute_total_hours", help="Total Hours for the Timesheet Invoice."
    )
    resource_calculation_ids = fields.One2many(
        "resource.calculation",
        "timesheet_invoice_id",
        "Resource Calculation",
        states={"draft": [("readonly", False)]},
        readonly=True,
        copy=False,
    )
    approved_by = fields.Many2one(
        "res.users", ondelete="restrict", copy=False, readonly=True, help="Approved By."
    )
    approved_on = fields.Datetime(copy=False, readonly=True)
    pre_approved_on = fields.Datetime("Pre-Approved on", copy=False, readonly=True)
    pre_approved_by = fields.Many2one(
        "res.users",
        ondelete="restrict",
        copy=False,
        readonly=True,
        help="Pre-Approved By.",
    )
    description = fields.Text(
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Description of the field",
    )
    show_reject_draft_btn = fields.Boolean(
        "Show Reject/Draft Buttons",
        compute="_compute_show_reject_draft_btn",
        compute_sudo=True,
    )
    completed_date = fields.Date("Completed On")
    completed_by = fields.Many2one(
        "res.users",
        ondelete="restrict",
        copy=False,
        readonly=True,
        help="Completed By.",
    )
    timesheet_inv_age = fields.Char(
        "Aging",
        store=False,
        compute="_compute_timesheet_inv_age",
        help="Timesheet Invoice Age (in days).",
    )
    user_is_admin = fields.Boolean("Admin User?", compute="_compute_user_id_admin")

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Update the project value."""
        self.project_id = False

    def _compute_user_id_admin(self):
        for invoice in self:
            invoice.user_is_admin = self.env.user._is_admin()

    def get_timesheet_invoice_url(self):
        """
        Generate Timesheet Invoice URL
        """
        self.ensure_one()
        invoice_url = " "
        try:
            base_url = self.env["ir.config_parameter"].get_param("web.base.url")
            invoice_url = urls.url_join(
                base_url, "web#id=%s&view_type=form&model=%s" % (self.id, self._name)
            )
        except Exception:
            pass
        return invoice_url

    def button_draft(self):
        """
        Set timesheet invoice to draft.
        """
        self.with_context(from_approval=True).sudo().write({"state": "draft"})

    def button_confirm(self):
        """
        Set timesheet invoice to confirm and send mail
        Project Manager to Pre-Approve the Timesheet Invoice.
        """
        mail_template = self.env.ref(
            "project_timesheet_management.email_timesheet_invoice_confirmed"
        )
        for invoice in self:
            invoice.write({"state": "confirm"})
            if mail_template:
                email_values = {
                    "email_from": self.env.user.email,
                    "email_to": invoice.project_id.user_id.email or ''
                }
                state = dict(invoice.fields_get(
                    allfields=['state'])['state']['selection'])[invoice.state]
                mail_template.sudo().with_context(state=state).send_mail(
                    invoice.id, force_send=True, email_values=email_values
                )

    def button_pre_approve(self):
        """
        Set timesheet invoice to pre-approve and add the pre_approved_on
        and send mail to CIO to Approve the Timesheet Invoice.
        """
        self._check_budget()
        mail_template = self.env.ref(
            "project_timesheet_management.email_timesheet_invoice_confirmed"
        )
        for invoice in self:
            invoice.write(
                {
                    "pre_approved_on": datetime.now(),
                    "pre_approved_by": self.env.user.id,
                    "state": "pre-approved",
                }
            )
            if mail_template:
                email_values = {
                    "email_from": self.env.user.email,
                    "email_to": invoice.project_id.product_owner_id.email or ''
                }
                state = dict(invoice.fields_get(
                    allfields=['state'])['state']['selection'])[invoice.state]
                mail_template.sudo().with_context(state=state).send_mail(
                    invoice.id, force_send=True, email_values=email_values
                )

    def button_approve(self):
        """
        Set timesheet invoice to approved and add approved_by and approved_on.
        Updating with sudo env due to the access rights.
        """
        self._check_budget()

        mail_template = self.env.ref(
            "project_timesheet_management.email_timesheet_invoice_confirmed"
        )

        po_group = 'project_management_security.group_supp_project_coordinator'
        finance_controller = 'project_management_security.group_finance_controller'
        it_manager = 'project.group_project_manager'
        for invoice in self:
            #             self.message_subscribe_users()
            invoice.with_context(from_approval=True).sudo().write(
                {
                    "state": "approved",
                    "approved_by": self.env.user.id,
                    "approved_on": datetime.now(),
                }
            )
            state = dict(invoice.fields_get(
                    allfields=['state'])['state']['selection'])[invoice.state]
            # Mail to project manager
            if mail_template:
                email_values = {
                    "email_from": invoice.project_id.product_owner_id.email or '',
                    "email_to": invoice.project_id.user_id.email or ''
                }
                mail_template.sudo().with_context(state=state).send_mail(
                    invoice.id, force_send=True, email_values=email_values
                )

    #             # IT Manager
                it_user_ids = invoice.project_id.favorite_user_ids.filtered(
                    lambda user: user.has_group(
                        it_manager) and
                    user.id != invoice.project_id.user_id.id) or invoice.project_id.resource_ids.mapped(
                    'user_ids').filtered(
                        lambda user: user.has_group(it_manager) and
                    user.id != invoice.project_id.user_id.id)

                for user_id in it_user_ids:
                    email_values.update({
                        'email_to': user_id.email or '',
                        'email_from': self.env.user.email or '',
                    })
                    mail_template.sudo().with_context(state=state).send_mail(
                    invoice.id, force_send=True, email_values=email_values)

    #             # Finance controller
                u_lst = it_user_ids.ids
                u_lst.append(invoice.project_id.user_id.id)
                fc_user_ids = invoice.project_id.favorite_user_ids.filtered(
                    lambda user: user.has_group(finance_controller) and (
                        user.id not in u_lst)) or invoice.project_id.resource_ids.mapped(
                    'user_ids').filtered(
                        lambda user: user.has_group(finance_controller) and
                    (user.id not in u_lst))

                for user_id in fc_user_ids:
                    email_values.update({
                        'email_to': user_id.email or '',
                        'email_from': self.env.user.email or '',
                    })
                    mail_template.sudo().with_context(state=state).send_mail(
                    invoice.id, force_send=True, email_values=email_values)

    #             supplier project coordinator
                u_lst += fc_user_ids.ids
                user_ids = invoice.project_id.favorite_user_ids.filtered(
                    lambda user: user.has_group(po_group) and (
                        user.id not in u_lst) and (
                        user.partner_id == invoice.partner_id or
                        user.supplier_company_id == invoice.partner_id)) or \
                    invoice.project_id.resource_ids.mapped(
                        'user_ids').filtered(
                            lambda user: user.has_group(po_group) and (
                                user.id not in u_lst
                            ) and (
                                user.partner_id == invoice.partner_id or
                                user.supplier_company_id == invoice.partner_id))

                for user_id in user_ids:
                    email_values.update({
                        'email_to': user_id.email or '',
                        'email_from': self.env.user.email or '',
                    })
                    mail_template.sudo().with_context(state=state).send_mail(
                    invoice.id, force_send=True, email_values=email_values)

    def button_completed(self):
        """
        Set timesheet invoice to completed.
        """
        su_po_group = "project_management_security.group_supp_project_coordinator"
        mail_template = self.env.ref(
            "project_timesheet_management.email_timesheet_invoice_confirmed")
        it_manager = "project.group_project_manager"
        author_id = (
            self.env["res.users"].sudo().browse(request.session.uid).partner_id.id
        )
        email_values = {
            "email_from": self.env.user.email or self.env.user.partner_id.email,
            "author_id": author_id or False
        }
        for timesheet_inv in self:
            timesheet_inv.with_context(from_approval=True).sudo().write(
                {
                    "state": "completed",
                    "completed_date": fields.Date.context_today(timesheet_inv),
                    "completed_by": self.env.user.id,
                }
            )
            state = dict(timesheet_inv.fields_get(
                    allfields=['state'])['state']['selection'])[timesheet_inv.state]
            email_values.update({
                "email_to": timesheet_inv.project_id.product_owner_id.email or '',
            })
            mail_template.sudo().with_context(state=state).send_mail(
                    timesheet_inv.id, force_send=True,
                    email_values=email_values)

            # supplier project coordinator
            project_id = timesheet_inv.sudo().project_id
            user_ids = project_id.favorite_user_ids.filtered(
                lambda user: user.has_group(su_po_group)
                             and user.id != timesheet_inv.sudo().project_id.product_owner_id.id
                             and (
                                 user.partner_id == timesheet_inv.sudo().partner_id
                                 or user.supplier_company_id == timesheet_inv.sudo().partner_id
                             )
            ) or project_id.resource_ids.mapped("user_ids").filtered(
                lambda user: user.has_group(su_po_group)
                             and user.id != timesheet_inv.sudo().project_id.product_owner_id.id
                             and (
                                 user.partner_id == timesheet_inv.sudo().partner_id
                                 or user.supplier_company_id == timesheet_inv.sudo().partner_id
                             )
            )

            for user_id in user_ids:
                email_values.update({
                    "email_to": user_id.email or '',
                })
                mail_template.sudo().with_context(state=state).send_mail(
                        timesheet_inv.id, force_send=True,
                        email_values=email_values)

            # IT Manager
            u_lst = user_ids.ids
            u_lst.append(timesheet_inv.sudo().project_id.product_owner_id.id)
            it_user_ids = project_id.favorite_user_ids.filtered(
                lambda user: user.has_group(it_manager) and user.id not in u_lst
            ) or project_id.resource_ids.mapped("user_ids").filtered(
                lambda user: user.has_group(it_manager) and user.id not in u_lst
            )

            for user_id in it_user_ids:
                email_values.update({
                    "email_to": user_id.email or '',
                })
                mail_template.sudo().with_context(state=state).send_mail(
                        timesheet_inv.id, force_send=True,
                        email_values=email_values)

    def write(self, vals):
        """
        @override
        To calculate and add the total_amount and if it is to Approve
        the Invoice then rewrite the current user id as the author of
        last change since we're using sudo() due to the access rights.
        """
        res = super(TimesheetInvoice, self).write(vals)
        user_obj = self.env["res.users"]
        author_id = user_obj.sudo().browse(request.session.uid).partner_id.id
        for timesheet_invoice in self:
            if (
                timesheet_invoice.document_type == "timesheet"
                and "from_approval" not in self._context
            ):
                total_amount = sum(
                    (line.worked_hours * line.resource_amount)
                    for line in timesheet_invoice.resource_calculation_ids
                )
                timesheet_invoice._write({"total_amount": total_amount})
            if self._context.get("from_approval", False):
                next(iter(timesheet_invoice.message_ids)).write(
                    {
                        "author_id": author_id
                    }
                )
        return res

    @api.model_create_multi
    def create(self, vals):
        """
        @override
        To calculate the amount when creating the record.
        """
        res = super(TimesheetInvoice, self).create(vals)
        po_group = 'project_management_security.group_project_coordinator'
        mail_template = self.env.ref(
            'project_timesheet_management.email_timesheet_invoice_confirmed')
        mail_state = 'Uploaded'
        email_from = self.env.user.email or ''
        for timesheet_invoice in res:
            if timesheet_invoice.document_type == "timesheet":
                total_amount = sum(
                    (line.worked_hours * line.resource_amount)
                    for line in timesheet_invoice.resource_calculation_ids
                )
                res.write({"total_amount": total_amount})
                user_ids = timesheet_invoice.project_id.favorite_user_ids.filtered(
                    lambda user: user.has_group(po_group)) or \
                    timesheet_invoice.project_id.resource_ids.mapped(
                        'user_ids').filtered(lambda user: user.has_group(po_group))
                for user_id in user_ids:
                    email_values = {
                        'email_to': user_id.email or '',
                        'email_from': email_from,
                    }
                    mail_template.sudo().with_context(state=mail_state).send_mail(
                        timesheet_invoice.id, force_send=True, email_values=email_values)
        return res

    def button_rejected(self):
        """
        Set timesheet invoice to Reject State.
        Updating with sudo env due to the access rights.
        """
        mail_template = self.env.ref(
            "project_timesheet_management.email_timesheet_invoice_confirmed"
        )

        po_group = 'project_management_security.group_supp_project_coordinator'
        cann_po_group = 'project_management_security.group_project_coordinator'
        # )
        author_id = (
            self.env["res.users"].sudo().browse(request.session.uid).partner_id.id
        )
        email_values = {
            'email_from': self.env.user.email or self.env.user.partner_id.email,
            "author_id": author_id or False
        }
        mail_status = 'Rejected'
        for timesheet_inv in self:
            u_lst = []
            if timesheet_inv.state == "pre-approved":
                email_values.update({
                    'email_to': timesheet_inv.project_id.user_id.email or '',
                })
                mail_template.sudo().with_context(state=mail_status).send_mail(
                    timesheet_inv.id, force_send=True,
                    email_values=email_values)
                u_lst = [timesheet_inv.project_id.user_id.id]
            elif timesheet_inv.state == "confirm":
                email_values.update({
                    'email_to': timesheet_inv.pre_approved_by.email or '',
                })
                mail_template.sudo().with_context(state=mail_status).send_mail(
                    timesheet_inv.id, force_send=True,
                    email_values=email_values)
                u_lst = [timesheet_inv.pre_approved_by.id]
            timesheet_inv.with_context(from_approval=True).sudo().write(
                {"state": "rejected"}
            )

            # Project Manager
            if (
                timesheet_inv.project_id.user_id.id not in u_lst
                and timesheet_inv.project_id.product_owner_id.id == self.env.user.id
            ):
                email_values.update({
                    'email_to': timesheet_inv.project_id.user_id.email or '',
                })
                mail_template.sudo().with_context(state=mail_status).send_mail(
                    timesheet_inv.id, force_send=True,
                    email_values=email_values)

            # Supplier Project Coordinator
            user_ids = timesheet_inv.project_id.favorite_user_ids.filtered(
                lambda user: user.has_group(po_group) and
                user.id not in u_lst and (
                    user.partner_id == timesheet_inv.partner_id or
                    user.supplier_company_id == timesheet_inv.partner_id)) or \
                timesheet_inv.project_id.resource_ids.mapped(
                    'user_ids').filtered(
                        lambda user: user.has_group(po_group) and
                user.id not in u_lst and (
                    user.partner_id == timesheet_inv.partner_id or
                    user.supplier_company_id == timesheet_inv.partner_id))

            for user_id in user_ids:
                email_values.update({
                    'email_to': user_id.email or '',
                })
                mail_template.sudo().with_context(state=mail_status).send_mail(
                    timesheet_inv.id, force_send=True,
                    email_values=email_values)

            # Canna Project Coordinator
            u_lst += user_ids.ids
            c_user_ids = timesheet_inv.project_id.favorite_user_ids.filtered(
                lambda user: user.has_group(
                    cann_po_group) and user.id not in u_lst) or \
                timesheet_inv.project_id.resource_ids.mapped(
                    'user_ids').filtered(
                    lambda user: user.has_group(
                        cann_po_group) and user.id not in u_lst)
            for user_id in c_user_ids:
                email_values.update({
                    'email_to': user_id.email or '',
                })
                mail_template.sudo().with_context(state=mail_status).send_mail(
                    timesheet_inv.id, force_send=True,
                    email_values=email_values)

    def unlink(self):
        """
        @override
        Preventing record deletion if the record is approved.
        Raises:
            UserError: If the record is Approved
        """
        for record in self:
            if record.state == "approved":
                raise UserError(
                    _(
                        "You can not delete Timesheet Invoice "
                        "which is already Approved."
                    )
                )
        return super(TimesheetInvoice, self).unlink()

    @api.returns("self", lambda value: value.id)
    def message_post(self, **kwargs):
        #         self.message_subscribe_users()
        return super(TimesheetInvoice, self).message_post(**kwargs)

    # @api.constrains('project_id', 'total_amount', 'state')
    def _check_budget(self):
        """Placeholder for checking budget method, to be overriden"""
        pass

    @api.onchange("project_id", "partner_id")
    def _onchange_project_document(self):
        """
        Get all the resources of the Project
        filtering the selected Partner's suppliers only
        """
        for timesheet_rec in self:
            timesheet_rec.resource_calculation_ids = False
            timesheet_rec.total_amount = 0.0
            if timesheet_rec.project_id and timesheet_rec.project_id.resource_ids:
                # resource_calculation_lines = []
                resource_calculation_lines = [
                    [
                        0,
                        False,
                        {
                            "resource_id": each_resource.id,
                            "resource_amount": each_resource.resource_amount,
                        },
                    ]
                    for each_resource in timesheet_rec.project_id.resource_ids
                    if timesheet_rec.partner_id
                       and timesheet_rec.partner_id == each_resource.parent_id
                ]
                timesheet_rec.resource_calculation_ids = resource_calculation_lines

    @api.onchange("resource_calculation_ids")
    def onchange_resource_calculation(self):
        """
        Get the total amount based on the resource working hours and price.
        """
        for timesheet_rec in self:
            if (
                timesheet_rec.resource_calculation_ids
                and timesheet_rec.document_type == "timesheet"
            ):
                timesheet_rec.total_amount = sum(
                    res_cal_line.worked_hours * res_cal_line.resource_amount
                    for res_cal_line in timesheet_rec.resource_calculation_ids
                )

    @api.onchange("date_due")
    def _onchange_submit_date(self):
        submit_date = self.submit_date
        if not submit_date:
            submit_date = fields.Date.context_today(self)
        if self.date_due and (submit_date > self.date_due):
            raise UserError(_("Due date should be greater then Submit Date."))
