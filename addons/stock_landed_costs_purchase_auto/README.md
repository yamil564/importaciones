# Isoft3 - Instancia demo
> **Isoft3** es un ERP basado en Odoo v10.
# nuevos cambios para compras importacion: 15 junio 2022
>compras->configuracion-> Métodos de costo: Use un método de coste 'fijo' 'real' o 'medio'
>Inventario-> configuracion->Contabilidad de stock->Incluir costes en destino en el cálculo del coste del producto, Valoración de inventario perpetuo
>Gastos: Flete(10), Seguro de carga(5), Comisión(10), Cargos de Manejo, Impuestos aduanales
Agregarlos como productos y marcar en facturación costes en destino, método de división: por Costo Actual
>Configuracion -> edicion masiva -> crear modelo product.category -> Método de coste y Valoración del inventario
>Inventario->menu configuracion-> categorias de productos->metodo de coste : precio real ,  valoracion del inventario: perpetuo, agregar todas las cuentass
>instalar bi_purchase_invoice_details , stock_landed_costs_purchase_auto
>actualizar permisos_inventario, personalizacion_compras
>