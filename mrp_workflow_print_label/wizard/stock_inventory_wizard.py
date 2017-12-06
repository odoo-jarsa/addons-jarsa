# -*- coding: utf-8 -*-
# 2017 Jarsa Sistemas, S.A. de C.V.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
import sys

from openerp import _, api, fields, models

reload(sys)
sys.setdefaultencoding('utf-8')


_logger = logging.getLogger(__name__)
try:
    from openpyxl import Workbook
    from openpyxl.writer.excel import save_virtual_workbook
except ImportError:
    _logger.debug('Cannot `import openpyxl`.')


class StockInventoryWizard(models.TransientModel):
    _name = 'stock.inventory.wizard'

    name = fields.Char()
    file_binary = fields.Binary(string="Download File")

    @api.model
    def default_get(self, fields):
        res = super(StockInventoryWizard, self).default_get(
            fields)
        obj_product = self.env['product.product']
        location_ids = self.env['stock.location'].search(
            [('usage', '=', 'internal')])
        stock_quants = self.env['stock.quant'].search([
            ('location_id', 'in', location_ids.ids)])
        product_ids = stock_quants.mapped('product_id')
        data = stock_quants.read_group(
            [('location_id', 'in', location_ids.ids)],
            ['product_id', 'qty', 'location_id', 'lot_id'],
            ['product_id', 'location_id', 'lot_id'], lazy=False,
            orderby="product_id")
        wb = Workbook()
        ws1 = wb.active
        ws1.append({
            'A': _('Product'),
            'B': _('Lot'),
            'C': _('Warehouse'),
            'D': _('UoM'),
            'E': _('Quantity'),
        })
        letters = {
            'A': len(_('Product')),
            'B': len(_('Lot')),
            'C': len(_('Warehouse')),
            'D': len(_('UoM')),
            'E': len(_('Quantity')),
        }
        name = ''
        for product in product_ids:
            if product.code:
                name = '[' + product.code + '] ' + product.name
            else:
                name = product.name
            ws1.append({'A': name, 'B': '', 'C': '', 'D': '', 'E': ''})
            letters['A'] = self.calculate_value(name, letters['A'])
            for line in data:
                product_line = line['product_id'][1]
                if name == product_line:
                    product_uom = obj_product.search(
                        [('id', '=', line['product_id'][0])]).uom_id.name
                    qty = str(line['qty'])
                    lot = line['lot_id'][1] if line['lot_id'] else 'N/A'
                    location = line['location_id'][1]
                    letters['B'] = self.calculate_value(lot, letters['D'])
                    letters['C'] = self.calculate_value(location, letters['E'])
                    letters['D'] = self.calculate_value(
                        product_uom, letters['B'])
                    letters['E'] = self.calculate_value(qty, letters['C'])
                    ws1.append({
                        'A': '',
                        'B': lot,
                        'C': location,
                        'D': product_uom,
                        'E': line['qty'] if line['qty'] > 0 else 0,

                    })
        for key, value in letters.items():
            ws1.column_dimensions[key].width = value
        xlsx_file = save_virtual_workbook(wb)
        res['file_binary'] = base64.encodestring(xlsx_file)
        res['name'] = 'Inventory.xlsx'
        return res

    def calculate_value(self, value, value2):
        if len(str(value)) > value2:
            return len(str(value))
        else:
            return value2
