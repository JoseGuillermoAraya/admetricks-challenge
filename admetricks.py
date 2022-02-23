# -*- coding: utf-8 -*-

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from dateutil import relativedelta

act = pd.read_excel("Tarea Data Scientist Admetricks.xlsx", "Actividad")
tarifas = pd.read_excel("Tarea Data Scientist Admetricks.xlsx", "Tarifas")


def extract_year_month(fecha):
    return str(fecha.year)+'-'+str('{:02d}'.format(fecha.month))


def plot_table(fig, ax: plt.Axes, tabla, colLabels, title):
    ax.axis('off')
    ax.axis('tight')
    ax.table(cellText=tabla.values, colLabels=colLabels, loc='center')
    ax.set_title(title)


def plot_table_and_lines(tabla, df_val, x_name, y_name, table_title, line_title, hue):
    fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={
        'width_ratios': [1, 2]}, figsize=(10, 6))
    fig.tight_layout()
    fig.patch.set_visible(False)
    fig.subplots_adjust(bottom=0.2, wspace=0.2, top=0.9)
    plot_table(fig, ax1, tabla, tabla.columns, table_title)
    sns.lineplot(x=x_name, y=y_name,
                 hue=hue, data=df_val, ax=ax2)
    ax2.set_title(line_title)
    ax2.tick_params(axis='x', labelrotation=45)


def get_end_date(row):
    if(row['Fecha inicio validez'] == primeras_fechas.loc[row['Sitio web']]['Fecha']):
        return cut_fechas[cut_fechas['Sitio web'] == row['Sitio web']].iloc[0]['Fecha inicio validez']
    else:
        return None


def get_month_diff(end, start):
    diff = relativedelta.relativedelta(end, start)
    return diff.years*12 + diff.months


"""# Ejercicio 1:

Tarifa CPM por sitio web (suma total de valorizaciones dividido en total de Impresiones * 1000):
"""

tabla_1 = act.groupby("SItio web")[['Valorización', 'Impresiones']].sum()
tabla_1['Tarifa'] = tabla_1['Valorización']/tabla_1['Impresiones']*1000
tabla_1 = tabla_1[['Tarifa']]
tabla_1_plot = tabla_1.reset_index()

"""Gráfico valorización mensual por sitio web:"""

# parse de fecha a año-mes
val_mensual = act.copy()
val_mensual['año-mes'] = val_mensual.apply(
    lambda x: extract_year_month(x['Fecha']), axis=1)
# Val por mes por sitio
val_mensual = val_mensual.groupby(
    ['SItio web', 'año-mes'])['Valorización'].sum()
val_mensual = val_mensual.reset_index()

plot_table_and_lines(tabla_1_plot, val_mensual, 'año-mes',
                     'Valorización', 'Tabla 1', 'Gráfico 1', 'SItio web')

"""# Ejercicio 2

Nueva tabla de tarifas:
"""
# Primeras fechas en aparecer para cada sitio en los datos
primeras_fechas = act.sort_values(by=['Fecha']).groupby(
    'SItio web').first()[['Fecha']]

# tabla de tarifas usando tarifas de ej1 y primeras_fechas como fechas de inicio de validez
new_tabla_1 = tabla_1.join(primeras_fechas)
new_tabla_1 = new_tabla_1.reset_index()
new_tabla_1 = new_tabla_1.rename(columns={
                                 'Fecha': 'Fecha inicio validez', 'Tarifa': 'Valor', 'SItio web': 'Sitio web'})

# juntar tarifas de new_tabla_1 con la tabla de tarifas de excel
tabla_2 = pd.concat([new_tabla_1, tarifas])
tabla_2 = tabla_2.reset_index()
tabla_2 = tabla_2.drop(['index'], axis=1)

"""Gráfica 2: nueva valorización mensual"""

# fechas de corte (fin) de las primeras tarifas (fechas de inicio de las segundas tarifas)
cut_fechas = tarifas[['Sitio web', 'Fecha inicio validez']]

# agregar columna con la fecha final de la tarifa (None para las últimas tarifas)
new_tabla_2 = tabla_2.copy()
new_tabla_2['fecha fin'] = new_tabla_2.apply(get_end_date, axis=1)

# agregar una columna con la tarifa correspondiente (según new_tabla_2) a la tabla actividad
graf = act.copy()
graf['tarifa'] = graf.apply(lambda x: new_tabla_2[(new_tabla_2['Sitio web'] == x['SItio web']) & (x['Fecha'] >= new_tabla_2['Fecha inicio validez']) & (
    (x['Fecha'] < new_tabla_2['fecha fin']) | (pd.isnull(new_tabla_2['fecha fin'])))].iloc[0]['Valor'], axis=1)

# agrega columna con la valorización calculada (Impresiones*tarifa)/1000
graf['val calculada'] = graf['Impresiones']*graf['tarifa']/1000

# agrega collumna con el año-mes extraido de la fecha
graf['año-mes'] = graf.apply(lambda x: extract_year_month(x['Fecha']), axis=1)

# Valorización calculada mensual por sitio
graf = graf.groupby(['SItio web', 'año-mes'])['val calculada'].sum()
graf = graf.reset_index()

plot_table_and_lines(tabla_2, graf, 'año-mes',
                     'val calculada', 'Tabla 2', 'Gráfico 2', 'SItio web')

"""# Ejercicio 3:"""


"""tabla 3:"""

INFLACION_ANUAL = 0.04
tabla_3 = act.copy()

# agrega columna con tarifas iniciales (de la tabla tarifas del excel)
tabla_3['tarifa'] = tabla_3.apply(
    lambda x: tarifas[tarifas['Sitio web'] == x['SItio web']]['Valor'].iloc[0], axis=1)
# columna con cuantos meses han pasado de la primera fecha que aparece en los datos
tabla_3['meses pasados'] = tabla_3.apply(lambda x: get_month_diff(
    x['Fecha'], primeras_fechas.loc[x['SItio web']]['Fecha']), axis=1)
# Columna con la tarifa ajustada para este mes, (multiplicando por inflación mensual)
tabla_3['tarifa ajustada'] = tabla_3.apply(lambda x: (
    1 + INFLACION_ANUAL/12 * x['meses pasados'])*x['tarifa'], axis=1)

# columna con la valorización calculada con la tarifa ajustada
tabla_3['val calculada'] = tabla_3['Impresiones'] * \
    tabla_3['tarifa ajustada']/1000
# extracción año-mes desde la fecha
tabla_3['año-mes'] = tabla_3.apply(
    lambda x: extract_year_month(x['Fecha']), axis=1)

# Tarifa ajustada por mes por sitio
new_tabla_3 = tabla_3.groupby(
    ['SItio web', 'año-mes'])['tarifa ajustada'].first()
new_tabla_3 = new_tabla_3.reset_index()

"""grafica 3"""

# Valorización calculada por mes por sitio
graf_3 = tabla_3.groupby(['SItio web', 'año-mes'])['val calculada'].sum()
graf_3 = graf_3.reset_index()

tabla_3_site = [new_tabla_3[new_tabla_3['SItio web'] == x]
                for x in new_tabla_3['SItio web'].unique()]

fig, axes = plt.subplots(1, len(tabla_3_site), figsize=(14, 6))
for (ax, df) in zip(axes, tabla_3_site):
    plot_table(fig, ax, df, df.columns,
               f'{df.iloc[0]["SItio web"]}')
fig.suptitle('Tarifas con inflación (Tabla 3)')
fig.subplots_adjust(bottom=0, wspace=0.2)

fig, ax = plt.subplots()
sns.lineplot(x='año-mes', y='val calculada',
             hue='SItio web', data=graf_3, ax=ax)
ax.set_title('Gráfico 3')
ax.tick_params(axis='x', labelrotation=45)

plt.show()
