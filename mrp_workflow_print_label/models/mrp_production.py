# -*- coding: utf-8 -*-
# © 2016 Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    state = fields.Selection([
        ('draft', 'New'),
        ('cancel', 'Cancelled'),
        ('confirmed', 'Awaiting Raw Materials'),
        ('ready', 'Ready to Produce'),
        ('in_production', 'Production Started'),
        ('print_label', 'Print Label'),
        ('done', 'Done')])
    print_lot = fields.Char(string="Printing Lot", readonly=True)
    container_qty = fields.Integer(string='Quantity per Lot', readonly=True)
    report_type = fields.Selection([
        ('cloth', 'Label for Cloth'),
        ('cover', 'Label for Cover')])

    @api.multi
    def action_state_print_label(self):
        for rec in self:
            rec.state = 'print_label'
            rec.message_post(body='Printing test')
