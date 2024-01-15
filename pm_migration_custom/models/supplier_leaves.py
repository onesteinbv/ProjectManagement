from odoo import api, fields, models

class SupplierLeaves(models.Model):
    _inherit = "supplier.leaves"

    @api.constrains("date_from")
    def _check_start_date(self):
        """
        Validate if the Date is of the future only.

        Raises:
            ValidationError: If the Date is not of the Future.
        """
        current_date = fields.Date.today()
        for supp_leaves in self:
            if supp_leaves.date_from < current_date:
                pass