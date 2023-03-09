# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    @api.depends("tasks")
    def _compute_progress(self):
        """ This method used to calculate project progress based on project
            completed percentage """
        for project in self:
            project.progress = (
                project.percentage_completed if project.percentage_completed else 0
            )

    progress = fields.Float(
        compute="_compute_progress",
        string="Overall Progress",
        help="Computed as avg. progress of related sprints",
    )

#    Needed for future scope

#     def action_project_form_view(self):
#         self.ensure_one()
#         action = self.env.ref(
#             'project_management_security.action_project_project_report').read()[0]
#         projects = self.env['project.project'].search([(
#             'name', '=', self.name)])
#         if len(projects) > 1:
#             action['domain'] = [('id', 'in', projects.ids)]
#         elif projects:
#             form_view = [(self.env.ref('project.edit_project').id, 'form')]
#             if 'views' in action:
#                 action['views'] = form_view + [
#                     (state, view)
#                     for state, view in action['views'] if view != 'form']
#             else:
#                 action['views'] = form_view
#             action['res_id'] = projects.id
#         return action
