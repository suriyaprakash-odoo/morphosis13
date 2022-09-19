from odoo import fields, models, api, _
import xlwt
import os
import base64
from odoo import tools
ADDONS_PATH=tools.config['addons_path'].split(",")[-1]

class ContainerDetailsReport(models.TransientModel):
	_name = 'container.details.report'

	project_id = fields.Many2one('project.entries', string="Project")

	def container_details_report(self):
		list=[]
		workbook = xlwt.Workbook()
		sheet = workbook.add_sheet('Fraction Sorting Report', cell_overwrite_ok=True)
		sheet.show_grid = False
		sheet.col(1).width = 256 * 25
		sheet.col(2).width = 256 * 25
		sheet.col(3).width = 256 * 25
		sheet.col(4).width = 256 * 25
		sheet.col(5).width = 256 * 25

		style01 = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color gray40,bottom_color gray40,right_color gray40,left_color gray40,left thin,right thin,top thin,bottom thin;')
		style02 = xlwt.easyxf('font: name Times New Roman,color-index black ; border:top_color gray40,bottom_color gray40,right_color gray40,left_color gray40,left thin,right thin,top thin,bottom thin;')
		total_weight = 0.00
		weight_uom_id = ''
		for line in self.project_id.project_entry_ids:
			if line.product_uom.name == 'Tonne':
				total_weight += (line.product_qty * 1000)
			else:
				total_weight += line.product_qty
			weight_uom_id = line.product_uom.name

		gross_weight = str(total_weight) + ' ' +str(weight_uom_id)

		sheet.write(0, 0,'Project Name', style01)
		sheet.write(0, 1,self.project_id.name, style01)
		sheet.write(1, 0,'Client', style01)
		sheet.write(1, 1,self.project_id.partner_id.name, style01)
		sheet.write(2, 0,'Gross Weight', style01)
		sheet.write(2, 1,gross_weight, style01)
		
		n=4
		n+=0

		sheet.write(n, 0,'Container', style01)
		sheet.write(n, 1,'Length', style01)
		sheet.write(n, 2,'width', style01)
		sheet.write(n, 3,'Height', style01)
		sheet.write(n, 4,'Extra Height', style01)
		sheet.write(n, 5,'Number of containers', style01)

		n+=2
		project_entry_line_obj = self.env['project.entries.line'].search([('project_entry_id' , '=' , self.project_id.id)])
		print(project_entry_line_obj)
		container_line_list = []
		for project_line in  project_entry_line_obj:
			container_line_obj = self.env['container.type.line'].search([('project_line_id' , '=' , project_line.id)])
			print(container_line_obj)
			if container_line_obj:
				for container in container_line_obj:
					sheet.write(n - 1, 0, container.container_type_id.name or '', style02)
					sheet.write(n - 1, 1, container.container_length or '', style02)
					sheet.write(n - 1, 2, container.container_width or '', style02)
					sheet.write(n - 1, 3, container.container_height or '', style02)
					sheet.write(n - 1, 4, container.final_container_height or '', style02)
					sheet.write(n - 1, 5, container.container_count or '', style02)
					n += 1

		filename = ('/tmp/Container Details Report.xls')
		# filename = os.path.join(ADDONS_PATH, 'Container Details Report.xls')

		workbook.save(filename)
		container_details_view=open(filename,'rb')
		file_data=container_details_view.read()
		out=base64.encodestring(file_data)
		attach_value={'container_details_char':'Container Details Report.xls','container_details_xml':out}

		act_id=self.env['container.report'].create(attach_value)
		container_details_view.close()
		return{
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'form',
            'res_model':'container.report',
            'res_id':act_id.id,
            'target':'new',
            }
        
        
class ExcelWizard(models.TransientModel):
    _name="container.report"    
    
    container_details_xml=fields.Binary("Download Excel Report")
    container_details_char=fields.Char("Excel File")