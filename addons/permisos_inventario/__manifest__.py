# -*- coding: utf-8 -*-
{
    'name': "Permisos Inventario",
    'summary':
        """
        Permisos para almacen, venta y despacho
        """,
    'description': """
        Permisos para almacen, venta y despacho
    """,
    'author': "KND S.A.C.",
    'website': "http://www.knd.pe",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['stock','sale_stock','mrp','sales_team','crm','odoope_einvoice_base'],
    'data': [
        'data/menus_operaciones.xml',
        'data/permisos.xml',
        'data/kits.xml',
        'data/permisos_cmr.xml',
        'data/my_user_view.xml',
        'data/my_stock_quant.xml',
        'data/my_sale_order.xml',
        'data/my_product_suplierinfo.xml',
        'data/my_product_product.xml'
    ]
}
#actualizar custom roatsa
#instalar permisos inventario, y actualizar modulo inventario
#agregar a acciones planificadas la funcion de reporte seguimiento
#configuracion en inventario: configuracion->rutas, almacenes->gestionar 3 operaciones
#actualizar modulo de inventario
#crear grupos para permisos de menu almacen e¡y despachador
#agregar a despachador y almacenero en inventario->usuario, y quitar menu por defecto
#quitarle permiso de venta a despachador

#28 junio
#crear almacen, crear usuario y ver id, cambiar tipo picking ubicacion destino en transferencia interna,
#crear agendar accion en actualizar_seg_almacen
#poner invisible el almacen en vista de cotizacion

#09 julio
#crear dos grupos de ventas productos uno para todos y el otro solo segundo almacen
#agregar al grupo Usuario: Solo mostrar documentos propios la vista de sale.order.form.sale.stock y 
#en permisos de acceso el modelo transitorio
#crear la sede al usuario