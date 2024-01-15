from odoo import fields, models


class ProjectScrumSprint(models.Model):
    _inherit = 'project.scrum.sprint'

    sprint_number = fields.Char(
        readonly=False,
    )
    create_date_old = fields.Datetime('Old Created on')
    create_uid_old = fields.Many2one('res.users', string='Old Created by')
    write_date_old = fields.Datetime('Old Updated on')
    write_uid_old = fields.Many2one('res.users', string='Old Updated by')


class ProjectScrumProductBacklog(models.Model):
    _inherit = 'project.scrum.product.backlog'

    old_id = fields.Integer('Old Id')
    backlog_number = fields.Char(
        readonly=False,
    )
    create_date_old = fields.Datetime('Old Created on')
    create_uid_old = fields.Many2one('res.users', string='Old Created by')
    write_date_old = fields.Datetime('Old Updated on')
    write_uid_old = fields.Many2one('res.users', string='Old Updated by')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    old_id = fields.Integer('Old Id')
    task_number = fields.Char(
        readonly=False,
    )
    create_date_old = fields.Datetime('Old Created on')
    create_uid_old = fields.Many2one('res.users', string='Old Created by')
    write_date_old = fields.Datetime('Old Updated on')
    write_uid_old = fields.Many2one('res.users', string='Old Updated by')


class ProjectProject(models.Model):
    _inherit = 'project.project'

    old_id = fields.Integer('Old Id')
    create_date_old = fields.Datetime('Old Created on')
    create_uid_old = fields.Many2one('res.users', string='Old Created by')
    write_date_old = fields.Datetime('Old Updated on')
    write_uid_old = fields.Many2one('res.users', string='Old Updated by')


class ProjectScrumRelease(models.Model):
    _inherit = 'project.scrum.release'

    old_id = fields.Integer('Old Id')
    create_date_old = fields.Datetime('Old Created on')
    create_uid_old = fields.Many2one('res.users', string='Old Created by')
    write_date_old = fields.Datetime('Old Updated on')
    write_uid_old = fields.Many2one('res.users', string='Old Updated by')
