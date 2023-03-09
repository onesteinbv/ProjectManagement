# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from datetime import datetime, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProjectScrumSprint(models.Model):
    _inherit = "project.scrum.sprint"

    @api.depends(
        "product_backlog_ids",
        "product_backlog_ids.expected_hours",
        "product_backlog_ids.effective_hours",
        "state",
        "estimate_adjustment",
    )
    def _compute_hours(self):
        """ This method used to calculate sprint weightage based on
            backlog effective hours, backlog expected hours,
            estimate adjustment and sprint state """
        stage_id = self.env["project.task.type"].search(
            [("name", "ilike", "Cancel")], limit=1
        )
        effective = 0
        expected_hours = 0
        progress = 0
        for sprint in self:
            for backlog in sprint.product_backlog_ids:
                if backlog.stage_id.id != stage_id.id:
                    effective += backlog.effective_hours
                    expected_hours += backlog.expected_hours

            sprint.expected_hours = expected_hours

            total_hours = sum(
                line.expected_hours for line in sprint.release_id.sprint_ids
            )
            total_hours = total_hours if total_hours > 0 else 1

            weightage = sprint.expected_hours / total_hours
            sprint.weightage = weightage
            sprint.effective_hours = effective
            sprint.progress = progress

            if sprint.expected_hours > 0:
                sprint.progress = sum(
                    (backlog.progress * backlog.expected_hours / sprint.expected_hours)
                    for backlog in sprint.with_prefetch().product_backlog_ids
                    if backlog.stage_id.id != stage_id.id
                )

    name = fields.Char("Sprint Name", size=64)
    goal = fields.Char("Goal", size=128)
    sprint_number = fields.Char(
        "Sprint number",
        readonly=True,
        copy=False,
        size=150,
        help="Sprint number sequence",
    )
    estimate_adjustment = fields.Float()
    weightage = fields.Float(compute="_compute_hours")

    @api.model
    def create(self, vals):
        """ This method used to add sprint details log in related
            release used in sprint """
        result = super(ProjectScrumSprint, self).create(vals)
        if vals.get("release_id", ""):
            msg = (
                _(
                    """ <ul class="o_mail_thread_message_tracking">
                <li>Sprint Added by: <span> %s </span></li><li>
                Sprint Number: <span> %s </span></li>
                Sprint Name: <span> %s </span></li>"""
                )
                % (self.env.user.name, result.sprint_number, result.name)
            )
            result.release_id.message_post(body=msg)
        return result

    def write(self, vals):
        """ This method used to update sprint detail logs in related
            release used in sprint """
        for rec in self:
            if vals.get("release_id", ""):
                release_id = self.env["project.scrum.release"].browse(
                    vals.get("release_id")
                )
                msg = (
                    _(
                        """ <ul class="o_mail_thread_message_tracking">
                    <li>Sprint Added by: <span> %s </span></li><li>
                    Sprint Number: <span> %s </span></li>
                    Sprint Name: <span> %s </span></li>"""
                    )
                    % (self.env.user.name, rec.sprint_number, rec.name)
                )
                release_id.message_post(body=msg)
                msg = (
                    _(
                        """ <ul class="o_mail_thread_message_tracking">
                    <li>Sprint Removed by: <span> %s </span></li><li>
                    Sprint Number: <span> %s </span></li>
                    Sprint Name: <span> %s </span></li>"""
                    )
                    % (self.env.user.name, rec.sprint_number, rec.name)
                )
                rec.release_id.message_post(body=msg)
        return super(ProjectScrumSprint, self).write(vals)

    def unlink(self):
        """ This method used to manage logs in sprint when remove
            release from sprint """
        for rec in self:
            msg = (
                _(
                    """ <ul class="o_mail_thread_message_tracking">
                <li>Sprint Removed by: <span> %s </span></li><li>
                Sprint Number: <span> %s </span></li>
                Sprint Name: <span> %s </span></li>"""
                )
                % (self.env.user.name, rec.sprint_number, rec.name)
            )
            rec.release_id.message_post(body=msg)
        return super(ProjectScrumSprint, self).unlink()


class ScrumMeeting(models.Model):
    _inherit = "project.scrum.meeting"

    @api.onchange("start_datetime", "allday", "stop")
    def onchange_dates(self):
        """Returns duration and/or end date based on values passed
        @param self: The object pointer
        """
        if not self.stop and not self.duration:
            duration = 1.00
            self.duration = duration
        if self.allday:  # For all day event
            duration = 24.0
            self.duration = duration
            # change start_date's time to 00:00:00 in the user's timezone
            user = self.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            start = pytz.utc.localize(self.start).astimezone(tz)
            # convert start in user's timezone
            start = start.replace(hour=0, minute=0, second=0)
            # change start's time to 00:00:00
            start = start.astimezone(pytz.utc)
            # convert start back to utc
            start_date = start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            self.start_date = start_date
        if self.stop and not self.duration:
            self.duration = self._get_duration(self.start_date, self.stop)
        elif not self.stop:
            end = start + timedelta(hours=self.duration)
            self.stop = end.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        elif self.stop and self.duration and not self.allday:
            duration = self._get_duration(self.start_date, self.stop)
            self.duration = duration

    @api.onchange("duration")
    def onchange_duration(self):
        """ This method used to update duration based on
            start and stop detail change """
        if self.duration:
            start = fields.Datetime.from_string(
                datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            )
            if self.start_date:
                start = fields.Datetime.from_string(self.start_date)
            self.start_date = start
            self.stop = fields.Datetime.to_string(
                start + timedelta(hours=self.duration)
            )

    def _get_duration(self, start, stop):
        """ Get the duration value between the 2 given dates.
        @param self: The object pointer
        @start self: Start Date
        @stop self: Stop Date
        """
        if start and stop:
            diff = fields.Datetime.from_string(stop) - fields.Datetime.from_string(
                start
            )
            if diff:
                duration = float(diff.days) * 24 + (float(diff.seconds) / 3600)
                return round(duration, 2)
            return 0.0


class ProjectScrumProductBacklog(models.Model):
    _inherit = "project.scrum.product.backlog"

    @api.depends(
        "tasks_id",
        "tasks_id.estimate_adjustment",
        "tasks_id.effective_hours",
        "tasks_id.planned_hours",
        "tasks_id.progress",
        "tasks_id.weightage",
    )
    def _compute_hours(self):
        """ This method is used to calculate weightage  based in related task
            estimate hours, effective hours, planned hours, progress,
            weightage etc """
        stage_id = self.env["project.task.type"].search(
            [("name", "ilike", "Cancel")], limit=1
        )
        for backlog in self:
            effective = task_hours = progress = 0.0
            for task in backlog.tasks_id.filtered(
                lambda t: t.stage_id.id != stage_id.id
            ):
                task_hours += task.planned_hours + task.estimate_adjustment
                effective += task.effective_hours

                # if backlog.expected_hours > 0 and task.planned_hours > 0:
                # old Formula
                # progress += (task.progress * (
                #     task.planned_hours + task.estimate_adjustment) / backlog.expected_hours)

            # if len(backlog.tasks_id.ids) > 0:
            #     progress = round(progress / len(backlog.tasks_id.ids))

            backlog.effective_hours = effective
            backlog.task_hours = task_hours

            # New Formula for progress in version 2
            # Not add below code in above for loop because calculation not work
            # proper if we add in above task loop
            for task in backlog.tasks_id.filtered(
                lambda t: t.stage_id.id != stage_id.id
            ):
                # progress += (task.weightage * task.progress)
                hours = task.planned_hours + task.estimate_adjustment
                if task.product_backlog_id.task_hours > 0:
                    progress += (
                        hours / task.product_backlog_id.task_hours
                    ) * task.progress

            backlog.progress = progress
            backlog.weightage = (
                backlog.expected_hours / backlog.sprint_id.expected_hours
                if backlog.sprint_id and backlog.sprint_id.expected_hours > 0
                else 0
            )

    def _compute_author_id_editable(self):
        """" This method is used to define author is editable or not
            based on group and state """
        for record in self:
            grp_pm = self.env.user.has_group("project_management_security.group_im")
            grp_custom_prj_crd = self.env.user.has_group(
                "project_management_security.group_project_coordinator"
            )
            record.author_id_editable = False
            if (
                grp_pm
                or grp_custom_prj_crd
                or record.project_id.user_id.id == self.env.user.id
                or record.state == "draft"
            ):
                record.author_id_editable = True

    name = fields.Char(
        "Title",
        required=True,
        translate=True,
        size=128,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    for_then = fields.Text(
        "For",
        translate=True,
        readonly=True,
        size=128,
        states={"draft": [("readonly", False)]},
    )
    backlog_number = fields.Char(
        "Number Requirement",
        readonly=True,
        copy=False,
        size=150,
        help="Sequence number of request",
    )
    weightage = fields.Float(compute="_compute_hours")
    author_id_editable = fields.Boolean(
        "Author Editable", compute="_compute_author_id_editable", store=False
    )

    def write(self, vals):
        """ This method is used to update logs of backlog details in release
            based on release detail update which used in backlog """
        result = super(ProjectScrumProductBacklog, self).write(vals)
        if vals.get("release_id", ""):
            for rec in self:
                release_id = self.env["project.scrum.release"].browse(
                    vals.get("release_id")
                )
                msg = (
                    _(
                        """ <ul class="o_mail_thread_message_tracking">
                    <li>Backlog Added by: <span> %s </span></li><li>
                    Backlog Number: <span> %s </span></li>
                    Backlog Name: <span> %s </span></li>"""
                    )
                    % (self.env.user.name, rec.backlog_number, rec.name)
                )
                release_id.message_post(body=msg)
                msg = (
                    _(
                        """ <ul class="o_mail_thread_message_tracking">
                    <li>Backlog Removed by: <span> %s </span></li><li>
                    Backlog Number: <span> %s </span></li>
                    Backlog Name: <span> %s </span></li>"""
                    )
                    % (self.env.user.name, rec.backlog_number, rec.name)
                )
                rec.release_id.message_post(body=msg)
        return result

    @api.model_create_multi
    def create(self, vals_lst):
        """ This method is used to manage logs of backlog details in release
            based on release used """
        result = super(ProjectScrumProductBacklog, self).create(vals_lst)
        if result.project_id.user_id:
            result.message_unsubscribe(partner_ids=[result.project_id.user_id.id])
        for vals in vals_lst:
            if vals.get("release_id", ""):
                msg = (
                    _(
                        """ <ul class="o_mail_thread_message_tracking">
                    <li>Backlog Added by: <span> %s </span></li><li>
                    Backlog Number: <span> %s </span></li>
                    Backlog Name: <span> %s </span></li>"""
                    )
                    % (self.env.user.name, result.backlog_number, result.name)
                )
                result.release_id.message_post(body=msg)
        return result

    def unlink(self):
        """ This method is used to remove logs from release detail when
            release removed form the backlog """
        for rec in self:
            msg = (
                _(
                    """ <ul class="o_mail_thread_message_tracking">
                <li>Backlog Removed by: <span> %s </span></li><li>
                Backlog Number: <span> %s </span></li>
                Backlog Name: <span> %s </span></li>"""
                )
                % (self.env.user.name, rec.backlog_number, rec.name)
            )
            rec.release_id.message_post(body=msg)
        return super(ProjectScrumProductBacklog, self).unlink()


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.depends(
        "stage_id",
        "timesheet_ids.unit_amount",
        "estimate_adjustment",
        "planned_hours",
        "child_ids.timesheet_ids.unit_amount",
        "child_ids.planned_hours",
        "child_ids.effective_hours",
        "child_ids.subtask_effective_hours",
        "child_ids.stage_id",
        "product_backlog_id.task_hours",
    )
    def _hours_get(self):
        """ This method is used to calculate weightage based on task stage,
            timesheet amount, estimate adjustment, planned hours,
            child task planned hours, backlog task hours,
            child task effective hours etc """
        for task in self:
            weightage = children_hours = 0
            for child_task in task.child_ids:
                if child_task.stage_id and child_task.stage_id.fold:
                    children_hours += (
                        child_task.effective_hours + child_task.subtask_effective_hours
                    )
                else:
                    children_hours += max(
                        child_task.planned_hours,
                        child_task.effective_hours + child_task.subtask_effective_hours,
                    )

            task.subtask_effective_hours = children_hours
            task.effective_hours = sum(task.sudo().timesheet_ids.mapped("unit_amount"))
            task.remaining_hours = (
                task.planned_hours - task.effective_hours - task.subtask_effective_hours
            )
            # Commented this line as total hours replaced as total hours spent in v15
            # here both line added total hours and total hours spent
            #             task.total_hours = max(task.planned_hours, task.effective_hours)
            task.total_hours_spent = task.effective_hours + task.subtask_effective_hours
            #             task.delay_hours = max(-task.remaining_hours, 0.0)

            story_estimated_hours = task.product_backlog_id.expected_hours
            planned_hours = task.planned_hours
            task.effective_hours
            estimate_adjustment = task.estimate_adjustment

            if story_estimated_hours > 0.0:
                weightage = planned_hours / story_estimated_hours
            hours = planned_hours + estimate_adjustment
            # hours = hours if hours > 0 else 1
            task.weightage = weightage

            # progress = sum(
            #     timesheet.unit_amount / (
            #         task.planned_hours + task.estimate_adjustment)
            #     for timesheet in task.timesheet_ids
            #     if timesheet.unit_amount > 0)

            # task.progress = progress

            if task.product_backlog_id.task_hours > 0:

                # New weightage calculation in Version 2
                task.weightage = hours / task.product_backlog_id.task_hours

            # New progress calculation in Version 2
            if task.effective_hours and hours > 0:
                task.progress = (task.effective_hours / hours) * 100

    name = fields.Char("Homework", size=256, translate=True)
    email = fields.Char(
        "Send mail",
        size=256,
        help="An email will be sent upon completion and upon validation of the"
        "Task to the following recipients. Separate with comma (,)"
        "each recipient ex: example@email.com, test@email.com",
    )
    task_number = fields.Char(
        "Task Number",
        readonly=True,
        copy=False,
        size=64,
        help="Sequence of the task number",
    )
    estimate_adjustment = fields.Float()
    weightage = fields.Float(compute="_hours_get")

    @api.model
    def create(self, vals):
        result = super(ProjectTask, self).create(vals)
        if result.manager_id:
            result.message_unsubscribe(partner_ids=[result.manager_id.id])
        return result


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.onchange("project_id")
    def onchange_project(self):
        """ This method is used to update account based on project detail update """
        for line in self:
            line.account_id = (
                line.project_id.analytic_account_id.id if line.project_id else False
            )
