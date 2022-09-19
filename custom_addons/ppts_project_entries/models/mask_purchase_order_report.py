from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
import xlwt
import os
import base64
from io import BytesIO
from PIL import Image
from odoo import tools
import math
import pathlib


class MaskPOReportExcelWizard(models.TransientModel):
    _name = "mask.po.report"

    file_data = fields.Binary("Download Excel Report")
    file_name = fields.Char("Excel File")


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    total_mask_po_weight = fields.Float(string="Total Mask Po Weight", compute="mask_po_total_qty")
    total_mask_po_pieces = fields.Integer(string="Total Mask Po Pieces", compute="mask_po_total_qty")


    def mask_po_total_qty(self):
                
        for po in self:
            total_mask_po_weight = 0.000
            total_mask_po_pieces = 0
            
            for picking in po.picking_ids:
                containers = self.env['project.container'].search([('picking_id', '=', picking.id)])

                for container in containers:
                    fractions = self.env['project.fraction'].search([('source_container_id', '=', container.id)])
                    for fraction in fractions:
                        total_mask_po_weight+=(fraction.fraction_weight/1000)
                        total_mask_po_pieces+=fraction.number_of_pieces
                    
                rc_obj = self.env['stock.container'].search([('project_id', '=', picking.project_entry_id.id),('picking_id', '=', picking.id)])

                for rc in rc_obj:
                    total_mask_po_weight+=(rc.net_weight/1000)
                    total_mask_po_pieces+=rc.total_number_of_pieces
            
            po.total_mask_po_weight = total_mask_po_weight
            po.total_mask_po_pieces = total_mask_po_pieces
    

    def xlwt_auto_adjust_column_width(self,sheet,column_index,column_data):
        #(Modify column width to match biggest data in that column)
        cwidth = sheet.col(column_index).width
        if (len(str(column_data))*367) > cwidth:  
            sheet.col(column_index).width = (len(column_data)*367) 
            


    def action_export_mask_po(self):
        workbook = xlwt.Workbook()

        sheet = workbook.add_sheet('Mask PO Report', cell_overwrite_ok=True)
        sheet.show_grid = False


        # sheet.col(0).width = 256 * 25
        sheet.col(1).width = 256 * 25
        sheet.col(2).width = 256 * 25
        sheet.col(3).width = 256 * 30
        sheet.col(4).width = 256 * 25
        sheet.col(5).width = 256 * 25
        sheet.col(6).width = 256 * 25
        sheet.col(7).width = 256 * 25

        sheet.row(10).height = 240*2
        sheet.row(17).height = 256*2
        for row_index in range(20,50):
            sheet.row(row_index).height = 240*2
        

        style01 = xlwt.easyxf('font: name Times New Roman,height 240,colour gray80 ; alignment: wrap True; ')

        style01_height = xlwt.easyxf('font: name Times New Roman,height 300,colour black ; alignment: wrap True; ')

        style01_val_height = xlwt.easyxf('font: name Times New Roman,height 300,colour gray80 ; alignment: wrap True; ')


        style02 = xlwt.easyxf('font: name Times New Roman,colour gray80 ; border:top_color black,bottom_color black,top thin,bottom thin; alignment: wrap True;')

        style02_bold = xlwt.easyxf('font: name Times New Roman,bold on,colour gray80 ; border:top_color black,bottom_color black,top thin,bottom thin; alignment: wrap True;')

        style03 = xlwt.easyxf('font: name Times New Roman,colour gray80,bold on,italic on; ')
        style04 = xlwt.easyxf('font: name Times New Roman,colour gray80 ; border:top_color black,bottom_color black,right_color black,left_color black,left thin,right thin,top thin,bottom thin; alignment: wrap True;')

        style05 = xlwt.easyxf('font: name Times New Roman,colour gray80 ; alignment: wrap True;')
        style05_bold = xlwt.easyxf('font: name Times New Roman,height 210,bold on,colour gray80 ; alignment: wrap True;')

        style06_left_border = xlwt.easyxf('font: name Times New Roman,colour gray80 ; border:top_color black,bottom_color black,left_color black,left thin,top thin,bottom thin; alignment: wrap True;')

        style06_right_border = xlwt.easyxf('font: name Times New Roman,colour gray80 ; border:top_color black,bottom_color black,right_color black,right thin,top thin,bottom thin; alignment: wrap True;')

        style06_left_border_bold = xlwt.easyxf('font: name Times New Roman,bold on,colour gray80 ; border:top_color black,bottom_color black,left_color black,left thin,top thin,bottom thin; alignment: wrap True;')

        style06_right_border_bold = xlwt.easyxf('font: name Times New Roman,bold on,colour gray80 ; border:top_color black,bottom_color black,right_color black,right thin,top thin,bottom thin; alignment: wrap True;')

        style07_border_bottom = xlwt.easyxf('border:bottom_color black,bottom thin;')

        style08 = xlwt.easyxf('font: name Times New Roman,colour gray80 ; alignment: wrap True;')

        style09_footer = xlwt.easyxf('font: name Times New Roman,colour gray80 ;alignment: wrap True; align: horiz center;')

        style09_border_bottom = xlwt.easyxf('border:bottom_color gray80,bottom thick;')

        # image_tag = """<img style="width: 7.0cm; height: 1.8cm;" src="{}" alt="logo"/>""".format(tools.image_data_uri(self.company_id.logo))

        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        img_dir = current_file_dir.rstrip("/").replace("/models","/static/description/")

        if self.company_id.id==1:
            img = Image.open(img_dir+"1.jpeg")
        elif self.company_id.id==2:
            img = Image.open(img_dir+"2.png")
        elif self.company_id.id==4:
            img = Image.open(img_dir+"4.jpeg")
        elif self.company_id.id==5:
            img = Image.open(img_dir+"5.jpeg")
        elif self.company_id.id==6:
            img = Image.open(img_dir+"6.jpeg")
        elif self.company_id.id==8:
            img = Image.open(img_dir+"8.png")
        else:
            img = Image.open(img_dir+"1.jpeg")
               
        image_parts = img.split()
        r = image_parts[0]
        g = image_parts[1]
        b = image_parts[2]
        img = Image.merge("RGB", (r, g, b))

        newsize = (200, 100)
        img = img.resize(newsize)
        
        fo = BytesIO()
        img.save(fo, format='bmp')
        sheet.insert_bitmap_data(fo.getvalue(),1,1)
        img.close()

        row_add = 2
        sheet.write(row_add, 5, self.company_id.name, style05)
        if self.company_id.street:
            row_add+=1
            sheet.write(row_add, 5, self.company_id.street, style05)
        if self.company_id.street2:
            row_add+=1
            sheet.write(row_add, 5, self.company_id.street2, style05)
        
        if self.company_id.zip:
            zip_code = self.company_id.zip
        else:
            zip_code = ""

        if self.company_id.city:
            city = self.company_id.city
        else:
            city = ""

        if zip_code or city:
            row_add+=1
            sheet.write(row_add, 5, zip_code+" "+city, style05)
        if self.company_id.state_id:
            row_add+=1
            sheet.write(row_add, 5, self.company_id.state_id.name, style05)
        if self.company_id.country_id:
            row_add+=1
            sheet.write(row_add, 5, self.company_id.country_id.name, style05)

        sheet.write_merge(7, 7, 1, 5, "", style07_border_bottom)
        
        row_add = 9
        sheet.write(row_add, 4, self.partner_id.display_name, style05)
        if self.partner_id.street:
            row_add+=1
            sheet.write(row_add, 4, self.partner_id.street, style05)
        if self.partner_id.street2:
            row_add+=1
            sheet.write(row_add, 4, self.partner_id.street2, style05)
        
        if self.partner_id.zip:
            zip_code = self.partner_id.zip
        else:
            zip_code = ""

        if self.partner_id.city:
            city = self.partner_id.city
        else:
            city = ""

        if zip_code or city:
            row_add+=1
            sheet.write(row_add, 4, zip_code+" "+city, style05)
        if self.partner_id.state_id:
            row_add+=1
            sheet.write(row_add, 4, self.partner_id.state_id.name, style05)
        if self.partner_id.country_id:
            row_add+=1
            sheet.write(row_add, 4, self.partner_id.country_id.name, style05)
        if self.partner_id.vat:
            row_add+=1
            tax_name = "TVA:"
            # if self.company_id.country_id.vat_label:
            #     tax_name = self.company_id.country_id.vat_label
            # else:
            #     tax_name = "TVA:"
            sheet.write(row_add, 4, tax_name+" "+self.partner_id.vat, style05)

        if self.dest_address_id:
            row_add = 9
            sheet.write(row_add, 1, "Shipping Address: ", style05)
            sheet.write(row_add, 1,self.dest_address_id.display_name, style05)
        if self.dest_address_id.street:
            row_add+=1
            sheet.write(row_add, 1, self.dest_address_id.street, style05)
        if self.dest_address_id.street2:
            row_add+=1
            sheet.write(row_add, 1, self.dest_address_id.street2, style05)
        
        if self.dest_address_id.zip:
            zip_code = self.dest_address_id.zip
        else:
            zip_code = ""

        if self.dest_address_id.city:
            city = self.dest_address_id.city
        else:
            city = ""

        if zip_code or city:
            row_add+=1
            sheet.write(row_add, 1, zip_code+" "+city, style05)

        if self.dest_address_id.state_id:
            row_add+=1
            sheet.write(row_add, 1, self.dest_address_id.state_id.name, style05)
        if self.dest_address_id.country_id:
            row_add+=1
            sheet.write(row_add, 1, self.dest_address_id.country_id.name, style05)
        

        if self.state == "draft":
            column_data = "Demande pour Devis"
            sheet.write(17, 1, column_data, style01_height)
        elif self.state in ['sent', 'to approve']:
            column_data = "Offre de Rachat"
            sheet.write(17, 1, column_data, style01_height)
        elif self.state in ['purchase', 'done']:
            column_data = "Offre de Rachat"
            sheet.write(17, 1, column_data, style01_height)
        elif self.state == "cancel":
            column_data = "Numéro du bon d'achat annulé"
            sheet.write(17, 1, column_data, style01_height)
        else:
            column_data = "Offre de Rachat"
            sheet.write(17, 1, column_data, style01_height)
        

        sheet.write(17, 2, self.name, style01_val_height)

        sheet.row(18).height = 300*2

        sheet.write(18, 1, 'Responsable achat:', style05_bold)
        
        sheet.write(19, 1, self.user_id.name if self.user_id else '', style05)

        sheet.write(18, 2, 'Date de commande:', style05_bold)

        sheet.write(19, 2, str(self.date_order.strftime("%d-%m-%Y %H:%M:%S")) if self.date_order else '', style05)
       

        sheet.write(18, 3, "Votre référence de commande:", style05_bold)

        sheet.write(19, 3, self.partner_ref if self.partner_ref else '', style05)

        project_entry = self.env['project.entries'].sudo().search([('origin','=',self.id)],limit=1)
        sheet.write(18, 4, 'Affaires en cours:', style05_bold)
        sheet.write(19, 4, project_entry.name if project_entry else '', style05)

        
        row_add = 19
      
        row_add+=2

        sheet.write(row_add, 1, "DESCRIPTION", style06_left_border_bold)

        sheet.write(row_add, 2, "TAXES", style02_bold)

        sheet.write(row_add, 3, "QTÉ", style02_bold)

        sheet.write(row_add, 4, "PRIX UNITAIRE", style02_bold)

        sheet.write(row_add, 5, "MONTANT", style06_right_border_bold)

        row_add+=1

        qty_total = 0.00
        price_unit_total = 0.00
        for line in self.mask_po_line_ids.sorted(key=lambda r: r.sequence):
            # update_name_field = line.update_name_field
            uom_name = line.product_uom.name

            price_unit_total+=line.price_unit

            if line.product_id:
                sheet.write(row_add, 1, line.description, style06_left_border)
                sheet.write(row_add, 2, ', '.join(map(lambda x: x.name, line.taxes_id)), style02)
                sheet.write(row_add, 3, str(round(line.product_qty, 6))+" "+str(uom_name), style02)
                sheet.write(row_add, 4, str(round(line.price_unit, 2)), style02)
                sheet.write(row_add, 5, str(round(line.price_subtotal, 2))+" €", style06_right_border)
            else:
                sheet.write(row_add, 1, line.description, style06_left_border)
                sheet.write(row_add, 2, "", style02)
                sheet.write(row_add, 3, "", style02)
                sheet.write(row_add, 4, "", style02)
                sheet.write(row_add, 5, "", style06_right_border)

            row_add+=1

        row_add+=1
        sheet.write(row_add, 4, "Quantité totale", style06_left_border_bold)

        sheet.write(row_add, 5, str(round(self.total_mask_po_weight, 2))+" "+"tonne", style06_right_border)
    
        row_add+=1
        sheet.write(row_add, 4, "Prix unitaire total", style06_left_border_bold)

        sheet.write(row_add, 5, str(round(price_unit_total, 2))+" €", style06_right_border)
        row_add+=1

        sheet.write(row_add, 4, "Prix total", style06_left_border_bold)

        sheet.write(row_add, 5, str(round(self.mask_po_total, 2))+" €", style06_right_border)


        # notes
        row_add+=1
        sheet.write(row_add, 1, self.notes if self.notes else "", style08)

        # footer

        report_footer = self.company_id.report_footer

        footer_lines = report_footer.split("\n")

        row_add+=4
        sheet.write_merge(row_add, row_add, 1, 5, "", style09_border_bottom)
        sheet.row(row_add).height = 256*1
        row_add+=1
        sheet.row(row_add).height = 256*1
        for footer in footer_lines:
            row_add+=1
            sheet.row(row_add).height = 256*1
            sheet.write_merge(row_add, row_add, 1, 5, str(footer),style09_footer)
            # sheet.write(row_add, 1, str(footer), style02)
        
       
        filename = ('/tmp/Mask PO Report.xls')
        # filename = os.path.join(ADDONS_PATH, 'Mask PO Report.xls')

        workbook.save(filename)
        mask_po_view = open(filename, 'rb')
        file_data = mask_po_view.read()
        out = base64.encodestring(file_data)
        attach_value = {
            'file_name': 'Mask PO Report.xls',
            'file_data': out,
        }

        act_id = self.env['mask.po.report'].create(attach_value)
        mask_po_view.close()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mask.po.report',
            'res_id': act_id.id,
            'target': 'new',
        }