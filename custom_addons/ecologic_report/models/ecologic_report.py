from odoo import fields, models, api, _
from odoo.exceptions import UserError
import xlwt
import os
import base64
import io

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ProjectEntree(models.Model):
    _inherit = 'project.entries'

    def print_ecologic_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Ecologic Report')
        worksheet.hide_gridlines(2)

        worksheet.set_column(1, 1, 15)

        style_headline = workbook.add_format({'font_size': 12, 'border': 2, 'align': 'center', 'valign': 'vcenter', 'bold': True})
        style_title = workbook.add_format({'align': 'left', 'bold': True, })
        style_normal = workbook.add_format({'align': 'left', 'font_size': 10})
        style_normal2 = workbook.add_format({'align': 'right', 'font_size': 10})
        style_normal3 = workbook.add_format({'align': 'left', 'font_size': 11, 'border': 1, 'bg_color': '#5aa172'})
        style_normal4 = workbook.add_format({'align': 'right', 'font_size': 11, 'border': 1, 'bg_color': '#5aa172'})

        style_normal5 = workbook.add_format({'align': 'left', 'font_size': 10, 'left': 1,})
        style_normal6 = workbook.add_format({'align': 'right', 'font_size': 10, 'right': 1,'left':1})

        style_normal7 = workbook.add_format({'align': 'left', 'font_size': 10, 'border': 1})
        style_normal8 = workbook.add_format({'align': 'right', 'font_size': 10, 'border': 1})


        image_width = 140.0
        image_height = 250.0

        cell_width = 200
        cell_height = 300.0

        x_scale = cell_width / image_width
        y_scale = cell_height / image_height

        buf_image = io.BytesIO(base64.b64decode(self.company_id.logo_web))
        worksheet.insert_image('B5', "logo.png", {'image_data': buf_image})

        pro_row = 9
        pro_col = 1

        worksheet.write(pro_row, pro_col, str(self.company_id.name), style_title)
        worksheet.write(pro_row + 1, pro_col, str(self.company_id.street), style_normal)
        worksheet.write(pro_row + 2, pro_col, str(self.company_id.city), style_normal)
        worksheet.write(pro_row + 3, pro_col, str(self.company_id.state_id.name + ' - ' + self.company_id.country_id.name), style_normal)

        worksheet.write(pro_row + 5, pro_col, "Téléphone", style_normal)
        worksheet.write(pro_row + 5, pro_col + 1, str(self.company_id.phone), style_normal)

        worksheet.write(pro_row + 6, pro_col, "Fax", style_normal)
        worksheet.write(pro_row + 6, pro_col + 1, "+33 (0)2 72 22 04 23", style_normal)

        worksheet.merge_range(18, 4, 19, 6, 'BORDEREAU DE RECEPTION', style_headline)

        worksheet.write(pro_row + 12, pro_col, "Provenance", style_normal)
        worksheet.write(pro_row + 12, pro_col + 1, "ECOLOGIC", style_normal)

        worksheet.write(pro_row + 13, pro_col, "Bon de transfert", style_normal)
        worksheet.write(pro_row + 13, pro_col + 1, "", style_normal2)
        worksheet.write(pro_row + 14, pro_col, "Ordre", style_normal)
        worksheet.write(pro_row + 14, pro_col + 1, self.order, style_normal2)
        worksheet.write(pro_row + 15, pro_col, "Ordre de Traitement	", style_normal)
        worksheet.write(pro_row + 15, pro_col + 1, self.ordre_de_traitement, style_normal2)
        worksheet.write(pro_row + 16, pro_col, "Commande", style_normal)
        worksheet.write(pro_row + 16, pro_col + 1, self.command, style_normal2)

        worksheet.merge_range(18, 4, 19, 6, 'BORDEREAU DE RECEPTION', style_headline)

        worksheet.set_row(27, 20)
        worksheet.set_column(27, 6, 12)

        worksheet.merge_range(27, 4, 27, 5, "Désignation", style_normal3)
        worksheet.write(27, 6, "Poids net(to)", style_normal4)

        product_list = []
        ec_list = []
        fraction_obj = self.env['project.fraction'].search([('project_id', '=', self.id)])
        rc_obj = self.env['stock.container'].search([('project_id', '=', self.id)])
        for fraction in fraction_obj:
            if fraction.sub_product_id.product_ecologic_code not in product_list:
                product_list.append(fraction.sub_product_id.product_ecologic_code)
        for rc in rc_obj:
            if rc.content_type_id.product_ecologic_code not in product_list:
                product_list.append(rc.content_type_id.product_ecologic_code)
        # for line in self.origin.mask_po_line_ids:
        #     if line.product_id.product_ecologic_code not in product_list:
        #         product_list.append(line.product_id.product_ecologic_code)

        for pr in product_list:
            # pro_line = self.env["mask.po.line"].search([('product_id.product_ecologic_code','=',pr),('mask_po_line_id','=',self.origin.id)])
            fractions = self.env['project.fraction'].search([('sub_product_id.product_ecologic_code', '=', pr),('project_id', '=', self.id)])
            recepients = self.env['stock.container'].search([('content_type_id.product_ecologic_code', '=', pr),('project_id', '=', self.id)])
            wgt = 0.0
            for fraction in fractions:
                if fraction.sub_product_id.uom_id.name == 'Tonne':
                    wgt += fraction.fraction_weight / 1000
                else:
                    wgt += fraction.fraction_weight
            for recepient in recepients:
                if recepient.content_type_id.uom_id.name == 'Tonne':
                    wgt += recepient.net_weight / 1000
                else:
                    wgt += recepient.net_weight
            # for prl in pro_line:
            #     if prl.product_uom.name == 'Tonne':
            #         wgt += prl.product_qty / 1000
            #     else:
            #         wgt += prl.product_qty

            # ec_code = self.env["product.product"].browse(pr).product_ecologic_code

            ec_list.append({
                'ec_code': pr,
                'qty': wgt,
            })

        n = 28
        qty = 0.0
        for line in ec_list:
            worksheet.merge_range(n, 4, n, 5, line.get('ec_code'), style_normal5)
            worksheet.write(n, 6, line.get('qty'), style_normal6)
            n += 1
            qty +=  line.get('qty')

        worksheet.merge_range(n, 4, n, 5, "Total général", style_normal7)
        worksheet.write(n, 6, qty, style_normal8)

        pro_row += 1
        workbook.close()
        output.seek(0)
        data = output.read()
        output.close()
        data = base64.encodestring(data)
        doc_id = self.env['ir.attachment'].create({'datas': data, 'name': 'Ecologic Report [' + self.name + ']' + '.xls'})
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?id=%s&download=true' % (doc_id.id),
            'target': 'current',
        }
