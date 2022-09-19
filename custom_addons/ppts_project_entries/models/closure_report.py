from odoo import fields, models, api, _
from datetime import datetime
from werkzeug.urls import url_encode
from odoo.exceptions import AccessError, UserError, ValidationError
import xlwt
import os
import base64
from odoo import tools


class ProjectEntries(models.Model):
    _inherit = 'project.entries'

    def print_project_report(self):
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Project Report - ' + self.name, cell_overwrite_ok=True)
        xlwt.add_palette_colour("custom_colour0", 0x16)
        sheet.show_grid = False
        sheet.col(0).width = 256 * 5
        sheet.col(1).width = 256 * 5
        sheet.col(2).width = 256 * 10
        sheet.col(3).width = 256 * 15
        sheet.col(4).width = 256 * 25
        sheet.col(5).width = 256 * 7
        sheet.col(6).width = 256 * 25
        sheet.col(7).width = 256 * 15
        sheet.col(8).width = 256 * 15
        sheet.col(9).width = 256 * 20



        style01 = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thin;')
        style02 = xlwt.easyxf('font: name Times New Roman,color-index black, bold True; align: horiz center;pattern:pattern solid,fore-colour custom_colour0;border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thin;')
        style02_pr = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thin;', num_format_str='0.00%')


        if self.actual_profit != 0 and self.actual_sale_cost != 0:
            margin_actual = self.actual_profit/self.actual_sale_cost
        else:
            margin_actual = 0

        sheet.write_merge(3, 3, 2, 3, "Offre Prévisonnelle", style02)
        sheet.write(3, 4, 'Résultats', style02)
        sheet.write_merge(4, 4, 2, 3, 'Offre Initiale', style01)
        sheet.write(4, 4, self.initial_offer_price, style01)
        sheet.write_merge(5, 5, 2, 3, 'Coût de transport', style01)
        sheet.write(5, 4, self.forcased_transport_cost, style01)
        sheet.write_merge(6, 6, 2, 3, 'Achats Supplémentaires', style01)
        sheet.write(6, 4,self.estimated_extra_purchase_cost, style01)
        sheet.write_merge(7, 7, 2, 3, 'Ventes Supplementaires', style01)
        sheet.write(7, 4, self.estimated_extra_sales, style01)
        sheet.write_merge(8, 8, 2, 3, 'Frais du traitement', style01)
        sheet.write(8, 4, self.process_type_cost, style01)
        sheet.write_merge(9, 9, 2, 3, 'Bénéfice ', style01)
        sheet.write(9, 4,  self.forecast_profit, style01)
        sheet.write_merge(10, 10, 2, 3, 'Valeur du lot ', style01)
        sheet.write(10, 4, self.value_of_lot, style01)


        sheet.write_merge(3, 3, 6, 7, "Valeurs réelles", style02)
        sheet.write(3, 8,'Résultats', style02)
        sheet.write_merge(4, 4, 6, 7, "Offre Actuelle", style01)
        sheet.write(4, 8, self.quoted_price, style01)
        sheet.write_merge(5, 5, 6, 7, 'Coût de transport', style01)
        sheet.write(5, 8, self.confirmed_transport_cost, style01)
        sheet.write_merge(6, 6, 6, 7, 'Frais du traitement', style01)
        sheet.write(6, 8, self.labour_cost, style01)
        sheet.write_merge(7, 7, 6, 7, 'Achats Supplémentaires', style01)
        sheet.write(7, 8, self.extra_purchase_cost, style01)
        sheet.write_merge(8, 8, 6, 7, 'Prix de Revient', style01)
        sheet.write(8, 8, self.total_production_cost, style01)
        sheet.write_merge(9, 9, 6, 7, 'Prix de Revient avec Offre', style01)
        sheet.write(9, 8, self.production_cost_with_offer, style01)
        sheet.write_merge(10, 10, 6, 7, 'Ventes Supplémentaires', style01)
        sheet.write(10, 8, self.extra_sales_cost, style01)
        sheet.write_merge(11, 11, 6, 7, 'Gain en Métaux ', style01)
        sheet.write(11, 8, self.metal_profit, style01)
        sheet.write_merge(12, 12, 6, 7, 'Gain en Services', style01)
        sheet.write(12, 8, self.calculated_service_profit, style01)
        sheet.write_merge(13, 13, 6, 7, 'Révenue Eventuelle', style01)
        sheet.write(13, 8, self.potential_sales_price, style01)
        sheet.write_merge(14, 14, 6, 7, 'Bénéfice Calculée', style01)
        sheet.write(14, 8, self.calculated_profit, style01)
        sheet.write_merge(15, 15, 6, 7, 'Revenue Actuelle', style01)
        sheet.write(15, 8, self.actual_sale_cost, style01)
        sheet.write_merge(16, 16, 6, 7, 'Bénéfice Actuelle', style01)
        sheet.write(16, 8, self.actual_profit, style01)
        sheet.write_merge(17, 17, 6, 7, 'Marge Actuelle', style01)
        sheet.write(17, 8, (margin_actual), style02_pr)
        # sheet.write(17, 8, (90 / 100), style02_pr)

        sheet.write_merge(20, 20, 2, 4, "Ventes", style02)
        sheet.write_merge(21, 21, 2, 3, "Prix de vente cible", style01)
        sheet.write(21, 4, self.potential_sales_price, style01)
        sheet.write_merge(22, 22, 2, 3, 'Prix de Revient', style01)
        sheet.write(22, 4, self.production_cost_with_offer, style01)
        sheet.write_merge(23, 23, 2, 3, 'Revenue', style01)
        sheet.write(23, 4, self.actual_sale_cost, style01)
        sheet.write_merge(24, 24, 2, 3, 'Marge en €', style01)
        sheet.write(24, 4, self.actual_profit, style01)
        sheet.write_merge(25, 25, 2, 3, 'Marge en %', style01)
        sheet.write(25, 4, (margin_actual), style02_pr)
        # sheet.write(25, 4, (9999 / 9999), style02_pr)


        filename = ('/tmp/Project Report.xls')
        workbook.save(filename)
        fixed_purchase_report_view = open(filename, 'rb')
        file_data = fixed_purchase_report_view.read()
        out = base64.encodestring(file_data)
        attach_value = {'name': 'Project Report - ' + self.name + '.xls', 'refining_report_xl': out}

        act_id = self.env['refining.report'].create(attach_value)
        fixed_purchase_report_view.close()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'refining.report',
            'res_id': act_id.id,
            'target': 'new',
        }
